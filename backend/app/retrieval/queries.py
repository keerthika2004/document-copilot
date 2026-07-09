"""Database retrieval queries for vector similarity, lexical full-text search, and context expansion."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.database.models.document_chunk import DocumentChunk
from app.database.models.source_document import SourceDocument

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class VectorRetriever:
    """Retrieves document chunks using pgvector cosine distance."""

    @staticmethod
    async def retrieve(
        db: AsyncSession,
        query_embedding: list[float],
        limit: int = 50,
        ticker: str | None = None,
        fiscal_year: int | None = None,
        filing_type: str | None = None,
    ) -> list[UUID]:
        """Return top matching chunk IDs ordered by ascending cosine distance."""
        if not query_embedding:
            return []

        stmt = (
            select(DocumentChunk.id)
            .join(DocumentChunk.document)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        if ticker:
            stmt = stmt.where(SourceDocument.ticker == ticker.upper())
        if fiscal_year:
            stmt = stmt.where(SourceDocument.fiscal_year == fiscal_year)
        if filing_type:
            stmt = stmt.where(SourceDocument.filing_type == filing_type.upper())

        result = await db.execute(stmt)
        return list(result.scalars().all())


class LexicalRetriever:
    """Retrieves document chunks using PostgreSQL full-text search."""

    @staticmethod
    async def retrieve(
        db: AsyncSession,
        query_text: str,
        limit: int = 50,
        ticker: str | None = None,
        fiscal_year: int | None = None,
        filing_type: str | None = None,
    ) -> list[UUID]:
        """Return top matching chunk IDs ordered by descending full-text search rank."""
        if not query_text or not query_text.strip():
            return []

        ts_query = func.websearch_to_tsquery("english", query_text)
        stmt = (
            select(DocumentChunk.id)
            .join(DocumentChunk.document)
            .where(DocumentChunk.search_vector.op("@@")(ts_query))
            .order_by(func.ts_rank_cd(DocumentChunk.search_vector, ts_query).desc())
            .limit(limit)
        )
        if ticker:
            stmt = stmt.where(SourceDocument.ticker == ticker.upper())
        if fiscal_year:
            stmt = stmt.where(SourceDocument.fiscal_year == fiscal_year)
        if filing_type:
            stmt = stmt.where(SourceDocument.filing_type == filing_type.upper())

        result = await db.execute(stmt)
        return list(result.scalars().all())


class SurroundingChunkRetriever:
    """Retrieves surrounding chunks (before and after) for context expansion."""

    @staticmethod
    async def retrieve(
        db: AsyncSession,
        document_id: UUID,
        chunk_index: int,
        window: int = 1,
    ) -> list[DocumentChunk]:
        """Return chunks in the index range [chunk_index - window, chunk_index + window]."""
        stmt = (
            select(DocumentChunk)
            .options(joinedload(DocumentChunk.document))
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.chunk_index >= max(0, chunk_index - window),
                DocumentChunk.chunk_index <= chunk_index + window,
            )
            .order_by(DocumentChunk.chunk_index.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class ChunkByIdRetriever:
    """Retrieves full DocumentChunk ORM objects by their UUIDs."""

    @staticmethod
    async def retrieve(
        db: AsyncSession,
        chunk_ids: list[UUID],
    ) -> list[DocumentChunk]:
        """Fetch chunks by IDs and return them ordered by the input ID sequence."""
        if not chunk_ids:
            return []

        stmt = (
            select(DocumentChunk)
            .options(joinedload(DocumentChunk.document))
            .where(DocumentChunk.id.in_(chunk_ids))
        )
        result = await db.execute(stmt)
        chunks_map = {chunk.id: chunk for chunk in result.scalars().all()}
        return [chunks_map[cid] for cid in chunk_ids if cid in chunks_map]
