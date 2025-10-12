"""Unit tests for UI formatting helpers."""

from __future__ import annotations

import time

from cam_vision.ui.formatting import (
    format_aspect_ratio,
    format_bbox_size,
    format_confidence_label,
    format_confirmation_progress,
    format_confirmation_status,
    format_event_summary,
    format_file_size,
    format_fps,
    format_list_badge,
    format_percentage,
    format_similarity_badge,
    format_time_ago,
    format_timestamp,
    truncate_text,
)


class TestSimilarityFormatting:
    """Test similarity score formatting functions."""

    def test_format_similarity_badge_high_confidence(self):
        """Test high confidence badge (similarity >= threshold + 0.15)."""
        emoji, color = format_similarity_badge(0.55, threshold=0.35)
        assert emoji == "🟢"
        assert color == "green"

    def test_format_similarity_badge_medium_confidence(self):
        """Test medium confidence badge (threshold <= similarity < threshold + 0.15)."""
        emoji, color = format_similarity_badge(0.40, threshold=0.35)
        assert emoji == "🟡"
        assert color == "amber"

    def test_format_similarity_badge_low_confidence(self):
        """Test low confidence badge (similarity < threshold)."""
        emoji, color = format_similarity_badge(0.30, threshold=0.35)
        assert emoji == "🔴"
        assert color == "red"

    def test_format_similarity_badge_custom_threshold(self):
        """Test custom threshold value."""
        emoji, color = format_similarity_badge(0.45, threshold=0.50)
        assert emoji == "🔴"
        assert color == "red"

    def test_format_confidence_label_high(self):
        """Test high confidence label."""
        label = format_confidence_label(0.55, threshold=0.35)
        assert label == "High Confidence"

    def test_format_confidence_label_medium(self):
        """Test medium confidence label."""
        label = format_confidence_label(0.40, threshold=0.35)
        assert label == "Medium Confidence"

    def test_format_confidence_label_low(self):
        """Test low confidence label."""
        label = format_confidence_label(0.30, threshold=0.35)
        assert label == "Low Confidence"


class TestListFormatting:
    """Test list match formatting functions."""

    def test_format_list_badge_whitelist(self):
        """Test whitelist badge."""
        emoji, label = format_list_badge("whitelist")
        assert emoji == "✅"
        assert label == "Whitelist"

    def test_format_list_badge_blacklist(self):
        """Test blacklist badge."""
        emoji, label = format_list_badge("blacklist")
        assert emoji == "🚫"
        assert label == "Blacklist"

    def test_format_list_badge_unknown(self):
        """Test unknown/no match badge."""
        emoji, label = format_list_badge(None)
        assert emoji == "○"
        assert label == "Unknown"

    def test_format_list_badge_empty_string(self):
        """Test empty string treated as unknown."""
        emoji, label = format_list_badge("")
        assert emoji == "○"
        assert label == "Unknown"


class TestConfirmationFormatting:
    """Test multi-frame confirmation formatting functions."""

    def test_format_confirmation_status(self):
        """Test confirmation status string."""
        status = format_confirmation_status(3, 5)
        assert status == "3/5 frames"

    def test_format_confirmation_status_complete(self):
        """Test confirmation status when complete."""
        status = format_confirmation_status(5, 5)
        assert status == "5/5 frames"

    def test_format_confirmation_progress_partial(self):
        """Test confirmation progress calculation."""
        progress = format_confirmation_progress(3, 5)
        assert progress == 0.6

    def test_format_confirmation_progress_complete(self):
        """Test confirmation progress when complete."""
        progress = format_confirmation_progress(5, 5)
        assert progress == 1.0

    def test_format_confirmation_progress_overflow(self):
        """Test confirmation progress capped at 1.0."""
        progress = format_confirmation_progress(7, 5)
        assert progress == 1.0

    def test_format_confirmation_progress_zero_required(self):
        """Test confirmation progress with zero required frames."""
        progress = format_confirmation_progress(3, 0)
        assert progress == 0.0


