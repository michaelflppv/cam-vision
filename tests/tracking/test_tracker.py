"""Tests for SimpleTracker."""

import pytest

from cam_vision.tracking.tracker import SimpleTracker
from cam_vision.tracking.types import TrackState
from cam_vision.types import BBox, Detection


@pytest.fixture
def face_tracker():
    """Create face tracker with default settings."""
    return SimpleTracker(
        detection_kind="face",
        iou_threshold=0.5,
        frames_required=3,
        max_age=5,
    )


@pytest.fixture
def plate_tracker():
    """Create plate tracker with default settings."""
    return SimpleTracker(
        detection_kind="plate",
        iou_threshold=0.5,
        frames_required=3,
        max_age=5,
        ocr_agreement_threshold=0.6,
    )


class TestSimpleTrackerBasics:
    """Basic tracker functionality tests."""

    def test_initialization(self, face_tracker):
        """Test tracker initializes correctly."""
        assert face_tracker.detection_kind == "face"
        assert face_tracker.iou_threshold == 0.5
        assert face_tracker.frames_required == 3
        assert face_tracker.max_age == 5
        assert len(face_tracker.tracks) == 0

    def test_single_detection_creates_track(self, face_tracker):
        """Test that a single detection creates a new track."""
        detection = Detection(
            kind="face",
            bbox=BBox(x1=100, y1=100, x2=200, y2=200),
            score=0.9,
        )

        face_tracker.update([detection], ts_ms=1000)

        assert len(face_tracker.tracks) == 1
        track = face_tracker.tracks[0]
        assert track.track_id == 1
        assert track.state == TrackState.TENTATIVE
        assert track.consecutive_hits == 1
        assert track.first_seen_ts == 1000

    def test_no_detections_keeps_tracks(self, face_tracker):
        """Test that empty frame doesn't remove tracks immediately."""
        detection = Detection(
            kind="face",
            bbox=BBox(x1=100, y1=100, x2=200, y2=200),
            score=0.9,
        )

        face_tracker.update([detection], ts_ms=1000)
        assert len(face_tracker.tracks) == 1

        # Empty frame
        face_tracker.update([], ts_ms=1100)

        # Track should still exist but marked as missed
        assert len(face_tracker.tracks) == 1
        track = face_tracker.tracks[0]
        assert track.consecutive_misses == 1
        assert track.consecutive_hits == 0

    def test_multiple_detections_create_multiple_tracks(self, face_tracker):
        """Test multiple detections create separate tracks."""
        detections = [
            Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9),
            Detection(kind="face", bbox=BBox(x1=300, y1=300, x2=400, y2=400), score=0.8),
        ]

        face_tracker.update(detections, ts_ms=1000)

        assert len(face_tracker.tracks) == 2
        assert face_tracker.tracks[0].track_id == 1
        assert face_tracker.tracks[1].track_id == 2


class TestTrackMatching:
    """Test detection-to-track matching logic."""

    def test_high_iou_detection_matches_existing_track(self, face_tracker):
        """Test detection with high IoU matches existing track."""
        # Frame 1: Create track
        det1 = Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9)
        face_tracker.update([det1], ts_ms=1000)

        track_id = face_tracker.tracks[0].track_id

        # Frame 2: Similar detection (should match)
        det2 = Detection(kind="face", bbox=BBox(x1=105, y1=105, x2=205, y2=205), score=0.9)
        face_tracker.update([det2], ts_ms=1100)

        # Should still be only one track
        assert len(face_tracker.tracks) == 1
        assert face_tracker.tracks[0].track_id == track_id
        assert face_tracker.tracks[0].consecutive_hits == 2

    def test_low_iou_detection_creates_new_track(self, face_tracker):
        """Test detection with low IoU creates new track."""
        # Frame 1: Create track
        det1 = Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9)
        face_tracker.update([det1], ts_ms=1000)

        # Frame 2: Far away detection (should not match)
        det2 = Detection(kind="face", bbox=BBox(x1=500, y1=500, x2=600, y2=600), score=0.9)
        face_tracker.update([det2], ts_ms=1100)

        # Should have two tracks
        assert len(face_tracker.tracks) == 2

    def test_greedy_matching_prefers_best_iou(self, face_tracker):
        """Test greedy matching assigns detection to best IoU track."""
        # Frame 1: Create two tracks
        det1 = Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9)
        det2 = Detection(kind="face", bbox=BBox(x1=300, y1=300, x2=400, y2=400), score=0.9)
        face_tracker.update([det1, det2], ts_ms=1000)

        # Frame 2: One detection closer to track 2
        det3 = Detection(kind="face", bbox=BBox(x1=305, y1=305, x2=405, y2=405), score=0.9)
        face_tracker.update([det3], ts_ms=1100)

        # Track 2 should have 2 hits, track 1 should have 1 miss
        track1 = [t for t in face_tracker.tracks if t.track_id == 1][0]
        track2 = [t for t in face_tracker.tracks if t.track_id == 2][0]

        assert track1.consecutive_misses == 1
        assert track2.consecutive_hits == 2


