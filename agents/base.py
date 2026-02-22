"""
Base agent template.
Every Ghost Founder agent is an instance of BaseAgent with a different AgentConfig.
Adding a new agent = adding a new config dict. No subclassing needed.
"""

from dataclasses import dataclass, field

import anthropic

from config import get_settings
from rag.retriever import Retriever


@dataclass
class AgentConfig:
    name: str
    role: str
    domain: str  # metadata filter for RAG retrieval
    system_prompt: str
    model: str = ""
    top_k: int = 0

    def __post_init__(self):
        s = get_settings()
        if not self.model:
            self.model = s.default_model
        if not self.top_k:
            self.top_k = s.retrieval_top_k


@dataclass
class AgentResponse:
    agent: str
    role: str
    content: str
    citations: list[dict] = field(default_factory=list)
    sources_used: int = 0


class BaseAgent:
    """
    Template agent: retrieves domain-specific context via RAG,
    then calls Claude with retrieved documents for grounded generation.
    """

    def __init__(self, config: AgentConfig, retriever: Retriever | None = None):
        self.config = config
        self.retriever = retriever or Retriever()
        self.client = anthropic.AsyncAnthropic(api_key=get_settings().anthropic_api_key)

    async def query(
        self,
        question: str,
        context: dict | None = None,
    ) -> AgentResponse:
        """
        Ask this agent a question. It will:
        1. Retrieve relevant docs from its domain
        2. Pass them to Claude as document blocks (with citations)
        3. Return a structured response
        """
        # 1 — Retrieve
        chunks = self.retriever.search(
            query=question,
            domain=self.config.domain,
            top_k=self.config.top_k,
        )

        # 2 — Build message content with document blocks
        content_blocks = []

        for i, chunk in enumerate(chunks):
            content_blocks.append(
                {
                    "type": "document",
                    "source": {
                        "type": "text",
                        "media_type": "text/plain",
                        "data": chunk["text"],
                    },
                    "title": f"{chunk['source_file']} (chunk {chunk['chunk_index']})",
                    "citations": {"enabled": True},
                }
            )

        # Build the user message: conversation history + state + question
        user_text = question
        if context:
            conversation = context.pop("conversation", None)
            state_lines = "\n".join(f"- {k}: {v}" for k, v in context.items())
            parts = []
            if conversation and conversation != "(No prior conversation.)":
                parts.append(f"Full conversation so far:\n{conversation}")
            parts.append(f"Current simulation state:\n{state_lines}")
            parts.append(f"Task: {question}")
            user_text = "\n\n".join(parts)

        content_blocks.append({"type": "text", "text": user_text})

        # 3 — Call Claude
        response = await self.client.messages.create(
            model=self.config.model,
            max_tokens=2048,
            system=self.config.system_prompt,
            messages=[{"role": "user", "content": content_blocks}],
        )

        # 4 — Parse response
        text_parts = []
        citations = []
        retrieval_citations = []

        for chunk in chunks:
            retrieval_citations.append(
                {
                    "source_file": chunk.get("source_file"),
                    "source_url": chunk.get("source_url"),
                    "title": chunk.get("title"),
                    "topic": chunk.get("topic"),
                    "fetched_at": chunk.get("fetched_at"),
                    "chunk_index": chunk.get("chunk_index"),
                    "score": chunk.get("score"),
                }
            )

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                # Extract citations if present
                if hasattr(block, "citations") and block.citations:
                    for cite in block.citations:
                        citations.append(
                            {
                                "cited_text": getattr(cite, "cited_text", ""),
                                "source": getattr(cite, "document_title", ""),
                            }
                        )

        return AgentResponse(
            agent=self.config.name,
            role=self.config.role,
            content="\n".join(text_parts),
            citations=citations + retrieval_citations,
            sources_used=len(chunks),
        )

    async def query_without_rag(
        self,
        question: str,
        context: dict | None = None,
        max_tokens: int = 2048,
    ) -> AgentResponse:
        """Query the agent without RAG retrieval (for debate rounds, reactions, etc.)."""
        user_text = question
        if context:
            conversation = context.pop("conversation", None)
            state_lines = "\n".join(f"- {k}: {v}" for k, v in context.items())
            parts = []
            if conversation and conversation != "(No prior conversation.)":
                parts.append(f"Full conversation so far:\n{conversation}")
            parts.append(f"Current simulation state:\n{state_lines}")
            parts.append(f"Task: {question}")
            user_text = "\n\n".join(parts)

        response = await self.client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens,
            system=self.config.system_prompt,
            messages=[{"role": "user", "content": user_text}],
        )

        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)

        return AgentResponse(
            agent=self.config.name,
            role=self.config.role,
            content="\n".join(text_parts),
        )