class TestTimestampFormatting:
    """Test timestamp formatting functions."""

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        # Use fixed timestamp: 2024-01-15 14:30:45 UTC
        ts_ms = 1705329045000
        formatted = format_timestamp(ts_ms)
        # Format should be YYYY-MM-DD HH:MM:SS
        assert len(formatted) == 19
        assert formatted.startswith("2024")
        # Time may vary by timezone, just check it has time component
        assert ":" in formatted

    def test_format_time_ago_seconds(self):
        """Test relative time formatting (seconds)."""
        current_ms = int(time.time() * 1000)
        ts_ms = current_ms - 30000  # 30 seconds ago
        result = format_time_ago(ts_ms)
        assert result == "30s ago"

    def test_format_time_ago_minutes(self):
        """Test relative time formatting (minutes)."""
        current_ms = int(time.time() * 1000)
        ts_ms = current_ms - 300000  # 5 minutes ago
        result = format_time_ago(ts_ms)
        assert result == "5m ago"

    def test_format_time_ago_hours(self):
        """Test relative time formatting (hours)."""
        current_ms = int(time.time() * 1000)
        ts_ms = current_ms - 7200000  # 2 hours ago
        result = format_time_ago(ts_ms)
        assert result == "2h ago"

    def test_format_time_ago_days(self):
        """Test relative time formatting (days)."""
        current_ms = int(time.time() * 1000)
        ts_ms = current_ms - 172800000  # 2 days ago
        result = format_time_ago(ts_ms)
        assert result == "2d ago"

    def test_format_time_ago_just_now(self):
        """Test relative time formatting for recent events."""
        current_ms = int(time.time() * 1000)
        ts_ms = current_ms - 5000  # 5 seconds ago
        result = format_time_ago(ts_ms)
        assert result == "5s ago"


class TestPercentageFormatting:
    """Test percentage formatting functions."""

    def test_format_percentage_ratio_input(self):
        """Test percentage formatting with ratio input (0.0-1.0)."""
        result = format_percentage(0.855, decimals=1)
        assert result == "85.5%"

    def test_format_percentage_percentage_input(self):
        """Test percentage formatting with percentage input (0-100)."""
        result = format_percentage(85.5, decimals=1)
        assert result == "85.5%"

    def test_format_percentage_zero_decimals(self):
        """Test percentage formatting with no decimals."""
        result = format_percentage(0.855, decimals=0)
        assert result == "86%"

    def test_format_percentage_two_decimals(self):
        """Test percentage formatting with two decimals."""
        result = format_percentage(0.85555, decimals=2)
        assert result == "85.56%"

    def test_format_percentage_boundary_case(self):
        """Test percentage at boundary (value = 1.0)."""
        # Value of exactly 1.0 should be treated as 100%
        result = format_percentage(1.0, decimals=1)
        assert result == "100.0%"


class TestTextFormatting:
    """Test text formatting functions."""

    def test_truncate_text_short(self):
        """Test truncate with text shorter than max_length."""
        result = truncate_text("Hello", max_length=10)
        assert result == "Hello"

    def test_truncate_text_exact(self):
        """Test truncate with text exactly at max_length."""
        result = truncate_text("Hello", max_length=5)
        assert result == "Hello"

    def test_truncate_text_long(self):
        """Test truncate with text longer than max_length."""
        result = truncate_text("Hello World", max_length=8)
        assert result == "Hello..."

    def test_truncate_text_custom_suffix(self):
        """Test truncate with custom suffix."""
        result = truncate_text("Hello World", max_length=8, suffix="…")
        assert result == "Hello W…"

    def test_truncate_text_very_short_limit(self):
        """Test truncate with very short limit."""
        result = truncate_text("Hello World", max_length=5)
        assert result == "He..."


class TestBboxFormatting:
    """Test bounding box formatting functions."""

    def test_format_bbox_size(self):
        """Test bbox size formatting."""
        result = format_bbox_size(640, 480)
        assert result == "640×480 px"

    def test_format_bbox_size_square(self):
        """Test bbox size for square."""
        result = format_bbox_size(512, 512)
        assert result == "512×512 px"

    def test_format_aspect_ratio_4_3(self):
        """Test aspect ratio detection for 4:3."""
        result = format_aspect_ratio(640, 480)
        assert result == "4:3"

    def test_format_aspect_ratio_16_9(self):
        """Test aspect ratio detection for 16:9."""
        result = format_aspect_ratio(1920, 1080)
        assert result == "16:9"

    def test_format_aspect_ratio_21_9(self):
        """Test aspect ratio detection for 21:9."""
        result = format_aspect_ratio(2560, 1080)
        assert result == "21:9"

    def test_format_aspect_ratio_custom(self):
        """Test aspect ratio for custom ratio."""
        result = format_aspect_ratio(1024, 768)
        # Should be close to 4:3 but slightly off
        assert result == "4:3"

    def test_format_aspect_ratio_unusual(self):
        """Test aspect ratio for unusual ratio."""
        # 1000/800 = 1.25, which is close to 4:3 (1.333) within tolerance
        result = format_aspect_ratio(1000, 800)
        # Should be detected as 4:3 since abs(1.25 - 1.333) < 0.1
        assert result == "4:3"

    def test_format_aspect_ratio_zero_height(self):
        """Test aspect ratio with zero height."""
        result = format_aspect_ratio(1920, 0)
        assert result == "N/A"


