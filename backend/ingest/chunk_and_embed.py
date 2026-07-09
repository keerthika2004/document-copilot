"""CLI orchestrator for chunking documents and generating vector embeddings."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database.models.document_chunk import DocumentChunk
from app.database.models.source_document import SourceDocument
from ingest.chunking import DoclingChunkerService
from ingest.embeddings import EmbeddingService


async def main() -> None:
    """Run chunking and embedding pipeline with optional single-chunk verification."""
    parser = argparse.ArgumentParser(
        description="SEC filing chunking and embedding ingestion orchestrator."
    )
    parser.add_argument(
        "--test-one-chunk",
        action="store_true",
        help="Process only 1 chunk of the first document for safety/verification.",
    )

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).resolve().parent
    markdown_dir = (script_dir / "../../data/markdown").resolve()
    manifest_path = markdown_dir / "manifest.json"

    if not manifest_path.exists():
        print(f"Error: manifest.json not found at {manifest_path}")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Build accession number to markdown file mapping
    accession_to_md_path = {
        f["accession_number"]: markdown_dir / Path(f["local_path"]).with_suffix(".md")
        for f in manifest.get("filings", [])
    }

    print("Initializing services...")
    chunker_service = DoclingChunkerService()
    embedding_service = EmbeddingService()

    # Database setup
    engine = create_async_engine(settings.sqlalchemy_database_url)
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session() as session:
        # Fetch all source documents ordered by ticker and fiscal year
        stmt = select(SourceDocument).order_by(
            SourceDocument.ticker, SourceDocument.fiscal_year
        )
        res = await session.execute(stmt)
        documents = list(res.scalars().all())

        print(f"Found {len(documents)} source documents in database.")

        if args.test_one_chunk:
            print(
                "\n--- [SINGLE-CHUNK VERIFICATION MODE ENABLED] ---"
            )
            print(
                "We will process exactly 1 document and upload 1 chunk to verify database and embedding integration.\n"
            )

        total_chunks_saved = 0

        for doc_idx, doc in enumerate(documents, 1):
            md_path = accession_to_md_path.get(doc.accession_number)
            if not md_path or not md_path.exists():
                print(
                    f"Warning: Markdown file missing for {doc.accession_number}. Skipping."
                )
                continue

            if not args.test_one_chunk:
                count_stmt = select(func.count(DocumentChunk.id)).where(
                    DocumentChunk.document_id == doc.id
                )
                count_res = await session.execute(count_stmt)
                existing_count = count_res.scalar() or 0
                if existing_count > 0:
                    print(
                        f"[{doc_idx}/{len(documents)}] {doc.ticker} FY{doc.fiscal_year} already ingested ({existing_count} chunks). Skipping!"
                    )
                    total_chunks_saved += existing_count
                    continue

            print(
                f"[{doc_idx}/{len(documents)}] Chunking {doc.ticker} FY{doc.fiscal_year} ({doc.accession_number})..."
            )
            processed_chunks = chunker_service.process_file(doc, md_path)
            print(f"    Generated {len(processed_chunks)} semantic chunks.")

            if args.test_one_chunk:
                # In verification mode, restrict to only the very first chunk (index 0)
                processed_chunks = processed_chunks[:1]
                print("    [Test Mode]: Restricting to chunk index 0.")

            # Extract texts for batch embedding
            texts = [c.text_content for c in processed_chunks]
            print(
                f"    Generating embeddings for {len(texts)} chunks via local model..."
            )
            embeddings = embedding_service.generate_embeddings(texts)

            # Persist chunks into PostgreSQL
            for c_data, emb_vec in zip(processed_chunks, embeddings):
                # Check for existing chunk to allow idempotent upserts
                chunk_stmt = select(DocumentChunk).where(
                    DocumentChunk.document_id == doc.id,
                    DocumentChunk.chunk_index == c_data.chunk_index,
                )
                chunk_res = await session.execute(chunk_stmt)
                existing_chunk = chunk_res.scalar_one_or_none()

                if existing_chunk:
                    existing_chunk.text_content = c_data.text_content
                    existing_chunk.section_name = c_data.section_name
                    existing_chunk.page_number = c_data.page_number
                    existing_chunk.embedding = emb_vec
                    existing_chunk.metadata_json = c_data.metadata_json
                    chunk_obj = existing_chunk
                else:
                    chunk_obj = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=c_data.chunk_index,
                        page_number=c_data.page_number,
                        section_name=c_data.section_name,
                        text_content=c_data.text_content,
                        embedding=emb_vec,
                        metadata_json=c_data.metadata_json,
                    )
                    session.add(chunk_obj)

                total_chunks_saved += 1

            await session.commit()
            print(
                f"    Committed {len(processed_chunks)} chunks to PostgreSQL."
            )

            if args.test_one_chunk:
                print(
                    "\n--- [SINGLE-CHUNK VERIFICATION SUCCESSFUL] ---"
                )
                print(
                    f"Saved chunk ID: {chunk_obj.id} (index {chunk_obj.chunk_index})"
                )
                print(f"Section:        {chunk_obj.section_name}")
                print(
                    f"Embedding dim:  {len(chunk_obj.embedding) if chunk_obj.embedding else 0}"
                )
                print(f"Metadata:       {chunk_obj.metadata_json}")
                print(
                    "\nVerify the database record above. Stopping early as requested."
                )
                break

    print(
        f"\nIngestion pipeline finished! Total chunks saved: {total_chunks_saved}"
    )


if __name__ == "__main__":
    asyncio.run(main())