class TestTrackLifecycle:
    """Test track state transitions."""

    def test_track_confirmed_after_k_frames(self, face_tracker):
        """Test track is confirmed after K consecutive hits."""
        bbox = BBox(x1=100, y1=100, x2=200, y2=200)

        # Frame 1: TENTATIVE (1 hit)
        face_tracker.update([Detection(kind="face", bbox=bbox, score=0.9)], ts_ms=1000)
        assert face_tracker.tracks[0].state == TrackState.TENTATIVE
        assert face_tracker.tracks[0].consecutive_hits == 1

        # Frame 2: TENTATIVE (2 hits)
        face_tracker.update([Detection(kind="face", bbox=bbox, score=0.9)], ts_ms=1100)
        assert face_tracker.tracks[0].state == TrackState.TENTATIVE
        assert face_tracker.tracks[0].consecutive_hits == 2

        # Frame 3: CONFIRMED (3 hits)
        face_tracker.update([Detection(kind="face", bbox=bbox, score=0.9)], ts_ms=1200)
        assert face_tracker.tracks[0].state == TrackState.CONFIRMED
        assert face_tracker.tracks[0].consecutive_hits == 3

    def test_track_lost_after_max_age(self, face_tracker):
        """Test track is marked LOST after max_age frames without match."""
        # Frame 1: Create track
        det = Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9)
        face_tracker.update([det], ts_ms=1000)

        # Frames 2-6: No detections (5 misses = max_age)
        for i in range(5):
            face_tracker.update([], ts_ms=1100 + i * 100)

        # Track should be marked LOST and removed
        assert len(face_tracker.tracks) == 0

    def test_confirmed_track_stays_confirmed_with_continued_matches(self, face_tracker):
        """Test confirmed track stays confirmed with continued matches."""
        bbox = BBox(x1=100, y1=100, x2=200, y2=200)

        # Confirm track (3 frames)
        for i in range(3):
            face_tracker.update(
                [Detection(kind="face", bbox=bbox, score=0.9)], ts_ms=1000 + i * 100
            )

        assert face_tracker.tracks[0].state == TrackState.CONFIRMED

        # Continue matching (5 more frames)
        for i in range(5):
            face_tracker.update(
                [Detection(kind="face", bbox=bbox, score=0.9)], ts_ms=1300 + i * 100
            )

        # Should still be confirmed
        assert face_tracker.tracks[0].state == TrackState.CONFIRMED
        assert face_tracker.tracks[0].consecutive_hits == 8

    def test_miss_resets_consecutive_hits(self, face_tracker):
        """Test that a miss resets consecutive hits."""
        bbox = BBox(x1=100, y1=100, x2=200, y2=200)

        # Frame 1-2: Hit, hit
        face_tracker.update([Detection(kind="face", bbox=bbox, score=0.9)], ts_ms=1000)
        face_tracker.update([Detection(kind="face", bbox=bbox, score=0.9)], ts_ms=1100)

        assert face_tracker.tracks[0].consecutive_hits == 2

        # Frame 3: Miss
        face_tracker.update([], ts_ms=1200)

        assert face_tracker.tracks[0].consecutive_hits == 0
        assert face_tracker.tracks[0].consecutive_misses == 1

        # Frame 4: Hit again (should restart count)
        face_tracker.update([Detection(kind="face", bbox=bbox, score=0.9)], ts_ms=1300)

        assert face_tracker.tracks[0].consecutive_hits == 1
        assert face_tracker.tracks[0].consecutive_misses == 0


