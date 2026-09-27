"""Unit tests for Bounding Box IoU matching and Reading Order evaluation (Requirement R5)."""

import pytest
from sih_archive.evaluation.iou import compute_iou, match_bounding_boxes
from sih_archive.evaluation.reading_order import (
    KendallTauReadingOrderEvaluator,
    ReadingOrderEvaluator,
)
from sih_archive.schemas.evaluation import BoundingBoxMetrics


def test_compute_iou_identical_boxes():
    """Verify IoU of identical boxes is 1.0."""
    box = [10, 20, 100, 50]
    assert compute_iou(box, box) == 1.0


def test_compute_iou_disjoint_boxes():
    """Verify IoU of non-overlapping boxes is 0.0."""
    b1 = [0, 0, 50, 50]
    b2 = [60, 60, 50, 50]
    assert compute_iou(b1, b2) == 0.0


def test_compute_iou_partial_overlap():
    """Verify IoU calculation on known partial overlap geometry."""
    # Box A: [0, 0, 100, 100] (area 10,000)
    # Box B: [50, 0, 100, 100] (area 10,000)
    # Intersection: [50, 0, 50, 100] (area 5,000)
    # Union: 10,000 + 10,000 - 5,000 = 15,000
    # Expected IoU: 5000 / 15000 = 1/3 ~ 0.333333
    b1 = [0, 0, 100, 100]
    b2 = [50, 0, 100, 100]
    expected = 5000.0 / 15000.0
    assert compute_iou(b1, b2) == pytest.approx(expected, rel=1e-4)


def test_compute_iou_degenerate_boxes():
    """Verify IoU returns 0.0 when width or height is zero or negative."""
    assert compute_iou([0, 0, 0, 50], [0, 0, 50, 50]) == 0.0
    assert compute_iou([0, 0, 50, -10], [0, 0, 50, 50]) == 0.0


def test_match_bounding_boxes_perfect():
    """Verify bipartite matching on identical sets of boxes produces 1.0 precision, recall, and F1."""
    boxes = [
        [10, 10, 50, 20],
        [70, 10, 60, 20],
        [10, 40, 100, 20],
    ]
    metrics, matched = match_bounding_boxes(boxes, boxes, iou_threshold=0.5)

    assert metrics.true_positives == 3
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0
    assert metrics.mean_iou == 1.0
    assert len(matched) == 3


def test_match_bounding_boxes_both_empty():
    """Verify bipartite matching when both hypothesis and reference are empty."""
    metrics, matched = match_bounding_boxes([], [], iou_threshold=0.5)
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0
    assert metrics.true_positives == 0
    assert len(matched) == 0


def test_match_bounding_boxes_empty_hypothesis():
    """Verify bipartite matching when hypothesis has 0 boxes but reference has boxes."""
    ref_boxes = [[10, 10, 50, 20], [70, 10, 60, 20]]
    metrics, matched = match_bounding_boxes([], ref_boxes, iou_threshold=0.5)

    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0
    assert metrics.true_positives == 0
    assert metrics.false_negatives == 2
    assert len(matched) == 0


def test_match_bounding_boxes_empty_reference():
    """Verify bipartite matching when hypothesis has boxes but reference is empty."""
    hyp_boxes = [[10, 10, 50, 20]]
    metrics, matched = match_bounding_boxes(hyp_boxes, [], iou_threshold=0.5)

    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0
    assert metrics.true_positives == 0
    assert metrics.false_positives == 1
    assert len(matched) == 0


def test_match_bounding_boxes_greedy_contention():
    """
    Verify greedy matching resolves contention:
    Hypothesis box 1 has IoU 0.9 with Ref 0.
    Hypothesis box 2 has IoU 0.6 with Ref 0.
    Ref 0 must be matched to Hyp 1, leaving Hyp 2 as false positive.
    """
    ref = [[0, 0, 100, 100]]
    # Hyp 0 overlaps slightly (w=100, h=100, offset 5 -> high overlap ~ 0.9)
    hyp_0 = [5, 0, 100, 100]
    # Hyp 1 overlaps moderately (offset 30 -> lower overlap ~ 0.53)
    hyp_1 = [30, 0, 100, 100]

    metrics, matched = match_bounding_boxes([hyp_0, hyp_1], ref, iou_threshold=0.5)
    assert metrics.true_positives == 1
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 0
    assert matched[0][0] == 0  # hyp_0 matched
    assert matched[0][1] == 0  # ref 0 matched


def test_match_bounding_boxes_threshold_filtering():
    """Verify pairs with IoU below threshold tau are not matched."""
    ref = [[0, 0, 100, 100]]
    hyp = [[60, 0, 100, 100]]  # IoU is 40/160 = 0.25 < 0.5

    metrics, matched = match_bounding_boxes(hyp, ref, iou_threshold=0.5)
    assert metrics.true_positives == 0
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert len(matched) == 0


def test_kendall_tau_reading_order_concordant():
    """Verify Kendall's Tau is 1.0 for perfectly preserved reading order sequence."""
    evaluator = KendallTauReadingOrderEvaluator()
    # (hyp_idx, ref_idx) pairs in natural monotonic order
    matched_pairs = [(0, 0), (1, 1), (2, 2), (3, 3)]
    res = evaluator.evaluate(matched_pairs)

    assert res["score"] == 1.0
    assert res["kendall_tau"] == 1.0
    assert res["normalized_inversion_distance"] == 0.0
    assert res["discordant_pairs"] == 0
    assert res["matched_count"] == 4


def test_kendall_tau_reading_order_inverted():
    """Verify Kendall's Tau is -1.0 and score 0.0 for completely inverted reading order."""
    evaluator = KendallTauReadingOrderEvaluator()
    # Hyp indices [3, 2, 1, 0] for ref [0, 1, 2, 3]
    matched_pairs = [(3, 0), (2, 1), (1, 2), (0, 3)]
    res = evaluator.evaluate(matched_pairs)

    assert res["kendall_tau"] == -1.0
    assert res["normalized_inversion_distance"] == 1.0
    assert res["score"] == 0.0
    assert res["concordant_pairs"] == 0
    assert res["discordant_pairs"] == 6  # 4*3/2 = 6


def test_kendall_tau_reading_order_single_or_empty():
    """Verify reading order score defaults to 1.0 on 0 or 1 matched region."""
    evaluator = KendallTauReadingOrderEvaluator()
    assert evaluator.evaluate([])["score"] == 1.0
    assert evaluator.evaluate([(0, 0)])["score"] == 1.0
