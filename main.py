"""
Ghost Founder — RAG Agentic System
Entry point for the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.simulation_routes import sim_router
from api.ws_routes import ws_router
from integrations.elevenlabs.router import elevenlabs_router
from integrations.stripe.router import stripe_router

app = FastAPI(
    title="Ghost Founder",
    description="Autonomous AI startup simulation — RAG-powered agents",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(sim_router, prefix="/api")
app.include_router(stripe_router, prefix="/api")
app.include_router(elevenlabs_router, prefix="/api")
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
