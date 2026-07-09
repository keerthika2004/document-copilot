"""Structured Pydantic output models for the assistant agent."""

from __future__ import annotations

from typing import Union
from pydantic import BaseModel, Field, field_validator


class SourcePassage(BaseModel):
    """A retrieved document chunk with formatting and ranking score."""

    chunk_id: str = Field(..., description="Unique UUID string of the document chunk")
    document_id: str = Field(..., description="Unique UUID string of the parent filing")
    ticker: str = Field(..., description="Company ticker symbol (e.g., AAPL)")
    fiscal_year: int = Field(..., description="Fiscal year of the filing (e.g., 2023)")
    filing_type: str = Field(..., description="SEC filing type (e.g., 10-K)")
    section_name: str = Field(..., description="Heading or section name within the filing")
    chunk_index: int = Field(..., description="Sequential index of the chunk in the filing")
    text_content: str = Field(..., description="Raw text content of the passage")
    score: float = Field(..., description="Reciprocal Rank Fusion (RRF) score")


class Citation(BaseModel):
    """An exact citation mapping a factual claim to a retrieved filing chunk."""

    ticker: str = Field(..., description="Company ticker symbol (e.g., AAPL)")
    fiscal_year: int = Field(..., description="Fiscal year of the filing (e.g., 2023)")
    section_name: str = Field(..., description="Section heading where the evidence resides")
    chunk_id: str = Field(..., description="Exact chunk UUID where the quote was found")
    exact_quote: str = Field(
        ..., description="Exact verbatim substring quote from the retrieved chunk supporting the claim"
    )


class GroundedAnswer(BaseModel):
    """The final structured answer returned by the assistant agent."""

    answer: str = Field(
        ...,
        description="Detailed Markdown response addressing the user's prompt based ONLY on retrieved evidence. MUST embed inline citation markers ([1], [2], [3], etc.) immediately after every factual sentence, bullet point, or paragraph, corresponding sequentially to the `citations` list.",
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Sequential list of verified citations corresponding 1-to-1 with the inline markers ([1], [2], etc.) embedded inside `answer`.",
    )
    has_sufficient_evidence: Union[bool, str] = Field(
        ...,
        description="Whether retrieved filings contain enough evidence to answer definitively (boolean true or false)",
    )
    confidence_summary: str = Field(
        ...,
        description="Brief explanation of evidence quality, completeness, and any data limitations encountered",
    )

    @field_validator("has_sufficient_evidence", mode="after")
    @classmethod
    def parse_evidence_bool(cls, v: Union[bool, str]) -> bool:
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ("true", "1", "yes")
