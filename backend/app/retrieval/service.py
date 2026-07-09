"""Hybrid retrieval service orchestrator combining dense vector and lexical full-text search."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.queries import (
    ChunkByIdRetriever,
    LexicalRetriever,
    SurroundingChunkRetriever,
    VectorRetriever,
)
from ingest.embeddings import EmbeddingService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class HybridRetriever:
    """Orchestrates hybrid search (vector + lexical) and context expansion over SEC filings."""

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self.embedding_service = embedding_service or EmbeddingService()

    async def search(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10,
        candidate_k: int = 50,
        ticker: str | None = None,
        fiscal_year: int | None = None,
        filing_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute hybrid search and return structured passage dictionaries."""
        if not query or not query.strip():
            return []

        # 1. Generate query embedding synchronously (CPU inference)
        embeddings = self.embedding_service.generate_embeddings([query])
        if not embeddings:
            return []
        query_embedding = embeddings[0]

        # 2. Execute vector and lexical retrievers concurrently
        vector_task = VectorRetriever.retrieve(
            db=db,
            query_embedding=query_embedding,
            limit=candidate_k,
            ticker=ticker,
            fiscal_year=fiscal_year,
            filing_type=filing_type,
        )
        lexical_task = LexicalRetriever.retrieve(
            db=db,
            query_text=query,
            limit=candidate_k,
            ticker=ticker,
            fiscal_year=fiscal_year,
            filing_type=filing_type,
        )
        results = await asyncio.gather(vector_task, lexical_task, return_exceptions=True)
        vector_ids = results[0] if isinstance(results[0], list) else []
        lexical_ids = results[1] if isinstance(results[1], list) else []

        if not vector_ids and not lexical_ids:
            return []

        # 3. Fuse rankings via RRF
        fused = reciprocal_rank_fusion([vector_ids, lexical_ids], k=60)
        top_fused = fused[:limit]
        top_ids = [cid for cid, _ in top_fused]
        score_map = dict(top_fused)

        # 4. Fetch full chunk ORM objects
        chunks = await ChunkByIdRetriever.retrieve(db=db, chunk_ids=top_ids)

        # 5. Format structured passage results
        passages = []
        for chunk in chunks:
            doc = chunk.document
            passages.append(
                {
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "ticker": doc.ticker if doc else "UNKNOWN",
                    "fiscal_year": doc.fiscal_year if doc else 0,
                    "filing_type": doc.filing_type if doc else "UNKNOWN",
                    "section_name": chunk.section_name or "General",
                    "chunk_index": chunk.chunk_index,
                    "text_content": chunk.text_content,
                    "score": round(score_map.get(chunk.id, 0.0), 4),
                }
            )

        return passages

    async def get_chunk_with_context(
        self,
        db: AsyncSession,
        document_id: UUID,
        chunk_index: int,
        window: int = 1,
    ) -> dict[str, Any]:
        """Fetch a chunk along with surrounding adjacent chunks for deeper reading."""
        chunks = await SurroundingChunkRetriever.retrieve(
            db=db,
            document_id=document_id,
            chunk_index=chunk_index,
            window=window,
        )
        if not chunks:
            return {}

        combined_text = "\n\n---\n\n".join(
            f"[Chunk {c.chunk_index} | Section: {c.section_name or 'General'}]\n{c.text_content}"
            for c in chunks
        )
        target_chunk = next((c for c in chunks if c.chunk_index == chunk_index), chunks[0])
        doc = target_chunk.document

        return {
            "document_id": str(document_id),
            "target_chunk_index": chunk_index,
            "window": window,
            "ticker": doc.ticker if doc else "UNKNOWN",
            "fiscal_year": doc.fiscal_year if doc else 0,
            "filing_type": doc.filing_type if doc else "UNKNOWN",
            "combined_text": combined_text,
        }

    async def get_chunk_by_id_with_context(
        self,
        db: AsyncSession,
        chunk_id: UUID,
        window: int = 1,
    ) -> dict[str, Any]:
        """Fetch a chunk by ID along with surrounding adjacent chunks."""
        chunks = await ChunkByIdRetriever.retrieve(db=db, chunk_ids=[chunk_id])
        if not chunks:
            return {"error": f"Chunk {chunk_id} not found"}

        target = chunks[0]
        return await self.get_chunk_with_context(
            db=db,
            document_id=target.document_id,
            chunk_index=target.chunk_index,
            window=window,
        )
