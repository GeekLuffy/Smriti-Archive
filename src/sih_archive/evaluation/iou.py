"""
Bounding box Intersection over Union (IoU) and greedy bipartite matching (Requirement R5).

Computes spatial alignment between OCR hypothesis token regions and ground truth reference
bounding boxes, reporting precision, recall, F1, and mean IoU.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
from sih_archive.schemas.evaluation import BoundingBoxMetrics


def compute_iou(box_a: Sequence[int], box_b: Sequence[int]) -> float:
    """
    Computes Intersection over Union (IoU) between two bounding boxes in [x, y, w, h] format.

    Parameters:
        box_a: [x, y, w, h]
        box_b: [x, y, w, h]

    Returns:
        Float IoU score in range [0.0, 1.0].
    """
    x_a, y_a, w_a, h_a = int(box_a[0]), int(box_a[1]), int(box_a[2]), int(box_a[3])
    x_b, y_b, w_b, h_b = int(box_b[0]), int(box_b[1]), int(box_b[2]), int(box_b[3])

    if w_a <= 0 or h_a <= 0 or w_b <= 0 or h_b <= 0:
        return 0.0

    x1 = max(x_a, x_b)
    y1 = max(y_a, y_b)
    x2 = min(x_a + w_a, x_b + w_b)
    y2 = min(y_a + h_a, y_b + h_b)

    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)
    inter_area = inter_w * inter_h

    if inter_area == 0:
        return 0.0

    area_a = w_a * h_a
    area_b = w_b * h_b
    union_area = area_a + area_b - inter_area

    if union_area <= 0:
        return 0.0

    return float(inter_area / union_area)


def match_bounding_boxes(
    hypothesis_boxes: Sequence[Sequence[int]],
    reference_boxes: Sequence[Sequence[int]],
    iou_threshold: float = 0.5,
) -> Tuple[BoundingBoxMetrics, List[Tuple[int, int, float]]]:
    """
    Performs greedy bipartite matching between hypothesis and reference bounding boxes.

    Parameters:
        hypothesis_boxes: List of candidate [x, y, w, h] boxes from OCR.
        reference_boxes: List of ground truth [x, y, w, h] boxes.
        iou_threshold: Minimum IoU overlap required to consider a match valid.

    Returns:
        Tuple of (BoundingBoxMetrics, list of matched tuples (hyp_idx, ref_idx, iou_score)).
    """
    m = len(hypothesis_boxes)
    n = len(reference_boxes)

    if m == 0 and n == 0:
        metrics = BoundingBoxMetrics(
            total_hypothesis_boxes=0,
            total_reference_boxes=0,
            true_positives=0,
            false_positives=0,
            false_negatives=0,
            precision=1.0,
            recall=1.0,
            f1=1.0,
            mean_iou=0.0,
            iou_threshold=iou_threshold,
            matched_pairs_count=0,
        )
        return metrics, []

    if m == 0 and n > 0:
        metrics = BoundingBoxMetrics(
            total_hypothesis_boxes=0,
            total_reference_boxes=n,
            true_positives=0,
            false_positives=0,
            false_negatives=n,
            precision=0.0,
            recall=0.0,
            f1=0.0,
            mean_iou=0.0,
            iou_threshold=iou_threshold,
            matched_pairs_count=0,
        )
        return metrics, []

    if m > 0 and n == 0:
        metrics = BoundingBoxMetrics(
            total_hypothesis_boxes=m,
            total_reference_boxes=0,
            true_positives=0,
            false_positives=m,
            false_negatives=0,
            precision=0.0,
            recall=0.0,
            f1=0.0,
            mean_iou=0.0,
            iou_threshold=iou_threshold,
            matched_pairs_count=0,
        )
        return metrics, []

    # Calculate all pairwise IoUs
    candidates: List[Tuple[float, int, int]] = []
    for h_idx, h_box in enumerate(hypothesis_boxes):
        for r_idx, r_box in enumerate(reference_boxes):
            iou_val = compute_iou(h_box, r_box)
            if iou_val >= iou_threshold:
                candidates.append((iou_val, h_idx, r_idx))

    # Sort descending by IoU for greedy assignment
    candidates.sort(key=lambda x: x[0], reverse=True)

    matched_hyp = set()
    matched_ref = set()
    matched_pairs: List[Tuple[int, int, float]] = []

    for iou_val, h_idx, r_idx in candidates:
        if h_idx not in matched_hyp and r_idx not in matched_ref:
            matched_hyp.add(h_idx)
            matched_ref.add(r_idx)
            matched_pairs.append((h_idx, r_idx, float(iou_val)))

    tp = len(matched_pairs)
    fp = m - tp
    fn = n - tp

    precision = float(tp / m) if m > 0 else 0.0
    recall = float(tp / n) if n > 0 else 0.0
    f1 = float(2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    mean_iou = float(sum(p[2] for p in matched_pairs) / tp) if tp > 0 else 0.0

    metrics = BoundingBoxMetrics(
        total_hypothesis_boxes=m,
        total_reference_boxes=n,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        mean_iou=round(mean_iou, 4),
        iou_threshold=iou_threshold,
        matched_pairs_count=tp,
    )
    return metrics, matched_pairs
