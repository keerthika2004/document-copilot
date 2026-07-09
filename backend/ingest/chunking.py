"""Docling chunker factory and document chunking module."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HybridChunker

if TYPE_CHECKING:
    from app.database.models.source_document import SourceDocument


@dataclass
class ProcessedChunk:
    """Structured data container for a processed document chunk."""

    chunk_index: int
    text_content: str
    section_name: str | None
    page_number: int | None
    metadata_json: dict[str, Any]


class DoclingChunkerService:
    """Service wrapper around Docling DocumentConverter and HybridChunker."""

    def __init__(self, max_tokens: int = 500, merge_peers: bool = True) -> None:
        """Initialize converter and hybrid chunker with token refinement."""
        self.converter = DocumentConverter()
        self.chunker = HybridChunker(
            max_tokens=max_tokens,
            merge_peers=merge_peers,
        )

    def process_file(
        self, doc_record: SourceDocument, md_path: Path
    ) -> list[ProcessedChunk]:
        """Convert a markdown file and split it into semantic chunks."""
        if not md_path.exists():
            raise FileNotFoundError(f"Markdown file not found at {md_path}")

        # Convert markdown file into DoclingDocument
        conv_result = self.converter.convert(md_path)
        docling_doc = conv_result.document

        # Generate chunks using HybridChunker (built on Hierarchical layout analysis)
        raw_chunks = list(self.chunker.chunk(docling_doc))

        processed_chunks: list[ProcessedChunk] = []
        for idx, chunk in enumerate(raw_chunks):
            headings = getattr(chunk.meta, "headings", None) or []
            section_name = " > ".join(headings) if headings else None
            if section_name and len(section_name) > 255:
                section_name = section_name[:252] + "..."

            # Attempt page number extraction from provenance if available
            page_number: int | None = None
            doc_items = getattr(chunk.meta, "doc_items", None) or []
            for item in doc_items:
                prov = getattr(item, "prov", None) or []
                for p in prov:
                    page_no = getattr(p, "page_no", None)
                    if isinstance(page_no, int):
                        page_number = page_no
                        break
                if page_number is not None:
                    break

            metadata_json = {
                "headings": headings,
                "ticker": doc_record.ticker,
                "fiscal_year": doc_record.fiscal_year,
                "filing_type": doc_record.filing_type,
                "accession_number": doc_record.accession_number,
                "company_name": doc_record.company_name,
            }

            processed_chunks.append(
                ProcessedChunk(
                    chunk_index=idx,
                    text_content=chunk.text,
                    section_name=section_name,
                    page_number=page_number,
                    metadata_json=metadata_json,
                )
            )

        return processed_chunks
