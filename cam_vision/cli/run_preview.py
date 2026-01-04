#!/usr/bin/env python3
"""Launch a lightweight SecureVision preview window without the desktop UI."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from typing import Tuple

import cv2
from pydantic import ValidationError

from ..config import VideoSource
from ..ui.capture import CaptureManager

logger = logging.getLogger(__name__)


def _resolution(value: str) -> Tuple[int, int]:
    """Parse WIDTHxHEIGHT strings from CLI arguments."""
    try:
        width_str, height_str = value.lower().split("x", 1)
        width = int(width_str)
        height = int(height_str)
    except (ValueError, AttributeError) as exc:
        raise argparse.ArgumentTypeError(
            "Resolution must be WIDTHxHEIGHT (e.g., 1280x720)"
        ) from exc

    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("Resolution values must be positive integers")

    return width, height


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Start SecureVision capture with face and plate overlays in an OpenCV preview window. "
            "Press 'q' or Ctrl+C to exit."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Built-in webcam with preview and tracking
  securevision-preview --source-type device --device 0 --backend AVFOUNDATION

  # RTSP camera at 10 FPS with resize
  securevision-preview --source-type rtsp --url rtsp://camera/stream --fps 10 --resize 1280x720

  # Disable plate detection for faster preview
  securevision-preview --source-type device --no-plates
        """,
    )

    parser.add_argument(
        "--source-type",
        required=True,
        choices=["device", "rtsp", "http_mjpeg", "file", "rtmp"],
        help="Video source type.",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=0,
        help="Device index when using --source-type device (default: 0).",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="URL or file path for network/file sources (rtsp/http_mjpeg/file/rtmp).",
    )
    parser.add_argument(
        "--backend",
        type=str,
        help="Optional OpenCV backend hint (e.g., AVFOUNDATION on macOS).",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=15,
        help="Target capture FPS (frames may be dropped to maintain this rate).",
    )
    parser.add_argument(
        "--resize",
        type=_resolution,
        help="Resize frames before processing (WIDTHxHEIGHT, e.g., 1280x720).",
    )
    parser.add_argument(
        "--face-threshold",
        type=float,
        help="Override face similarity threshold (0.0-1.0).",
    )
    parser.add_argument(
        "--no-faces",
        action="store_true",
        help="Disable face recognition overlays.",
    )
    parser.add_argument(
        "--no-plates",
        action="store_true",
        help="Disable license plate recognition overlays.",
    )
    parser.add_argument(
        "--disable-tracking",
        action="store_true",
        help="Disable multi-frame tracking/confirmation pipeline.",
    )
    parser.add_argument(
        "--tracking-frames",
        type=int,
        help="Override frames required for confirmation (default from config).",
    )
    parser.add_argument(
        "--tracking-iou",
        type=float,
        help="Override IoU threshold for track association (0.0-1.0).",
    )
    parser.add_argument(
        "--tracking-max-age",
        type=int,
        help="Override max age for tracks in frames.",
    )
    parser.add_argument(
        "--ocr-agreement",
        type=float,
        help="Override OCR agreement threshold for plate confirmation (0.0-1.0).",
    )
    parser.add_argument(
        "--window-title",
        type=str,
        default="SecureVision Preview",
        help="Title for the OpenCV preview window.",
    )
    parser.add_argument(
        "--stats-interval",
        type=float,
        default=5.0,
        help="Seconds between console stats updates (set to 0 to disable).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )

    args = parser.parse_args()

    # Validate argument combinations
    if args.source_type == "device":
        if args.url:
            parser.error("--url is not used with --source-type device")
    else:
        if not args.url:
            parser.error(f"--url is required for --source-type {args.source_type}")

    if args.fps <= 0:
        parser.error("--fps must be a positive integer")

    if args.face_threshold is not None and not 0.0 < args.face_threshold <= 1.0:
        parser.error("--face-threshold must be between 0.0 and 1.0")

    if args.tracking_iou is not None and not 0.0 <= args.tracking_iou <= 1.0:
        parser.error("--tracking-iou must be between 0.0 and 1.0")

    if args.ocr_agreement is not None and not 0.0 <= args.ocr_agreement <= 1.0:
        parser.error("--ocr-agreement must be between 0.0 and 1.0")

    if args.stats_interval < 0:
        parser.error("--stats-interval must be zero or a positive number")

    return args


class PreviewRunner:
    """Manage preview loop and keyboard interaction."""

    def __init__(
        self,
        manager: CaptureManager,
        window_title: str,
        stats_interval: float,
    ):
        self.manager = manager
        self.window_title = window_title
        self.stats_interval = stats_interval
        self.running = False
        self._last_stats_at = 0.0
        self._latest_frame = None

        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, _sig, _frame):
        """Handle Ctrl+C gracefully."""
        print("\nStopping preview...")
        self.running = False

    def run(self) -> int:
        """Display annotated preview until user exits."""
        self.running = True
        self._last_stats_at = time.time()

        try:
            cv2.namedWindow(self.window_title, cv2.WINDOW_NORMAL)
        except cv2.error as exc:
            logger.error("Unable to create preview window: %s", exc)
            return 1

        print("SecureVision preview running.")
        print("Press 'q' inside the window or use Ctrl+C to exit.\n")

        exit_code = 0

        try:
            while self.running:
                frame_result = self.manager.get_latest_frame()
                if frame_result:
                    self._latest_frame = frame_result

                if self._latest_frame:
                    preview_image = self._latest_frame.preview_image.copy()
                    stats = self.manager.get_stats()
                    self._draw_overlay(preview_image, stats, self._latest_frame)
                    cv2.imshow(self.window_title, preview_image)

                    if self.stats_interval > 0:
                        now = time.time()
                        if now - self._last_stats_at >= self.stats_interval:
                            self._print_console_stats(stats, self._latest_frame)
                            self._last_stats_at = now

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    print("\nUser pressed 'q' - exiting preview.")
                    break

                if frame_result is None:
                    time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nPreview interrupted by user.")
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Preview encountered an error: %s", exc, exc_info=True)
            exit_code = 1
        finally:
            cv2.destroyWindow(self.window_title)

        return exit_code

    def _draw_overlay(self, image, stats: dict, frame_result) -> None:
        """Render status text overlays similar to the desktop dashboard."""
        known_faces = sum(1 for obs in frame_result.face_observations if obs.matched)
        total_faces = len(frame_result.face_observations)
        unknown_faces = total_faces - known_faces
        plate_observations = frame_result.plate_observations
        plate_read = sum(1 for obs in plate_observations if obs.status == "read")
        plate_pending = sum(
            1 for obs in plate_observations if obs.status != "read" and obs.is_displayable()
        )

        init_status = self.manager.get_init_status()
        face_status = self._format_feature_status(
            enabled=init_status["faces_enabled"],
            error=init_status["face_error"],
            extra=(
                f"{init_status['gallery_persons']} enrolled"
                if init_status["faces_enabled"] and init_status["gallery_persons"] > 0
                else ""
            ),
        )
        plate_status = self._format_feature_status(
            enabled=init_status["plates_enabled"],
            error=init_status["plate_error"],
        )

        lines = [
            f"FPS: {stats['fps']:.1f}",
            f"Frames: {stats['frame_count']}",
            f"Faces ({face_status}): {known_faces} known / {unknown_faces} unknown",
            f"Plates ({plate_status}): {plate_read} read / {plate_pending} pending",
            "Press 'q' to exit",
        ]

        y = 28
        for line in lines:
            cv2.putText(
                image,
                line,
                (12, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                3,
                cv2.LINE_AA,
            )
            cv2.putText(
                image,
                line,
                (12, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            y += 26

    def _print_console_stats(self, stats: dict, frame_result) -> None:
        """Print periodic stats to the console."""
        known_faces = sum(1 for obs in frame_result.face_observations if obs.matched)
        unknown_faces = len(frame_result.face_observations) - known_faces
        plate_observations = frame_result.plate_observations
        plate_read = sum(1 for obs in plate_observations if obs.status == "read")
        plate_pending = sum(
            1 for obs in plate_observations if obs.status != "read" and obs.is_displayable()
        )

        logger.info(
            "Frames=%d | FPS=%.1f | Faces: %d known / %d unknown | Plates: %d read / %d pending",
            stats["frame_count"],
            stats["fps"],
            known_faces,
            unknown_faces,
            plate_read,
            plate_pending,
        )

        if frame_result.face_matches:
            for match in frame_result.face_matches:
                logger.info(
                    "  Face match: %s (similarity=%.3f, score=%.3f)",
                    match.person_id,
                    match.similarity,
                    match.detection.score,
                )

        if frame_result.plate_reads:
            for plate in frame_result.plate_reads:
                logger.info(
                    "  Plate read: %s (confidence=%.2f, score=%.3f)",
                    plate.text_clean,
                    plate.confidence,
                    plate.detection.score,
                )

        pending = [
            obs for obs in plate_observations if obs.status != "read" and obs.is_displayable()
        ]
        if pending:
            for obs in pending:
                logger.info(
                    "  Pending plate: %s status=%s (confidence=%.2f%%)%s",
                    obs.label,
                    obs.status,
                    obs.confidence,
                    f" reason={obs.reason}" if obs.reason else "",
                )

    @staticmethod
    def _format_feature_status(enabled: bool, error: str | None, extra: str = "") -> str:
        """Return human readable feature status string."""
        if error:
            return "error"
        if not enabled:
            return "off"
        return f"on{f' ({extra})' if extra else ''}"


def build_source_config(args: argparse.Namespace):
    """Construct a concrete source config from CLI arguments."""
    video_source = VideoSource(type=args.source_type)

    if args.source_type == "device":
        video_source.device_index = args.device
        video_source.backend = args.backend
    else:
        video_source.url = args.url

    return video_source


def main() -> int:
    """Entry point for securevision-preview CLI."""
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        source = build_source_config(args)
        source_config = source.to_concrete()
    except ValidationError as exc:
        logger.error("Invalid video source configuration: %s", exc)
        return 1

    manager = CaptureManager(
        enable_faces=not args.no_faces,
        enable_plates=not args.no_plates,
        enable_tracking=not args.disable_tracking,
    )

    try:
        manager.start(
            source_config=source_config,
            fps_target=args.fps,
            frame_resize=args.resize,
            face_similarity_threshold=args.face_threshold,
            tracking_enabled=not args.disable_tracking,
            frames_required=args.tracking_frames,
            iou_threshold=args.tracking_iou,
            max_age_frames=args.tracking_max_age,
            ocr_agreement_threshold=args.ocr_agreement,
        )
    except Exception as exc:
        logger.error("Failed to start capture: %s", exc, exc_info=True)
        manager.stop()
        return 1

    init_status = manager.get_init_status()
    if init_status["face_error"]:
        logger.warning("Face recognition disabled: %s", init_status["face_error"])
    elif not init_status["faces_enabled"]:
        logger.info("Face recognition disabled.")

    if init_status["plate_error"]:
        logger.warning("Plate recognition disabled: %s", init_status["plate_error"])
    elif not init_status["plates_enabled"]:
        logger.info("Plate recognition disabled.")

    runner = PreviewRunner(
        manager=manager, window_title=args.window_title, stats_interval=args.stats_interval
    )
    exit_code = runner.run()

    manager.stop()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
