"""
FastAPI routes for the Ghost Founder RAG system.
"""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.definitions import AGENT_CONFIGS, get_agent
from rag.ingest import ingest_documents, ingest_text
from rag.retriever import Retriever

router = APIRouter()

# Shared retriever instance — all agents use the same vector store
_retriever = Retriever()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str
    context: dict | None = None


class IngestDirectoryRequest(BaseModel):
    directory: str
    domain: str
    chunk_size: int | None = None
    chunk_overlap: int | None = None


class IngestTextRequest(BaseModel):
    text: str
    domain: str
    source_name: str = "direct_input"


class SearchRequest(BaseModel):
    query: str
    domain: str | None = None
    top_k: int | None = None
    source_names: list[str] | None = None
    topic_tags: list[str] | None = None
    max_age_hours: int | None = None


# ---------------------------------------------------------------------------
# Agent endpoints
# ---------------------------------------------------------------------------

@router.get("/agents")
async def list_agents():
    """List all available agents and their roles."""
    return {
        name: {"name": cfg.name, "role": cfg.role, "domain": cfg.domain}
        for name, cfg in AGENT_CONFIGS.items()
    }


@router.post("/agents/{agent_name}/query")
async def query_agent(agent_name: str, req: QueryRequest):
    """
    Query a specific agent. It retrieves domain-relevant context via RAG
    and responds in character.
    """
    try:
        agent = get_agent(agent_name, retriever=_retriever)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    response = await agent.query(question=req.question, context=req.context)
    return asdict(response)


@router.post("/agents/{agent_name}/query-direct")
async def query_agent_direct(agent_name: str, req: QueryRequest):
    """Query an agent without RAG retrieval (for debates, reactions, etc.)."""
    try:
        agent = get_agent(agent_name, retriever=_retriever)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    response = await agent.query_without_rag(question=req.question, context=req.context)
    return asdict(response)


# ---------------------------------------------------------------------------
# RAG management endpoints
# ---------------------------------------------------------------------------

@router.post("/rag/ingest/directory")
async def ingest_from_directory(req: IngestDirectoryRequest):
    """Ingest all documents from a local directory into the vector store."""
    try:
        result = ingest_documents(
            directory=req.directory,
            domain=req.domain,
            chunk_size=req.chunk_size,
            chunk_overlap=req.chunk_overlap,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@router.post("/rag/ingest/text")
async def ingest_raw_text(req: IngestTextRequest):
    """Ingest raw text directly into the vector store."""
    result = ingest_text(text=req.text, domain=req.domain, source_name=req.source_name)
    return result


@router.post("/rag/search")
async def search_knowledge_base(req: SearchRequest):
    """Search the knowledge base directly (useful for debugging)."""
    results = _retriever.search(
        query=req.query,
        domain=req.domain,
        top_k=req.top_k,
        source_names=req.source_names,
        topic_tags=req.topic_tags,
        max_age_hours=req.max_age_hours,
    )
    return {
        "query": req.query,
        "domain": req.domain,
        "source_names": req.source_names,
        "topic_tags": req.topic_tags,
        "max_age_hours": req.max_age_hours,
        "results": results,
    }