class TestMetricFormatting:
    """Test metric formatting functions."""

    def test_format_fps_default_decimals(self):
        """Test FPS formatting with default decimals."""
        result = format_fps(15.3)
        assert result == "15.3 FPS"

    def test_format_fps_zero_decimals(self):
        """Test FPS formatting with zero decimals."""
        result = format_fps(15.7, decimals=0)
        assert result == "16 FPS"

    def test_format_fps_two_decimals(self):
        """Test FPS formatting with two decimals."""
        result = format_fps(15.375, decimals=2)
        assert result == "15.38 FPS"

    def test_format_file_size_bytes(self):
        """Test file size formatting (bytes)."""
        result = format_file_size(512)
        assert result == "512.0 B"

    def test_format_file_size_kilobytes(self):
        """Test file size formatting (kilobytes)."""
        result = format_file_size(1536)  # 1.5 KB
        assert result == "1.5 KB"

    def test_format_file_size_megabytes(self):
        """Test file size formatting (megabytes)."""
        result = format_file_size(1572864)  # 1.5 MB
        assert result == "1.5 MB"

    def test_format_file_size_gigabytes(self):
        """Test file size formatting (gigabytes)."""
        result = format_file_size(1610612736)  # 1.5 GB
        assert result == "1.5 GB"

    def test_format_file_size_zero(self):
        """Test file size formatting for zero bytes."""
        result = format_file_size(0)
        assert result == "0.0 B"


class TestEventSummary:
    """Test event summary formatting functions."""

    def test_format_event_summary_face_match(self):
        """Test face match event summary."""
        payload = {
            "person_id": "john_doe",
            "similarity": 0.87,
        }
        result = format_event_summary("face_match", payload)
        assert result == "Face: john_doe (0.87)"

    def test_format_event_summary_face_match_unknown(self):
        """Test face match event summary with missing person_id."""
        payload = {
            "similarity": 0.87,
        }
        result = format_event_summary("face_match", payload)
        assert result == "Face: Unknown (0.87)"

    def test_format_event_summary_plate_read_whitelist(self):
        """Test plate read event summary with whitelist match."""
        payload = {
            "text_clean": "ABC123",
            "matched_list": "whitelist",
        }
        result = format_event_summary("plate_read", payload)
        assert result == "Plate: ABC123 [whitelist]"

    def test_format_event_summary_plate_read_blacklist(self):
        """Test plate read event summary with blacklist match."""
        payload = {
            "text_clean": "XYZ789",
            "matched_list": "blacklist",
        }
        result = format_event_summary("plate_read", payload)
        assert result == "Plate: XYZ789 [blacklist]"

    def test_format_event_summary_plate_read_unknown(self):
        """Test plate read event summary with no list match."""
        payload = {
            "text_clean": "ABC123",
            "matched_list": None,
        }
        result = format_event_summary("plate_read", payload)
        assert result == "Plate: ABC123"

    def test_format_event_summary_plate_read_missing_text(self):
        """Test plate read event summary with missing text_clean."""
        payload = {
            "matched_list": "whitelist",
        }
        result = format_event_summary("plate_read", payload)
        # Even with missing text, list match is included
        assert result == "Plate: ??? [whitelist]"

    def test_format_event_summary_unknown_type(self):
        """Test event summary with unknown event type."""
        payload = {}
        result = format_event_summary("unknown_event", payload)
        assert result == "Unknown event type: unknown_event"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_format_similarity_badge_exact_threshold(self):
        """Test similarity exactly at threshold boundary."""
        emoji, color = format_similarity_badge(0.35, threshold=0.35)
        assert emoji == "🟡"  # Should be medium confidence

    def test_format_similarity_badge_exact_high_boundary(self):
        """Test similarity exactly at high confidence boundary."""
        emoji, color = format_similarity_badge(0.50, threshold=0.35)
        assert emoji == "🟢"  # 0.35 + 0.15 = 0.50

    def test_format_percentage_zero(self):
        """Test percentage formatting with zero."""
        result = format_percentage(0.0, decimals=1)
        assert result == "0.0%"

    def test_format_percentage_over_100(self):
        """Test percentage formatting with value over 100."""
        result = format_percentage(150.0, decimals=1)
        assert result == "150.0%"

    def test_truncate_text_empty(self):
        """Test truncate with empty string."""
        result = truncate_text("", max_length=10)
        assert result == ""

    def test_format_bbox_size_zero(self):
        """Test bbox size with zero dimensions."""
        result = format_bbox_size(0, 0)
        assert result == "0×0 px"

    def test_format_file_size_large(self):
        """Test file size formatting for very large file."""
        result = format_file_size(1099511627776)  # 1 TB
        assert result == "1.0 TB"

    def test_format_confirmation_progress_negative(self):
        """Test confirmation progress doesn't go negative."""
        # Even with weird inputs, progress should be 0.0-1.0
        progress = format_confirmation_progress(0, 5)
        assert progress == 0.0
