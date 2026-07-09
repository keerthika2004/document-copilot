"""PydanticAI agent definition and tool implementations for SEC Filing Copilot."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic_ai import Agent, RunContext
from sqlalchemy import select

from app.assistant.deps import DocumentAgentDeps
from app.assistant.instructions import SYSTEM_PROMPT
from app.assistant.outputs import GroundedAnswer
from app.config import settings
from app.database.models.source_document import SourceDocument


# Create the PydanticAI agent with structured output and dependency injection
document_agent = Agent(
    model=settings.llm_model,
    output_type=GroundedAnswer,
    deps_type=DocumentAgentDeps,
    system_prompt=SYSTEM_PROMPT,
    defer_model_check=True,
    model_settings={"temperature": 0.0},
)



@document_agent.tool
async def search_filings(
    ctx: RunContext[DocumentAgentDeps],
    query: str,
    ticker: str | None = None,
    fiscal_year: int | None = None,
    filing_type: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]] | str:
    """Search SEC filings using hybrid keyword and vector retrieval (RRF).

    Args:
        ctx: Agent run context containing database session and retriever.
        query: Natural language search query or keywords.
        ticker: Optional company ticker filter (e.g., 'AAPL', 'MSFT').
        fiscal_year: Optional fiscal year filter (e.g., 2023, 2024).
        filing_type: Optional filing type filter (e.g., '10-K', '10-Q').
        limit: Max number of passages to return (default 10, max 15).

    Returns:
        List of matching passage dictionaries or error string.
    """
    try:
        bounded_limit = min(max(1, limit), 15)
        results = await ctx.deps.retriever.search(
            db=ctx.deps.db,
            query=query,
            limit=bounded_limit,
            ticker=ticker,
            fiscal_year=fiscal_year,
            filing_type=filing_type,
        )
        if not results:
            return "No matching passages found for the given query and filters."
        return results
    except Exception as exc:
        return f"Error executing search: {exc!s}"


@document_agent.tool
async def read_chunk_with_context(
    ctx: RunContext[DocumentAgentDeps],
    chunk_id: str,
    window: int = 1,
) -> dict[str, Any] | str:
    """Read a specific chunk by UUID along with adjacent surrounding paragraphs for deeper context.

    Args:
        ctx: Agent run context.
        chunk_id: UUID string of the target chunk to inspect.
        window: Number of surrounding chunks before and after to include (default 1, max 2).

    Returns:
        Dictionary with combined reading context or error string.
    """
    try:
        try:
            target_uuid = UUID(chunk_id)
        except ValueError:
            return f"Error: Invalid chunk_id format '{chunk_id}'. Must be a valid UUID string."

        bounded_window = min(max(0, window), 2)
        result = await ctx.deps.retriever.get_chunk_by_id_with_context(
            db=ctx.deps.db,
            chunk_id=target_uuid,
            window=bounded_window,
        )
        if "error" in result:
            return str(result["error"])
        return result
    except Exception as exc:
        return f"Error reading chunk context: {exc!s}"


@document_agent.tool
async def list_available_filings(
    ctx: RunContext[DocumentAgentDeps],
    ticker: str | None = None,
) -> list[dict[str, Any]] | str:
    """List all SEC filings available in the database corpus.

    Args:
        ctx: Agent run context.
        ticker: Optional company ticker filter to check specific filings.

    Returns:
        List of available filing summary dictionaries or error string.
    """
    try:
        stmt = select(SourceDocument).order_by(
            SourceDocument.ticker.asc(), SourceDocument.fiscal_year.desc()
        )
        if ticker:
            stmt = stmt.where(SourceDocument.ticker == ticker.upper())

        result = await ctx.deps.db.execute(stmt)
        docs = result.scalars().all()
        if not docs:
            return "No filings found in the database matching the criteria."

        return [
            {
                "ticker": doc.ticker,
                "company_name": doc.company_name,
                "filing_type": doc.filing_type,
                "fiscal_year": doc.fiscal_year,
                "accession_number": doc.accession_number,
            }
            for doc in docs
        ]
    except Exception as exc:
        return f"Error listing filings: {exc!s}"
