"""Tests for IoU and centroid distance calculations."""

import pytest

from cam_vision.tracking.iou import compute_centroid_distance, compute_iou
from cam_vision.types import BBox


class TestComputeIoU:
    """Test suite for IoU calculation."""

    def test_identical_boxes_perfect_overlap(self):
        """Test that identical boxes have IoU of 1.0."""
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=0, y1=0, x2=100, y2=100)

        iou = compute_iou(bbox1, bbox2)
        assert iou == 1.0

    def test_no_overlap_returns_zero(self):
        """Test that non-overlapping boxes have IoU of 0.0."""
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=200, y1=200, x2=300, y2=300)

        iou = compute_iou(bbox1, bbox2)
        assert iou == 0.0

    def test_partial_overlap_50_percent(self):
        """Test boxes with 50% overlap."""
        # Box 1: 100x100 = 10,000 area
        # Box 2: 100x100 = 10,000 area
        # Overlap: 50x100 = 5,000 area
        # Union: 10,000 + 10,000 - 5,000 = 15,000
        # IoU: 5,000 / 15,000 = 0.333...
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=50, y1=0, x2=150, y2=100)

        iou = compute_iou(bbox1, bbox2)
        assert pytest.approx(iou, abs=0.001) == 0.333

    def test_one_box_inside_another(self):
        """Test small box completely inside larger box."""
        # Small: 50x50 = 2,500 area
        # Large: 100x100 = 10,000 area
        # Overlap: 2,500 (entire small box)
        # Union: 10,000 (entire large box)
        # IoU: 2,500 / 10,000 = 0.25
        bbox_large = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox_small = BBox(x1=25, y1=25, x2=75, y2=75)

        iou = compute_iou(bbox_large, bbox_small)
        assert iou == 0.25

        # Should be symmetric
        iou_reversed = compute_iou(bbox_small, bbox_large)
        assert iou_reversed == 0.25

    def test_edge_touching_no_overlap(self):
        """Test boxes touching at edge have IoU of 0.0."""
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=100, y1=0, x2=200, y2=100)

        iou = compute_iou(bbox1, bbox2)
        assert iou == 0.0

    def test_corner_touching_no_overlap(self):
        """Test boxes touching at corner have IoU of 0.0."""
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=100, y1=100, x2=200, y2=200)

        iou = compute_iou(bbox1, bbox2)
        assert iou == 0.0

    def test_small_overlap(self):
        """Test boxes with small overlap (~14%)."""
        # Box 1: 100x100 = 10,000 area
        # Box 2: 100x100 = 10,000 area
        # Overlap: 50x50 = 2,500 area
        # Union: 10,000 + 10,000 - 2,500 = 17,500
        # IoU: 2,500 / 17,500 = 0.142857...
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=50, y1=50, x2=150, y2=150)

        iou = compute_iou(bbox1, bbox2)
        assert pytest.approx(iou, abs=0.001) == 0.143

    def test_high_overlap_above_threshold(self):
        """Test boxes with high overlap (>0.5 threshold)."""
        # Box 1: 100x100 = 10,000 area
        # Box 2: 100x100 = 10,000 area
        # Overlap: 80x100 = 8,000 area
        # Union: 10,000 + 10,000 - 8,000 = 12,000
        # IoU: 8,000 / 12,000 = 0.666...
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=20, y1=0, x2=120, y2=100)

        iou = compute_iou(bbox1, bbox2)
        assert pytest.approx(iou, abs=0.001) == 0.667
        assert iou > 0.5  # Above common tracking threshold

    def test_zero_area_boxes(self):
        """Test boxes with zero area."""
        # Degenerate box (line)
        bbox1 = BBox(x1=0, y1=0, x2=0, y2=100)
        bbox2 = BBox(x1=0, y1=0, x2=100, y2=100)

        iou = compute_iou(bbox1, bbox2)
        assert iou == 0.0

    def test_different_aspect_ratios(self):
        """Test boxes with different aspect ratios."""
        # Wide box: 200x50 = 10,000 area
        # Tall box: 50x200 = 10,000 area
        # Overlap: 50x50 = 2,500 area
        # Union: 10,000 + 10,000 - 2,500 = 17,500
        # IoU: 2,500 / 17,500 = 0.142857...
        bbox_wide = BBox(x1=0, y1=0, x2=200, y2=50)
        bbox_tall = BBox(x1=0, y1=0, x2=50, y2=200)

        iou = compute_iou(bbox_wide, bbox_tall)
        assert pytest.approx(iou, abs=0.001) == 0.143


class TestComputeCentroidDistance:
    """Test suite for centroid distance calculation."""

    def test_identical_boxes_zero_distance(self):
        """Test that identical boxes have zero centroid distance."""
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=0, y1=0, x2=100, y2=100)

        distance = compute_centroid_distance(bbox1, bbox2)
        assert distance == 0.0

    def test_horizontal_separation(self):
        """Test boxes separated horizontally."""
        # Centroids: (50, 50) and (150, 50)
        # Distance: 100
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=100, y1=0, x2=200, y2=100)

        distance = compute_centroid_distance(bbox1, bbox2)
        assert distance == 100.0

    def test_vertical_separation(self):
        """Test boxes separated vertically."""
        # Centroids: (50, 50) and (50, 150)
        # Distance: 100
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=0, y1=100, x2=100, y2=200)

        distance = compute_centroid_distance(bbox1, bbox2)
        assert distance == 100.0

    def test_diagonal_separation(self):
        """Test boxes separated diagonally."""
        # Centroids: (50, 50) and (150, 150)
        # Distance: sqrt((100)^2 + (100)^2) = sqrt(20000) = 141.42...
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=100, y1=100, x2=200, y2=200)

        distance = compute_centroid_distance(bbox1, bbox2)
        assert pytest.approx(distance, abs=0.01) == 141.42

    def test_overlapping_boxes_non_zero_distance(self):
        """Test that overlapping boxes can have non-zero centroid distance."""
        # Centroids: (50, 50) and (100, 100)
        # Distance: sqrt((50)^2 + (50)^2) = sqrt(5000) = 70.71...
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=50, y1=50, x2=150, y2=150)

        distance = compute_centroid_distance(bbox1, bbox2)
        assert pytest.approx(distance, abs=0.01) == 70.71

    def test_different_sizes_same_centroid(self):
        """Test boxes with different sizes but same centroid."""
        # Large box: centroid (50, 50)
        # Small box: centroid (50, 50)
        bbox_large = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox_small = BBox(x1=25, y1=25, x2=75, y2=75)

        distance = compute_centroid_distance(bbox_large, bbox_small)
        assert distance == 0.0

    def test_symmetry(self):
        """Test that distance is symmetric (dist(A,B) == dist(B,A))."""
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=50, y1=50, x2=150, y2=150)

        dist_1_2 = compute_centroid_distance(bbox1, bbox2)
        dist_2_1 = compute_centroid_distance(bbox2, bbox1)

        assert dist_1_2 == dist_2_1

    def test_large_separation(self):
        """Test boxes with large separation."""
        # Centroids: (50, 50) and (550, 550)
        # Distance: sqrt((500)^2 + (500)^2) = sqrt(500000) = 707.10...
        bbox1 = BBox(x1=0, y1=0, x2=100, y2=100)
        bbox2 = BBox(x1=500, y1=500, x2=600, y2=600)

        distance = compute_centroid_distance(bbox1, bbox2)
        assert pytest.approx(distance, abs=0.1) == 707.1
