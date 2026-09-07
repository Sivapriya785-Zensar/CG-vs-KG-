"""
Thin client over the local Ollama REST API.

Token counts come straight from Ollama's response (`prompt_eval_count`,
`eval_count`) -- these are the actual counts the model reports for that
specific call, never estimated with a tokenizer and never guessed.
"""
import requests

from kg_cg_experiment.config import (
    EMBED_MODEL,
    OLLAMA_MODEL,
    OLLAMA_OPTIONS,
    OLLAMA_TIMEOUT_S,
    OLLAMA_URL,
)


class OllamaUnavailableError(RuntimeError):
    """Raised when Ollama cannot be reached or errors -- callers must surface
    this plainly (e.g. a 'not connected' UI state), never fabricate a result."""


def is_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/version", timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def chat(messages: list[dict]) -> dict:
    """messages: [{"role": "system"|"user"|"assistant", "content": str}, ...]

    Returns {"text": str, "prompt_tokens": int, "completion_tokens": int,
    "total_tokens": int} -- all real, from the Ollama response."""
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": OLLAMA_OPTIONS,
            },
            timeout=OLLAMA_TIMEOUT_S,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise OllamaUnavailableError(f"Could not reach Ollama at {OLLAMA_URL}: {e}") from e

    data = resp.json()
    if "message" not in data:
        raise OllamaUnavailableError(f"Unexpected Ollama response shape: {data}")

    prompt_tokens = data.get("prompt_eval_count")
    completion_tokens = data.get("eval_count")
    if prompt_tokens is None or completion_tokens is None:
        raise OllamaUnavailableError(f"Ollama response missing token counts: {data}")

    return {
        "text": data["message"]["content"],
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


def embed(text: str) -> list[float]:
    """Real embedding vector from the local nomic-embed-text model -- used
    for genuine similarity-based trace matching, never a hardcoded keyword
    list. Raises OllamaUnavailableError on failure, same contract as chat()."""
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=OLLAMA_TIMEOUT_S,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise OllamaUnavailableError(f"Could not reach Ollama embeddings at {OLLAMA_URL}: {e}") from e

    data = resp.json()
    if "embedding" not in data:
        raise OllamaUnavailableError(f"Unexpected Ollama embeddings response shape: {data}")
    return data["embedding"]
