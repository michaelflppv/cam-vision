"""
Intersection over Union (IoU) utilities for object tracking.

IoU is a standard metric for measuring bbox overlap. It's the ratio of
the intersection area to the union area of two bounding boxes.

IoU = Area(Intersection) / Area(Union)

- IoU = 1.0: Perfect overlap (identical boxes)
- IoU = 0.0: No overlap
- IoU > 0.5: Generally considered a good match for tracking

For tracking, we use IoU to determine if a new detection matches an existing
track. A typical threshold is 0.5, meaning the boxes must overlap by at least 50%.
"""

from __future__ import annotations

from ..types import BBox


def compute_iou(bbox1: BBox, bbox2: BBox) -> float:
    """
    Compute Intersection over Union (IoU) between two bounding boxes.

    Args:
        bbox1: First bounding box
        bbox2: Second bounding box

    Returns:
        IoU score (0.0 to 1.0)
            - 1.0: Perfect overlap (identical boxes)
            - 0.5: 50% overlap (common matching threshold)
            - 0.0: No overlap

    Examples:
        >>> bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        >>> bbox2 = BBox(x1=50, y1=50, x2=150, y2=150)
        >>> compute_iou(bbox1, bbox2)
        0.14285714285714285  # Small overlap

        >>> bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        >>> bbox2 = BBox(x1=0, y1=0, x2=100, y2=100)
        >>> compute_iou(bbox1, bbox2)
        1.0  # Perfect overlap
    """
    # Calculate intersection rectangle
    x1_inter = max(bbox1.x1, bbox2.x1)
    y1_inter = max(bbox1.y1, bbox2.y1)
    x2_inter = min(bbox1.x2, bbox2.x2)
    y2_inter = min(bbox1.y2, bbox2.y2)

    # Check if boxes overlap
    if x2_inter <= x1_inter or y2_inter <= y1_inter:
        return 0.0

    # Calculate intersection area
    intersection_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)

    # Calculate union area
    area1 = bbox1.area()
    area2 = bbox2.area()
    union_area = area1 + area2 - intersection_area

    # Avoid division by zero
    if union_area == 0:
        return 0.0

    return intersection_area / union_area


def compute_centroid_distance(bbox1: BBox, bbox2: BBox) -> float:
    """
    Compute Euclidean distance between centroids of two bounding boxes.

    This is a fallback metric when IoU is not applicable (e.g., very small boxes
    or boxes that don't overlap but are close). Useful for tracking fast-moving
    objects where bbox might not overlap between frames.

    Args:
        bbox1: First bounding box
        bbox2: Second bounding box

    Returns:
        Distance in pixels between centroids

    Examples:
        >>> bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        >>> bbox2 = BBox(x1=0, y1=0, x2=100, y2=100)
        >>> compute_centroid_distance(bbox1, bbox2)
        0.0  # Same centroid

        >>> bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        >>> bbox2 = BBox(x1=100, y1=0, x2=200, y2=100)
        >>> compute_centroid_distance(bbox1, bbox2)
        100.0  # Centroids 100px apart
    """
    # Calculate centroids
    cx1 = (bbox1.x1 + bbox1.x2) / 2.0
    cy1 = (bbox1.y1 + bbox1.y2) / 2.0

    cx2 = (bbox2.x1 + bbox2.x2) / 2.0
    cy2 = (bbox2.y1 + bbox2.y2) / 2.0

    # Compute Euclidean distance
    distance = ((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2) ** 0.5

    return distance
