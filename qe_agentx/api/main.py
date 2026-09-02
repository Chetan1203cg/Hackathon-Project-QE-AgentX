"""
api/main.py
============
FastAPI application entrypoint for QE AgentX.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import artifacts, execution, pipeline, webhook
from config.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("QE AgentX API starting — env: %s", settings.app_env)
    yield
    logger.info("QE AgentX API shutting down")


app = FastAPI(
    title="QE AgentX API",
    description="Agentic Test Design Assistant — REST API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit UI origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline.router, prefix="/pipeline", tags=["Pipeline"])
app.include_router(artifacts.router, prefix="/artifacts", tags=["Artifacts"])
app.include_router(execution.router, prefix="/execution", tags=["Test Execution"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhooks"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "qe-agentx"}