class TestPlateTracking:
    """Test plate-specific tracking with OCR agreement."""

    def test_plate_track_requires_ocr_agreement(self, plate_tracker):
        """Test plate track requires OCR text agreement for confirmation."""
        bbox = BBox(x1=100, y1=100, x2=200, y2=200)

        # Frame 1-3: Same bbox, same text
        for i in range(3):
            detections = [Detection(kind="plate", bbox=bbox, score=0.9)]
            ocr_texts = [("ABC123", 85.0)]
            plate_tracker.update(detections, ts_ms=1000 + i * 100, ocr_texts=ocr_texts)

        # Should be confirmed (3 hits + OCR agreement)
        assert plate_tracker.tracks[0].state == TrackState.CONFIRMED
        assert plate_tracker.tracks[0].get_majority_ocr_text() == "ABC123"

    def test_plate_track_not_confirmed_without_ocr_agreement(self, plate_tracker):
        """Test plate track is not confirmed without OCR agreement."""
        bbox = BBox(x1=100, y1=100, x2=200, y2=200)

        # Frame 1-3: Same bbox, different text each time
        texts = ["ABC123", "XYZ789", "DEF456"]
        for i, text in enumerate(texts):
            detections = [Detection(kind="plate", bbox=bbox, score=0.9)]
            ocr_texts = [(text, 85.0)]
            plate_tracker.update(detections, ts_ms=1000 + i * 100, ocr_texts=ocr_texts)

        # Should NOT be confirmed (no OCR agreement)
        assert plate_tracker.tracks[0].state == TrackState.TENTATIVE
        assert plate_tracker.tracks[0].consecutive_hits == 3
        # No majority text (need 60% agreement)
        assert plate_tracker.tracks[0].get_majority_ocr_text() is None

    def test_plate_track_confirmed_with_majority_ocr_text(self, plate_tracker):
        """Test plate track confirmed with majority OCR text."""
        bbox = BBox(x1=100, y1=100, x2=200, y2=200)

        # Frame 1-5: 4 times "ABC123", 1 time "ABC124" (OCR error)
        texts = ["ABC123", "ABC123", "ABC124", "ABC123", "ABC123"]
        for i, text in enumerate(texts):
            detections = [Detection(kind="plate", bbox=bbox, score=0.9)]
            ocr_texts = [(text, 85.0)]
            plate_tracker.update(detections, ts_ms=1000 + i * 100, ocr_texts=ocr_texts)

        # Should be confirmed (5 hits + 80% agreement on "ABC123")
        assert plate_tracker.tracks[0].state == TrackState.CONFIRMED
        assert plate_tracker.tracks[0].get_majority_ocr_text() == "ABC123"

    def test_plate_ocr_text_history_limited(self, plate_tracker):
        """Test OCR text history is limited to prevent unbounded growth."""
        bbox = BBox(x1=100, y1=100, x2=200, y2=200)

        # Add 15 detections with same text
        for i in range(15):
            detections = [Detection(kind="plate", bbox=bbox, score=0.9)]
            ocr_texts = [("ABC123", 85.0)]
            plate_tracker.update(detections, ts_ms=1000 + i * 100, ocr_texts=ocr_texts)

        # OCR history should be limited to max_history (default 10)
        track = plate_tracker.tracks[0]
        assert len(track.ocr_text_history) == 10


