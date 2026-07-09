"""Unit tests for retrieval pipeline and Reciprocal Rank Fusion (RRF)."""

from uuid import uuid4

import pytest

from app.retrieval.fusion import reciprocal_rank_fusion


def test_reciprocal_rank_fusion_basic() -> None:
    """Test RRF fusion across two ranked lists with overlapping items."""
    id1, id2, id3, id4 = uuid4(), uuid4(), uuid4(), uuid4()

    list_a = [id1, id2, id3]
    list_b = [id2, id3, id4]

    fused = reciprocal_rank_fusion([list_a, list_b], k=60)

    # id2 is rank 2 in list_a (1/62) and rank 1 in list_b (1/61)
    # id3 is rank 3 in list_a (1/63) and rank 2 in list_b (1/62)
    # id1 is rank 1 in list_a (1/61)
    # id4 is rank 3 in list_b (1/63)

    expected_order = [id2, id3, id1, id4]
    actual_order = [item for item, _ in fused]

    assert actual_order == expected_order

    # Verify exact scores
    score_map = dict(fused)
    assert score_map[id2] == pytest.approx(1.0 / 62 + 1.0 / 61)
    assert score_map[id3] == pytest.approx(1.0 / 63 + 1.0 / 62)
    assert score_map[id1] == pytest.approx(1.0 / 61)
    assert score_map[id4] == pytest.approx(1.0 / 63)


def test_reciprocal_rank_fusion_empty() -> None:
    """Test RRF with empty lists and no inputs."""
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []


def test_reciprocal_rank_fusion_single_list() -> None:
    """Test RRF with a single input ranking."""
    id1, id2 = uuid4(), uuid4()
    fused = reciprocal_rank_fusion([[id1, id2]], k=10)

    assert len(fused) == 2
    assert fused[0] == (id1, pytest.approx(1.0 / 11))
    assert fused[1] == (id2, pytest.approx(1.0 / 12))
