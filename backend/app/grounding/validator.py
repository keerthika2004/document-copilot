"""Grounding validator to enforce citation completeness and chunk validity."""

import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


def validate_citations_existence(citations: list[Any], valid_chunk_ids: set[UUID | str]) -> list[Any]:
    """Filter citations to only those whose chunk_id exists in valid_chunk_ids.

    Logs a warning when a hallucinated or unretrieved chunk ID is detected.
    """
    if not citations:
        return []

    # Normalize valid_chunk_ids to strings for comparison
    normalized_valid = {str(cid) for cid in valid_chunk_ids}
    validated = []

    for cit in citations:
        chunk_id = getattr(cit, "chunk_id", None) or (cit.get("chunk_id") if isinstance(cit, dict) else None)
        if not chunk_id:
            continue
        if str(chunk_id) in normalized_valid:
            validated.append(cit)
        else:
            logger.warning(
                "Grounding validation: Dropping hallucinated or invalid citation chunk_id=%s (ticker=%s)",
                chunk_id,
                getattr(cit, "ticker", "unknown") if not isinstance(cit, dict) else cit.get("ticker", "unknown"),
            )

    return validated


def validate_grounded_answer(
    answer_text: str,
    citations: list[Any],
    has_sufficient_evidence: bool,
    confidence_summary: str,
    valid_chunk_ids: set[UUID | str] | None = None,
) -> tuple[list[Any], bool, str]:
    """Validate and enforce grounding invariants on the final assistant answer.

    Returns:
        tuple of (validated_citations, has_sufficient_evidence, confidence_summary)
    """
    validated_citations = citations

    if valid_chunk_ids is not None:
        validated_citations = validate_citations_existence(citations, valid_chunk_ids)

    # Invariant: If there are factual citations present, evidence is sufficient unless explicitly contradicted.
    # If has_sufficient_evidence is True but 0 citations exist (and answer is more than trivial/refusal length),
    # we adjust sufficient evidence flag to reflect lack of verifiable grounding.
    if has_sufficient_evidence and not validated_citations and len(answer_text.strip()) > 80:
        # Check if the answer itself is a clean refusal / statement of lack of info
        refusal_keywords = [
            "does not mention",
            "do not mention",
            "not mention",
            "does not disclose",
            "do not disclose",
            "not found in",
            "insufficient evidence",
            "no evidence",
            "cannot find",
            "no disclosures",
            "not disclosed",
            "no mention",
        ]
        is_refusal = any(kw in answer_text.lower() for kw in refusal_keywords)
        if not is_refusal:
            logger.warning("Grounding validation: Answer has sufficient_evidence=True but no valid citations found.")
            has_sufficient_evidence = False
            confidence_summary = (
                confidence_summary
                or "Answer lacks verifiable filing citations; please cross-reference primary SEC documents directly."
            )

    return validated_citations, has_sufficient_evidence, confidence_summary
