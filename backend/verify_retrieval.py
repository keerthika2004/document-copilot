"""End-to-end verification script for Phase 9, 10 & 11 retrieval and tools against PostgreSQL."""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assistant import document_agent
from app.config import settings
from app.retrieval import HybridRetriever


async def main() -> None:
    print("Connecting to PostgreSQL database...")
    engine = create_async_engine(settings.sqlalchemy_database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        print("\n--- 1. Testing list_available_filings tool ---")
        list_tool = document_agent._function_toolset.tools["list_available_filings"].function
        class MockCtx:
            class deps:
                pass
        mock_ctx = MockCtx()
        mock_ctx.deps.db = db
        mock_ctx.deps.retriever = HybridRetriever()

        filings = await list_tool(mock_ctx, ticker="AAPL")
        if isinstance(filings, list):
            print(f"Found {len(filings)} AAPL filings in database:")
            for f in filings[:3]:
                print(f"  - [{f['ticker']}] {f['filing_type']} FY{f['fiscal_year']} ({f['accession_number']})")
        else:
            print("Result:", filings)

        print("\n--- 2. Testing Hybrid Search (RRF: Vector + Lexical) ---")
        retriever = HybridRetriever()
        query = "artificial intelligence and machine learning competition risks"
        print(f"Query: '{query}' (Ticker: NVDA)")
        
        passages = await retriever.search(
            db=db,
            query=query,
            ticker="NVDA",
            limit=3,
        )
        print(f"Retrieved {len(passages)} passages via RRF:")
        for i, p in enumerate(passages, 1):
            print(f"  {i}. [Score: {p['score']}] {p['ticker']} FY{p['fiscal_year']} - {p['section_name']}")
            print(f"     Excerpt: {p['text_content'][:150]}...")

        if passages:
            top_chunk_id = passages[0]["chunk_id"]
            print("\n--- 3. Testing Context Expansion (read_chunk_with_context) ---")
            print(f"Expanding context for top chunk {top_chunk_id} (window=1)...")
            read_tool = document_agent._function_toolset.tools["read_chunk_with_context"].function
            context_res = await read_tool(mock_ctx, chunk_id=top_chunk_id, window=1)
            if isinstance(context_res, dict):
                print(f"Combined Text Length: {len(context_res.get('combined_text', ''))} characters")
                print("First 250 chars of expanded context:")
                print("--------------------------------------------------")
                print(context_res.get("combined_text", "")[:250])
                print("--------------------------------------------------")
            else:
                print("Result:", context_res)

    await engine.dispose()
    print("\nVerification completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
