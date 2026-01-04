"""CLI tool for testing video capture sources with live preview and FPS monitoring."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from typing import Optional

import cv2

from ..config import VideoSettings, VideoSource
from ..io.capture import OpenCVCapture
from ..utils.timing import FPSMeter


class CaptureRunner:
    """Runner for capture testing with preview and statistics."""

    def __init__(
        self,
        capture: OpenCVCapture,
        show_preview: bool = False,
        duration: Optional[int] = None,
        verbose: bool = False,
    ):
        self.capture = capture
        self.show_preview = show_preview
        self.duration = duration
        self.verbose = verbose
        self.running = False
        self.stats = {
            "total_frames": 0,
            "start_time": 0.0,
            "last_fps_report": 0.0,
        }
        self.fps_meter = FPSMeter(window=60)

        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\nShutting down gracefully...")
        self.running = False

    def run(self) -> None:
        """Run the capture loop."""
        self.running = True
        self.stats["start_time"] = time.time()
        self.stats["last_fps_report"] = time.time()

        print(f"Starting capture from {self.capture.source_config.type} source...")
        print(f"Target FPS: {self.capture.fps_target}")
        if self.show_preview:
            print("Preview window enabled (press 'q' to quit)")
        print("Press Ctrl+C to stop\n")

        try:
            self.capture.open()

            while self.running:
                # Check duration limit
                if self.duration:
                    elapsed = time.time() - self.stats["start_time"]
                    if elapsed >= self.duration:
                        print(f"\nReached duration limit ({self.duration}s)")
                        break

                # Read frame
                frame = self.capture.read()

                if frame is None:
                    # No frame available (dropped for FPS control or timeout)
                    time.sleep(0.01)  # Small sleep to avoid busy-waiting
                    continue

                # Update stats
                self.stats["total_frames"] += 1
                self.fps_meter.tick()

                # Show preview if enabled
                if self.show_preview:
                    self._show_preview(frame.image)

                    # Check for 'q' key press to quit
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        print("\nUser pressed 'q' - exiting")
                        break

                # Periodic FPS report
                now = time.time()
                if now - self.stats["last_fps_report"] >= 2.0:
                    self._print_stats()
                    self.stats["last_fps_report"] = now

        except Exception as e:
            print(f"\nError during capture: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()
        finally:
            self.capture.close()
            if self.show_preview:
                cv2.destroyAllWindows()

            # Print final summary
            self._print_summary()

    def _show_preview(self, image) -> None:
        """Display preview window."""
        # Add FPS overlay
        fps = self.fps_meter.fps()
        cv2.putText(
            image,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Capture Preview (press 'q' to quit)", image)

    def _print_stats(self) -> None:
        """Print current statistics."""
        fps = self.fps_meter.fps()
        elapsed = time.time() - self.stats["start_time"]
        print(
            f"Frames: {self.stats['total_frames']:6d} | "
            f"FPS: {fps:5.1f} | "
            f"Elapsed: {elapsed:6.1f}s"
        )

    def _print_summary(self) -> None:
        """Print final summary."""
        elapsed = time.time() - self.stats["start_time"]
        avg_fps = self.stats["total_frames"] / elapsed if elapsed > 0 else 0

        print("\n" + "=" * 60)
        print("CAPTURE SUMMARY")
        print("=" * 60)
        print(f"Source type:    {self.capture.source_config.type}")
        print(f"Total frames:   {self.stats['total_frames']}")
        print(f"Duration:       {elapsed:.2f}s")
        print(f"Average FPS:    {avg_fps:.2f}")
        print(f"Target FPS:     {self.capture.fps_target}")
        fps_delta = abs(avg_fps - self.capture.fps_target)
        fps_tolerance = self.capture.fps_target * 0.1
        if fps_delta <= fps_tolerance:
            print("FPS Status:     ✓ Within ±10% tolerance")
        else:
            print(f"FPS Status:     ⚠ Outside ±10% tolerance (Δ={fps_delta:.2f})")
        print("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Test video capture from device/RTSP/HTTP/file sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # MacBook camera with preview
  securevision-capture --source-type device --device 0 --backend AVFOUNDATION --preview

  # RTSP camera at 10 FPS
  securevision-capture --source-type rtsp --url rtsp://user:pass@192.168.1.100/stream --fps 10

  # HTTP MJPEG stream with resize
  securevision-capture --source-type http_mjpeg --url http://192.168.1.50:8080/video --resize 640x480

  # Video file for testing (loop for 30 seconds)
  securevision-capture --source-type file --url /path/to/video.mp4 --duration 30
        """,
    )

    parser.add_argument(
        "--source-type",
        type=str,
        required=True,
        choices=["device", "rtsp", "http_mjpeg", "file", "rtmp"],
        help="Video source type",
    )

    parser.add_argument("--device", type=int, default=0, help="Device index (for device source)")

    parser.add_argument(
        "--url",
        type=str,
        help="URL or file path (for rtsp/http_mjpeg/file sources)",
    )

    parser.add_argument(
        "--backend",
        type=str,
        help="OpenCV backend (e.g., AVFOUNDATION, V4L2, DSHOW)",
    )

    parser.add_argument("--fps", type=int, default=15, help="Target FPS (default: 15)")

    parser.add_argument(
        "--resize",
        type=str,
        help="Resize frames to WIDTHxHEIGHT (e.g., 640x480)",
    )

    parser.add_argument(
        "--rotate-180",
        action="store_true",
        help="Rotate frames 180 degrees",
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show live preview window",
    )

    parser.add_argument(
        "--duration",
        type=int,
        help="Run for N seconds (default: run forever)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for CLI."""
    args = parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Parse resize if provided
    frame_resize = None
    if args.resize:
        try:
            width, height = map(int, args.resize.lower().split("x"))
            frame_resize = (width, height)
        except ValueError:
            print(f"Error: Invalid resize format '{args.resize}'. Use WIDTHxHEIGHT (e.g., 640x480)")
            return 1

    # Validate source-specific arguments
    if args.source_type != "device" and not args.url:
        print(f"Error: --url required for {args.source_type} source")
        return 1

    # Build VideoSource config
    video_source = VideoSource(
        type=args.source_type,
        device_index=args.device if args.source_type == "device" else None,
        backend=args.backend,
        url=args.url,
    )

    # Build VideoSettings
    video_settings = VideoSettings(
        source=video_source,
        fps_target=args.fps,
        frame_resize=frame_resize,
        rotate_180=args.rotate_180,
    )

    # Create capture
    try:
        capture = OpenCVCapture.from_config(video_settings, source_id="cli_capture")
    except Exception as e:
        print(f"Error creating capture: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    # Run capture
    runner = CaptureRunner(
        capture=capture,
        show_preview=args.preview,
        duration=args.duration,
        verbose=args.verbose,
    )

    try:
        runner.run()
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
