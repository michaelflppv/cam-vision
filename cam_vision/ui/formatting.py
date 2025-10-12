"""Formatting helpers for UI components."""

from __future__ import annotations

from typing import Literal, Optional


def format_similarity_badge(similarity: float, threshold: float = 0.35) -> tuple[str, str]:
    """
    Format similarity score as badge with color.

    Args:
        similarity: Similarity score (0.0-1.0)
        threshold: Threshold for matching

    Returns:
        Tuple of (emoji, color) for display
    """
    if similarity >= threshold + 0.15:
        return ("🟢", "green")  # High confidence
    elif similarity >= threshold:
        return ("🟡", "amber")  # Medium confidence
    else:
        return ("🔴", "red")  # Low confidence


def format_confidence_label(similarity: float, threshold: float = 0.35) -> str:
    """
    Format confidence label for similarity score.

    Args:
        similarity: Similarity score (0.0-1.0)
        threshold: Threshold for matching

    Returns:
        Human-readable confidence label
    """
    if similarity >= threshold + 0.15:
        return "High Confidence"
    elif similarity >= threshold:
        return "Medium Confidence"
    else:
        return "Low Confidence"


def format_list_badge(matched_list: Optional[Literal["whitelist", "blacklist"]]) -> tuple[str, str]:
    """
    Format list match as badge with color.

    Args:
        matched_list: List type or None

    Returns:
        Tuple of (emoji, label) for display
    """
    if matched_list == "whitelist":
        return ("✅", "Whitelist")
    elif matched_list == "blacklist":
        return ("🚫", "Blacklist")
    else:
        return ("○", "Unknown")


def format_confirmation_status(confirmed: int, required: int) -> str:
    """
    Format multi-frame confirmation status.

    Args:
        confirmed: Number of frames confirmed
        required: Number of frames required

    Returns:
        Formatted string like "3/5 frames"
    """
    return f"{confirmed}/{required} frames"


def format_confirmation_progress(confirmed: int, required: int) -> float:
    """
    Format multi-frame confirmation as progress value.

    Args:
        confirmed: Number of frames confirmed
        required: Number of frames required

    Returns:
        Progress value (0.0-1.0)
    """
    if required == 0:
        return 0.0
    return min(1.0, confirmed / required)


def format_timestamp(ts_ms: int) -> str:
    """
    Format timestamp as human-readable string.

    Args:
        ts_ms: Timestamp in milliseconds

    Returns:
        Formatted string like "2024-11-15 14:30:45"
    """
    from datetime import datetime

    dt = datetime.fromtimestamp(ts_ms / 1000.0)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_time_ago(ts_ms: int) -> str:
    """
    Format timestamp as relative time.

    Args:
        ts_ms: Timestamp in milliseconds

    Returns:
        Formatted string like "2 minutes ago"
    """
    import time

    current_ms = int(time.time() * 1000)
    diff_seconds = (current_ms - ts_ms) / 1000.0

    if diff_seconds < 60:
        return f"{int(diff_seconds)}s ago"
    elif diff_seconds < 3600:
        return f"{int(diff_seconds / 60)}m ago"
    elif diff_seconds < 86400:
        return f"{int(diff_seconds / 3600)}h ago"
    else:
        return f"{int(diff_seconds / 86400)}d ago"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format float as percentage string.

    Args:
        value: Value (0.0-1.0 or 0-100)
        decimals: Number of decimal places

    Returns:
        Formatted string like "85.5%"
    """
    # Auto-detect if value is already in percentage (0-100) or ratio (0-1)
    if value > 1.0:
        # Already percentage
        return f"{value:.{decimals}f}%"
    else:
        # Convert ratio to percentage
        return f"{value * 100:.{decimals}f}%"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to append when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    truncate_at = max_length - len(suffix)
    return text[:truncate_at] + suffix


def format_bbox_size(width: int, height: int) -> str:
    """
    Format bounding box size.

    Args:
        width: Box width in pixels
        height: Box height in pixels

    Returns:
        Formatted string like "320×240 px"
    """
    return f"{width}×{height} px"


def format_aspect_ratio(width: int, height: int) -> str:
    """
    Format aspect ratio.

    Args:
        width: Width in pixels
        height: Height in pixels

    Returns:
        Formatted string like "4:3" or "16:9"
    """
    if height == 0:
        return "N/A"

    ratio = width / height

    # Common aspect ratios
    if abs(ratio - 4 / 3) < 0.1:
        return "4:3"
    elif abs(ratio - 16 / 9) < 0.1:
        return "16:9"
    elif abs(ratio - 21 / 9) < 0.1:
        return "21:9"
    else:
        return f"{ratio:.2f}:1"


def format_fps(fps: float, decimals: int = 1) -> str:
    """
    Format FPS value.

    Args:
        fps: Frames per second
        decimals: Number of decimal places

    Returns:
        Formatted string like "15.3 FPS"
    """
    return f"{fps:.{decimals}f} FPS"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string like "1.5 MB"
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"


def format_event_summary(event_type: str, payload: dict) -> str:
    """
    Format event as one-line summary.

    Args:
        event_type: Type of event (face_match or plate_read)
        payload: Event payload dict

    Returns:
        One-line summary string
    """
    if event_type == "face_match":
        person_id = payload.get("person_id", "Unknown")
        similarity = payload.get("similarity", 0.0)
        return f"Face: {person_id} ({similarity:.2f})"
    elif event_type == "plate_read":
        text_clean = payload.get("text_clean", "???")
        matched_list = payload.get("matched_list")
        list_str = f" [{matched_list}]" if matched_list else ""
        return f"Plate: {text_clean}{list_str}"
    else:
        return f"Unknown event type: {event_type}"
