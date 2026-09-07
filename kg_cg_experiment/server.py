"""
FastAPI backend for the KG vs CG test UI. Every /api/query and
/api/statement call hits the real local Ollama model (or, for statements,
just the real local embedding model -- no chat call) live -- nothing here is
precomputed. If Ollama isn't reachable, endpoints return a clear
"not connected" error instead of a plausible-looking fake result.
"""
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from kg_cg_experiment.agent.llm_client import OllamaUnavailableError, is_available
from kg_cg_experiment.agent.runner import run_cg, run_kg, run_statement
from kg_cg_experiment.config import OLLAMA_MODEL, OLLAMA_URL
from kg_cg_experiment.data import trace_store
from kg_cg_experiment.session import store

app = FastAPI(title="KG vs CG experiment")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class QueryRequest(BaseModel):
    user_id: str
    session_id: str
    query: str
    use_cache: bool = False


class StatementRequest(BaseModel):
    user_id: str
    session_id: str
    text: str


class ResetRequest(BaseModel):
    session_id: str


def _condition_to_dict(res) -> dict:
    return asdict(res)


@app.get("/api/health")
def health():
    available = is_available()
    return {
        "ollama_available": available,
        "ollama_url": OLLAMA_URL,
        "model": OLLAMA_MODEL,
    }


@app.post("/api/reset")
def reset(req: ResetRequest):
    """Clears this session's turn history/display only. Decision traces are
    persistent by design and are never touched here."""
    store.reset(req.session_id)
    return {"ok": True}


@app.post("/api/statement")
def statement(req: StatementRequest):
    if not is_available():
        raise HTTPException(
            status_code=503,
            detail=f"Ollama not reachable at {OLLAMA_URL} (needed for embeddings). Nothing was stored.",
        )
    try:
        result = run_statement(req.text, req.user_id, req.session_id)
    except OllamaUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    store.append_turn(req.session_id, "user", f"[statement] {req.text}")
    return result


@app.post("/api/query")
def query(req: QueryRequest):
    if not is_available():
        raise HTTPException(
            status_code=503,
            detail=f"Ollama not reachable at {OLLAMA_URL}. Nothing was run; no result to show.",
        )

    turns = store.get_turns(req.session_id)

    try:
        kg_res = run_kg(req.query)
        cg_res = run_cg(req.query, req.user_id, req.session_id, turns, use_cache=req.use_cache)
    except OllamaUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    store.append_turn(req.session_id, "user", req.query)
    store.append_turn(req.session_id, "assistant", cg_res.answer)

    return {
        "kg": _condition_to_dict(kg_res),
        "cg": _condition_to_dict(cg_res),
        "session_turns": store.get_turns(req.session_id),
    }


@app.get("/api/traces")
def list_traces(session_id: str | None = None, limit: int = 50):
    rows = trace_store.traces_by_session(session_id) if session_id else trace_store.all_traces()
    return [
        {
            "id": r.id, "user_id": r.user_id, "entity_key": r.entity_key, "attribute": r.attribute,
            "value": r.value, "raw_statement": r.raw_statement,
            "session_id": r.session_id, "kg_node_id": r.kg_node_id,
            "created_at": r.created_at,
        }
        for r in rows[:limit]
    ]


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))
