import asyncio
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import settings and models from the backend app
from app.config import settings
from app.database.models.source_document import SourceDocument

TICKER_TO_COMPANY = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc.",
    "NVDA": "NVIDIA Corporation",
}


async def seed_documents():
    # From backend/ingest/seed_source_documents.py, data/markdown is at ../../data/markdown
    script_dir = Path(__file__).resolve().parent
    markdown_dir = (script_dir / "../../data/markdown").resolve()
    manifest_path = markdown_dir / "manifest.json"

    print(f"Reading manifest from: {manifest_path}")
    print(f"Reading markdown from: {markdown_dir}")

    if not manifest_path.exists():
        print(f"Error: manifest.json not found at {manifest_path}")
        return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    # Create direct async database engine using backend settings
    engine = create_async_engine(settings.sqlalchemy_database_url)
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session() as session:
        for filing in manifest["filings"]:
            ticker = filing["ticker"]
            accession_number = filing["accession_number"]
            filing_date_str = filing["filing_date"]
            report_date_str = filing["report_date"]
            source_url = filing["source_url"]

            # Map the local HTML path in manifest to the parsed .md path
            local_path = Path(filing["local_path"])
            local_md_path = markdown_dir / local_path.with_suffix(".md")

            if not local_md_path.exists():
                print(f"Warning: Markdown file not found at {local_md_path}. Skipping.")
                continue

            with open(local_md_path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            # Parse metadata parameters
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
            report_date = datetime.strptime(report_date_str, "%Y-%m-%d")
            fiscal_year = report_date.year
            company_name = TICKER_TO_COMPANY.get(ticker, "Unknown Company")

            # Check if document already exists to avoid duplicates
            stmt = select(SourceDocument).where(
                SourceDocument.accession_number == accession_number
            )
            res = await session.execute(stmt)
            existing_doc = res.scalar_one_or_none()

            if existing_doc:
                print(
                    f"Document {accession_number} ({ticker} {fiscal_year}) already exists. Updating content..."
                )
                existing_doc.raw_content = raw_content
                existing_doc.source_url = source_url
            else:
                print(
                    f"Inserting new document {accession_number} ({ticker} {fiscal_year})..."
                )
                doc = SourceDocument(
                    ticker=ticker,
                    company_name=company_name,
                    filing_type="10-K",
                    filing_date=filing_date,
                    fiscal_year=fiscal_year,
                    fiscal_period="FY",
                    accession_number=accession_number,
                    source_url=source_url,
                    raw_content=raw_content,
                )
                session.add(doc)

        await session.commit()
    print("Database seeding of source documents complete!")


if __name__ == "__main__":
    asyncio.run(seed_documents())
