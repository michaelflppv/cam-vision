"""
Tracking module for multi-frame confirmation and deduplication.

This module provides simple IoU-based tracking to support multi-frame
confirmation requirements (PR8). Designed to work with existing stateless
processors while maintaining clean separation of concerns.
"""

from .iou import compute_centroid_distance, compute_iou
from .tracker import SimpleTracker
from .types import Track, TrackState

__all__ = [
    "Track",
    "TrackState",
    "SimpleTracker",
    "compute_iou",
    "compute_centroid_distance",
]
