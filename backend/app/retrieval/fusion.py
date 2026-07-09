"""Reciprocal Rank Fusion (RRF) algorithm for combining ranked lists."""

from __future__ import annotations

from collections import defaultdict
from typing import TypeVar

T = TypeVar("T")


def reciprocal_rank_fusion(
    rankings: list[list[T]], k: int = 60
) -> list[tuple[T, float]]:
    """Fuse multiple ranked lists of items into one ranked list using RRF.

    Args:
        rankings: A list of ranked lists (e.g. from dense and sparse retrieval).
        k: Smoothing constant, conventionally set to 60.

    Returns:
        A list of (item, rrf_score) tuples sorted by descending RRF score.
    """
    scores: dict[T, float] = defaultdict(float)
    for ranking in rankings:
        for rank, item in enumerate(ranking, 1):
            scores[item] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
