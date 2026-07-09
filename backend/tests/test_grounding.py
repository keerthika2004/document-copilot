"""Unit tests for citation validation and grounding enforcement."""

from dataclasses import dataclass
from uuid import uuid4

from app.grounding.validator import validate_citations_existence, validate_grounded_answer


@dataclass
class DummyCitation:
    chunk_id: str
    ticker: str = "AMZN"
    fiscal_year: int = 2025


def test_validate_citations_existence_valid():
    cid1 = str(uuid4())
    cid2 = str(uuid4())
    citations = [DummyCitation(chunk_id=cid1), DummyCitation(chunk_id=cid2)]
    valid_ids = {cid1, cid2}

    validated = validate_citations_existence(citations, valid_ids)
    assert len(validated) == 2
    assert validated[0].chunk_id == cid1
    assert validated[1].chunk_id == cid2


def test_validate_citations_existence_drops_hallucinated():
    valid_id = str(uuid4())
    fake_id = str(uuid4())
    citations = [DummyCitation(chunk_id=valid_id), DummyCitation(chunk_id=fake_id)]
    valid_ids = {valid_id}

    validated = validate_citations_existence(citations, valid_ids)
    assert len(validated) == 1
    assert validated[0].chunk_id == valid_id


def test_validate_grounded_answer_adjusts_insufficient_evidence_when_no_citations():
    answer = "Amazon operating income for AWS was $25.0 billion in fiscal 2024 with a margin of 28.5%."
    citations = []

    validated_cites, sufficient, confidence = validate_grounded_answer(
        answer_text=answer,
        citations=citations,
        has_sufficient_evidence=True,
        confidence_summary="High confidence based on report.",
        valid_chunk_ids=set(),
    )

    assert validated_cites == []
    assert sufficient is False
    assert "High confidence" in confidence


def test_validate_grounded_answer_preserves_refusal():
    answer = "The provided SEC filings do not mention or disclose any information regarding crypto asset holdings."
    citations = []

    validated_cites, sufficient, confidence = validate_grounded_answer(
        answer_text=answer,
        citations=citations,
        has_sufficient_evidence=True,
        confidence_summary="No information found.",
        valid_chunk_ids=set(),
    )

    # Since it explicitly states lack of info ("do not mention"), it remains a clean refusal
    assert validated_cites == []
    assert sufficient is True
