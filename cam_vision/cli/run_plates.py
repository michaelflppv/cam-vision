"""Demo CLI for testing license plate recognition with live video sources."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time

import cv2

from ..config import VideoSettings, VideoSource
from ..io.capture import OpenCVCapture
from ..plates.detector import YOLOPlateDetector
from ..plates.lists import PlateListLoader
from ..plates.ocr import TesseractOCR
from ..plates.pipeline import PlateRecognizer

logger = logging.getLogger(__name__)


class PlateDemoRunner:
    """Runner for license plate recognition demo with live preview."""

    def __init__(
        self,
        capture: OpenCVCapture,
        recognizer: PlateRecognizer,
        show_preview: bool = False,
        duration: int | None = None,
    ):
        self.capture = capture
        self.recognizer = recognizer
        self.show_preview = show_preview
        self.duration = duration
        self.running = False
        self.read_count = 0
        self.start_time = 0.0

        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\nShutting down...")
        self.running = False

    def run(self) -> None:
        """Run the demo."""
        self.running = True
        self.start_time = time.time()

        print("Starting license plate recognition demo...")
        print(f"Model: {self.recognizer.detector.model_path.name}")
        print(f"Lists: {self.recognizer.lists.size()}")
        print(f"Confidence threshold: {self.recognizer.min_confidence}")
        if self.show_preview:
            print("Preview window enabled (press 'q' to quit)")
        print("Press Ctrl+C to stop\n")

        try:
            self.capture.open()
            self.recognizer.open()

            while self.running:
                # Check duration limit
                if self.duration:
                    elapsed = time.time() - self.start_time
                    if elapsed >= self.duration:
                        print(f"\nReached duration limit ({self.duration}s)")
                        break

                # Read frame
                frame = self.capture.read()

                if frame is None:
                    time.sleep(0.01)
                    continue

                # Process frame
                events = list(self.recognizer.process_frame(frame))

                # Handle events
                for event in events:
                    self.read_count += 1
                    plate_read = event.payload

                    # Colorize output based on list match
                    list_status = ""
                    if plate_read.matched_list == "whitelist":
                        list_status = " [WHITELIST]"
                    elif plate_read.matched_list == "blacklist":
                        list_status = " [BLACKLIST]"

                    print(
                        f"[{event.ts_ms}ms] PLATE: '{plate_read.text_clean}' "
                        f"(raw='{plate_read.text_raw}', conf={plate_read.confidence:.1f}%, "
                        f"det_score={plate_read.detection.score:.3f})"
                        f"{list_status}"
                    )

                # Show preview
                if self.show_preview:
                    annotated = self._annotate_frame(frame.image, events)
                    cv2.imshow("Plate Recognition Demo (press 'q' to quit)", annotated)

                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        print("\nUser pressed 'q' - exiting")
                        break

        except Exception as e:
            print(f"\nError during demo: {e}")
            if logger.isEnabledFor(logging.DEBUG):
                import traceback

                traceback.print_exc()
        finally:
            self.recognizer.close()
            self.capture.close()
            if self.show_preview:
                cv2.destroyAllWindows()

            # Print summary
            self._print_summary()

    def _annotate_frame(self, image, events):
        """Draw bounding boxes and labels on frame."""
        annotated = image.copy()

        for event in events:
            plate_read = event.payload
            bbox = plate_read.detection.bbox

            # Choose color based on list match
            if plate_read.matched_list == "whitelist":
                color = (0, 255, 0)  # Green
            elif plate_read.matched_list == "blacklist":
                color = (0, 0, 255)  # Red
            else:
                color = (255, 255, 0)  # Cyan (no match)

            # Draw bounding box
            cv2.rectangle(
                annotated,
                (bbox.x1, bbox.y1),
                (bbox.x2, bbox.y2),
                color,
                2,
            )

            # Draw label with plate text and confidence
            label = f"{plate_read.text_clean} ({plate_read.confidence:.0f}%)"
            label_y = bbox.y1 - 10 if bbox.y1 > 30 else bbox.y1 + 20

            # Draw label background
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(
                annotated,
                (bbox.x1, label_y - label_h - 5),
                (bbox.x1 + label_w, label_y + 5),
                color,
                -1,
            )

            # Draw label text
            cv2.putText(
                annotated,
                label,
                (bbox.x1, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2,
            )

        # Add FPS counter
        fps = self.capture.get_fps()
        cv2.putText(
            annotated,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        return annotated

    def _print_summary(self) -> None:
        """Print final summary."""
        elapsed = time.time() - self.start_time

        print("\n" + "=" * 60)
        print("PLATE RECOGNITION DEMO SUMMARY")
        print("=" * 60)
        print(f"Duration:       {elapsed:.2f}s")
        print(f"Plate reads:    {self.read_count}")
        print(f"Recognizer stats: {self.recognizer._format_stats()}")
        print("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="License plate recognition demo with YOLOv8 + Tesseract",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # MacBook camera with preview
  securevision-plates --source-type device --device 0 --model weights/yolov8n_plate.pt --preview

  # RTSP camera without preview
  securevision-plates --source-type rtsp --url rtsp://camera/stream --model weights/yolov8n_plate.pt

  # Video file with custom settings
  securevision-plates --source-type file --url video.mp4 --model weights/yolov8n_plate.pt \\
    --whitelist data/plates/whitelist.csv --enable-bilateral --preview
        """,
    )

    # Video source options
    parser.add_argument(
        "--source-type",
        type=str,
        required=True,
        choices=["device", "rtsp", "http_mjpeg", "file"],
        help="Video source type",
    )
    parser.add_argument("--device", type=int, default=0, help="Device index (for device source)")
    parser.add_argument("--url", type=str, help="URL or path (for rtsp/http_mjpeg/file)")
    parser.add_argument("--backend", type=str, help="OpenCV backend (e.g., AVFOUNDATION)")
    parser.add_argument("--fps", type=int, default=15, help="Target FPS (default: 15)")
    parser.add_argument("--resize", type=str, help="Resize frames (e.g., 640x480)")

    # Detector options
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to YOLOv8 plate detection model (.pt file)",
    )
    parser.add_argument(
        "--conf-threshold",
        type=float,
        default=0.25,
        help="Detection confidence threshold (default: 0.25)",
    )

    # List options
    parser.add_argument(
        "--whitelist",
        type=str,
        default="./data/plates/whitelist.csv",
        help="Whitelist CSV path (default: ./data/plates/whitelist.csv)",
    )
    parser.add_argument(
        "--blacklist",
        type=str,
        default="./data/plates/blacklist.csv",
        help="Blacklist CSV path (default: ./data/plates/blacklist.csv)",
    )

    # OCR preprocessing options
    parser.add_argument(
        "--enable-bilateral",
        action="store_true",
        help="Enable bilateral filter preprocessing (good for noise)",
    )
    parser.add_argument(
        "--enable-adaptive",
        action="store_true",
        help="Enable adaptive thresholding (good for uneven lighting)",
    )
    parser.add_argument(
        "--enable-clahe",
        action="store_true",
        help="Enable CLAHE preprocessing (adds overhead, research shows minimal benefit)",
    )

    # Display options
    parser.add_argument("--preview", action="store_true", help="Show live preview with annotations")
    parser.add_argument("--duration", type=int, help="Run for N seconds (default: run forever)")

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Parse resize
    frame_resize = None
    if args.resize:
        try:
            width, height = map(int, args.resize.lower().split("x"))
            frame_resize = (width, height)
        except ValueError:
            print(f"Error: Invalid resize format '{args.resize}'. Use WIDTHxHEIGHT")
            return 1

    # Validate source args
    if args.source_type != "device" and not args.url:
        print(f"Error: --url required for {args.source_type} source")
        return 1

    # Build video source config
    video_source = VideoSource(
        type=args.source_type,
        device_index=args.device if args.source_type == "device" else None,
        backend=args.backend,
        url=args.url,
    )

    video_settings = VideoSettings(
        source=video_source,
        fps_target=args.fps,
        frame_resize=frame_resize,
    )

    try:
        # Create capture
        capture = OpenCVCapture.from_config(video_settings, source_id="plate_demo")

        # Create detector
        detector = YOLOPlateDetector(
            model_path=args.model,
            conf_threshold=args.conf_threshold,
        )

        # Create OCR
        ocr = TesseractOCR(
            enable_bilateral=args.enable_bilateral,
            enable_adaptive_threshold=args.enable_adaptive,
            enable_clahe=args.enable_clahe,
        )

        # Create lists
        lists = PlateListLoader(
            whitelist_path=args.whitelist,
            blacklist_path=args.blacklist,
        )

        # Create recognizer
        recognizer = PlateRecognizer(
            detector=detector,
            ocr=ocr,
            lists=lists,
        )

        # Run demo
        runner = PlateDemoRunner(
            capture=capture,
            recognizer=recognizer,
            show_preview=args.preview,
            duration=args.duration,
        )

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
