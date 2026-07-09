"""FastAPI application entrypoint.

Configures CORS middleware, structlog logging, and application lifecycle events.
"""

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.api.chat import router as chat_router
from app.config import settings


def configure_logging() -> None:
    """Configure structlog for structured logging across the application."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
            if not sys.stderr.isatty()
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan event handler."""
    configure_logging()
    logger = structlog.get_logger()
    logger.info(
        "startup",
        message="Document Copilot backend starting up",
        origins=settings.cors_origins,
    )
    yield
    logger.info("shutdown", message="Document Copilot backend shutting down")


app = FastAPI(
    title="Document Copilot API",
    description="Backend service for Driftwood Capital Document Copilot",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS middleware using settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, tags=["chat"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
