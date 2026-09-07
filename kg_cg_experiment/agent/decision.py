"""
Decision mode: the agent picks a structured ACTION, not free text.

Everything before this file tested whether KG/CG produce a good *answer*.
That's necessary but not sufficient for an agentic claim -- an agent's
memory only matters if it changes what the agent *does*. This module makes
that testable: both conditions are constrained to emit exactly one action
from a fixed set, parsed structurally, so "did the evidence change the
decision" is a hard equality check, not a judgment call about phrasing.

Same isolation discipline as the rest of the system: same system prompt
template, same LLM, same call shape for both conditions -- only the graph
context (and CG's evidence) differs. On fallback, CG's decision prompt is
byte-identical to KG's.
"""
import re
from dataclasses import dataclass, field

from kg_cg_experiment.agent.llm_client import chat, embed
from kg_cg_experiment.config import CG_RECENT_TURNS_WINDOW, GRAPH_TRAVERSAL_HOPS
from kg_cg_experiment.graph.context_graph import build_context_graph
from kg_cg_experiment.graph.knowledge_graph import build_static_kg
from kg_cg_experiment.graph.seed_matching import traverse
from kg_cg_experiment.graph.serialize import graph_to_context_text, graph_to_json

ACTIONS = ["approve_refund", "apply_waiver", "deny_request", "escalate_to_human", "request_more_info"]

DECISION_SYSTEM_PROMPT = (
    "You are a customer support agent deciding how to handle a customer's "
    "return/exchange request. Based ONLY on the policy graph facts below, "
    "choose EXACTLY ONE action:\n"
    "- approve_refund: grant the return/refund/exchange under standard policy "
    "(a fee may still apply if the policy says one does -- this action does "
    "NOT waive anything)\n"
    "- apply_waiver: grant the request AND waive the fee that would otherwise apply\n"
    "- deny_request: the request cannot be granted under policy\n"
    "- escalate_to_human: you do not have enough confidence or the policy graph "
    "does not cover this situation\n"
    "- request_more_info: you need one more specific fact from the customer "
    "before you can decide\n\n"
    "Respond in EXACTLY this format and nothing else:\n"
    "ACTION: <one of the five actions above>\n"
    "REASONING: <one sentence>\n\n"
    "{graph_context}"
)

_ACTION_RE = re.compile(r"ACTION:\s*([a-z_]+)", re.IGNORECASE)
_REASONING_RE = re.compile(r"REASONING:\s*(.+)", re.IGNORECASE | re.DOTALL)


@dataclass
class DecisionResult:
    condition: str
    action: str | None  # None if the response didn't parse to a known action -- never guessed
    reasoning: str
    raw_response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    graph_json: dict
    fell_back: bool = False
    fallback_reason: str | None = None
    messages_sent: list = field(default_factory=list)


def _parse_decision(text: str) -> tuple[str | None, str]:
    action_match = _ACTION_RE.search(text)
    reasoning_match = _REASONING_RE.search(text)
    action = action_match.group(1).lower() if action_match else None
    if action not in ACTIONS:
        action = None  # unparseable or invented an action outside the fixed set -- report as None, don't coerce
    reasoning = reasoning_match.group(1).strip() if reasoning_match else text.strip()
    return action, reasoning


def run_kg_decision(query: str) -> DecisionResult:
    kg = build_static_kg()
    sub = traverse(query, kg, hops=GRAPH_TRAVERSAL_HOPS)
    context_text = graph_to_context_text(sub)
    messages = [
        {"role": "system", "content": DECISION_SYSTEM_PROMPT.format(graph_context=context_text)},
        {"role": "user", "content": query},
    ]
    result = chat(messages)
    action, reasoning = _parse_decision(result["text"])
    return DecisionResult(
        condition="kg", action=action, reasoning=reasoning, raw_response=result["text"],
        prompt_tokens=result["prompt_tokens"], completion_tokens=result["completion_tokens"],
        total_tokens=result["total_tokens"], graph_json=graph_to_json(sub), messages_sent=messages,
    )


def run_cg_decision(query: str, user_id: str, session_id: str, turns: list[dict]) -> DecisionResult:
    kg = build_static_kg()
    query_embedding = embed(query)
    cg_result = build_context_graph(query, user_id, session_id, kg, query_embedding)

    context_text = graph_to_context_text(cg_result.subgraph)
    if cg_result.fell_back:
        messages = [
            {"role": "system", "content": DECISION_SYSTEM_PROMPT.format(graph_context=context_text)},
            {"role": "user", "content": query},
        ]
    else:
        recent = turns[-CG_RECENT_TURNS_WINDOW:]
        messages = [
            {"role": "system", "content": DECISION_SYSTEM_PROMPT.format(graph_context=context_text)},
            *recent,
            {"role": "user", "content": query},
        ]

    result = chat(messages)
    action, reasoning = _parse_decision(result["text"])
    return DecisionResult(
        condition="cg", action=action, reasoning=reasoning, raw_response=result["text"],
        prompt_tokens=result["prompt_tokens"], completion_tokens=result["completion_tokens"],
        total_tokens=result["total_tokens"],
        graph_json=graph_to_json(cg_result.subgraph, cg_result.rejected_candidates, kg),
        fell_back=cg_result.fell_back, fallback_reason=cg_result.fallback_reason, messages_sent=messages,
    )
