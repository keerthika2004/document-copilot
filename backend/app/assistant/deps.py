"""Runtime dependency container for PydanticAI document assistant agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.retrieval.service import HybridRetriever


@dataclass
class DocumentAgentDeps:
    """Dependencies injected into tool executions during agent runs."""

    db: AsyncSession
    retriever: HybridRetriever
    user_id: str | None = None
    thread_id: str | None = None
