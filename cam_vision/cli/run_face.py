"""Demo CLI for testing face recognition with live video sources."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time

import cv2

from ..config import VideoSettings, VideoSource
from ..face.enroll import enroll_gallery
from ..face.gallery import FaceGallery
from ..face.recognizer import FaceRecognizer
from ..io.capture import OpenCVCapture

logger = logging.getLogger(__name__)


class FaceDemoRunner:
    """Runner for face recognition demo with live preview."""

    def __init__(
        self,
        capture: OpenCVCapture,
        recognizer: FaceRecognizer,
        show_preview: bool = False,
        duration: int | None = None,
    ):
        self.capture = capture
        self.recognizer = recognizer
        self.show_preview = show_preview
        self.duration = duration
        self.running = False
        self.match_count = 0
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

        print("Starting face recognition demo...")
        print(f"Gallery: {self.recognizer.gallery.size()} persons")
        print(f"Threshold: {self.recognizer.similarity_threshold}")
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
                    self.match_count += 1
                    face_match = event.payload
                    print(
                        f"[{event.ts_ms}ms] MATCH: {face_match.person_id} "
                        f"(similarity={face_match.similarity:.3f}, "
                        f"det_score={face_match.detection.score:.3f})"
                    )

                # Show preview
                if self.show_preview:
                    annotated = self._annotate_frame(frame.image, events)
                    cv2.imshow("Face Recognition Demo (press 'q' to quit)", annotated)

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
            face_match = event.payload
            bbox = face_match.detection.bbox

            # Draw bounding box (green)
            cv2.rectangle(
                annotated,
                (bbox.x1, bbox.y1),
                (bbox.x2, bbox.y2),
                (0, 255, 0),
                2,
            )

            # Draw label with name and similarity
            label = f"{face_match.person_id} ({face_match.similarity:.2f})"
            label_y = bbox.y1 - 10 if bbox.y1 > 30 else bbox.y1 + 20

            # Draw label background
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(
                annotated,
                (bbox.x1, label_y - label_h - 5),
                (bbox.x1 + label_w, label_y + 5),
                (0, 255, 0),
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
        print("FACE RECOGNITION DEMO SUMMARY")
        print("=" * 60)
        print(f"Duration:       {elapsed:.2f}s")
        print(f"Face matches:   {self.match_count}")
        print(f"Recognizer stats: {self.recognizer._format_stats()}")
        print("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Face recognition demo with live video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # MacBook camera with preview
  securevision-face-demo --source-type device --device 0 --preview

  # RTSP camera without enrollment (assumes gallery exists)
  securevision-face-demo --source-type rtsp --url rtsp://camera/stream --preview

  # Enroll first, then run demo
  securevision-face-demo --source-type device --device 0 --enroll-first --preview

  # Custom gallery and threshold
  securevision-face-demo --source-type device --device 0 \\
    --gallery ./my_faces --threshold 0.45 --preview
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

    # Gallery options
    parser.add_argument(
        "--gallery",
        type=str,
        default="./data/faces/trusted",
        help="Gallery folder (default: ./data/faces/trusted)",
    )
    parser.add_argument(
        "--cache",
        type=str,
        default="./data/faces/gallery.npz",
        help="Gallery cache file (default: ./data/faces/gallery.npz)",
    )
    parser.add_argument(
        "--enroll-first",
        action="store_true",
        help="Run enrollment before starting demo",
    )

    # Recognition options
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.35,
        help="Similarity threshold (default: 0.35, higher=stricter)",
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

    # Enroll if requested
    if args.enroll_first:
        print("Running enrollment first...\n")
        result = enroll_gallery(
            gallery_path=args.gallery,
            cache_path=args.cache,
            force_rebuild=True,
            verbose=args.verbose,
        )
        if result < 0:
            print("Enrollment failed, cannot proceed")
            return 1
        print()

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
        capture = OpenCVCapture.from_config(video_settings, source_id="face_demo")

        # Create gallery
        gallery = FaceGallery(gallery_path=args.gallery, cache_path=args.cache)

        # Create recognizer
        recognizer = FaceRecognizer(
            gallery=gallery,
            similarity_threshold=args.threshold,
        )

        # Run demo
        runner = FaceDemoRunner(
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
