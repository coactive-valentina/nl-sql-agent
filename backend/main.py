# FastAPI backend for the NL-SQL Agent.
# Exposes two endpoints: POST /query and GET /logs.

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import run

LOGS_PATH = Path(__file__).parent.parent / "logs" / "interactions.json"

app = FastAPI(
    title="NL-SQL Agent",
    description="Natural language to SQL agent for Coactive visual analytics.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models ---

class QueryRequest(BaseModel):
    question: str
    dataset_id: str


class QueryResponse(BaseModel):
    question: str
    sql: str | None
    results: list[dict]
    error: str | None


# --- Endpoints ---

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """
    Accepts a natural language question and dataset ID,
    runs the full NL → SQL → Coactive pipeline,
    and returns the results.
    """
    result = run(request.question, request.dataset_id)
    return QueryResponse(**result)


@app.get("/logs")
def get_logs():
    """
    Returns the full interaction log history.
    """
    try:
        entries = json.loads(LOGS_PATH.read_text())
        return {"logs": entries, "total": len(entries)}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"logs": [], "total": 0}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