class TestTrackerStats:
    """Test tracker statistics tracking."""

    def test_stats_track_creation(self, face_tracker):
        """Test stats correctly track track creation."""
        det1 = Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9)
        det2 = Detection(kind="face", bbox=BBox(x1=300, y1=300, x2=400, y2=400), score=0.9)

        face_tracker.update([det1, det2], ts_ms=1000)

        stats = face_tracker.get_stats()
        assert stats["total_detections"] == 2
        assert stats["tracks_created"] == 2
        assert stats["active_tracks"] == 2

    def test_stats_track_confirmation(self, face_tracker):
        """Test stats correctly track track confirmation."""
        bbox = BBox(x1=100, y1=100, x2=200, y2=200)

        # Confirm track (3 frames)
        for i in range(3):
            face_tracker.update(
                [Detection(kind="face", bbox=bbox, score=0.9)], ts_ms=1000 + i * 100
            )

        stats = face_tracker.get_stats()
        assert stats["tracks_confirmed"] == 1
        assert stats["confirmed_tracks"] == 1
        assert stats["tentative_tracks"] == 0

    def test_stats_track_loss(self, face_tracker):
        """Test stats correctly track track loss."""
        det = Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9)
        face_tracker.update([det], ts_ms=1000)

        # Age out track (5 misses)
        for i in range(5):
            face_tracker.update([], ts_ms=1100 + i * 100)

        stats = face_tracker.get_stats()
        assert stats["tracks_lost"] == 1
        assert stats["active_tracks"] == 0

    def test_reset_clears_stats(self, face_tracker):
        """Test reset clears all stats."""
        det = Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9)
        face_tracker.update([det], ts_ms=1000)

        face_tracker.reset()

        stats = face_tracker.get_stats()
        assert stats["total_detections"] == 0
        assert stats["tracks_created"] == 0
        assert len(face_tracker.tracks) == 0


class TestTrackerEdgeCases:
    """Test edge cases and error handling."""

    def test_ocr_texts_length_mismatch_raises_error(self, plate_tracker):
        """Test mismatched OCR texts length raises ValueError."""
        detections = [
            Detection(kind="plate", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9),
            Detection(kind="plate", bbox=BBox(x1=300, y1=300, x2=400, y2=400), score=0.9),
        ]
        ocr_texts = [("ABC123", 85.0)]  # Only 1 text for 2 detections

        with pytest.raises(ValueError, match="ocr_texts length.*must match"):
            plate_tracker.update(detections, ts_ms=1000, ocr_texts=ocr_texts)

    def test_get_track_by_id_returns_correct_track(self, face_tracker):
        """Test get_track_by_id returns correct track."""
        det1 = Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9)
        det2 = Detection(kind="face", bbox=BBox(x1=300, y1=300, x2=400, y2=400), score=0.9)

        face_tracker.update([det1, det2], ts_ms=1000)

        track = face_tracker.get_track_by_id(2)
        assert track is not None
        assert track.track_id == 2

    def test_get_track_by_id_returns_none_for_invalid_id(self, face_tracker):
        """Test get_track_by_id returns None for invalid ID."""
        det = Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9)
        face_tracker.update([det], ts_ms=1000)

        track = face_tracker.get_track_by_id(999)
        assert track is None

    def test_get_confirmed_tracks_filters_correctly(self, face_tracker):
        """Test get_confirmed_tracks only returns confirmed tracks."""
        # Create two tracks
        det1 = Detection(kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.9)
        det2 = Detection(kind="face", bbox=BBox(x1=300, y1=300, x2=400, y2=400), score=0.9)
        face_tracker.update([det1, det2], ts_ms=1000)

        # Confirm only track 1 (3 frames)
        for i in range(2):
            face_tracker.update([det1, det2], ts_ms=1100 + i * 100)

        confirmed = face_tracker.get_confirmed_tracks()
        assert len(confirmed) == 2  # Both confirmed after 3 frames
        assert all(t.state == TrackState.CONFIRMED for t in confirmed)
