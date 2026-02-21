"""
Ghost Founder — RAG Agentic System
Entry point for the FastAPI application.
"""

from fastapi import FastAPI

from api.routes import router
from integrations.stripe.router import stripe_router

app = FastAPI(
    title="Ghost Founder",
    description="Autonomous AI startup simulation — RAG-powered agents",
    version="0.1.0",
)

app.include_router(router, prefix="/api")
app.include_router(stripe_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
