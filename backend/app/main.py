"""PlacementPilot API gateway (FastAPI): router factory + rate limiter."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .core.embeddings import get_embedder
from .core.llm import get_llm
from .core.rate_limit import make_rate_limit_dependency
from .routers import interview, plan, progress, resume

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    app = FastAPI(
        title="PlacementPilot API",
        version="1.0.0",
        description="Resume-aware ATS analysis, mock HR interviews, coding practice and personalised roadmaps "
                    "using LangGraph, FAISS/RAG, HuggingFace embeddings and Groq.",
    )
    app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

    rate_limit = make_rate_limit_dependency()
    for module in (resume, interview, plan, progress):  # router factory
        app.include_router(module.create_router(rate_limit))

    @app.get("/health", tags=["meta"])
    def health():
        emb = get_embedder()
        return {"status": "ok", "llm_mode": get_llm().mode, "embedding_backend": emb.name}

    return app


app = create_app()
