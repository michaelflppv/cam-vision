"""
Performance benchmarks for SecureVision pipeline components.

Measures:
- Frame processing latency (face detection, plate detection, OCR)
- Throughput (FPS) for single and multiple streams
- End-to-end latency (frame → event storage)
- API response times
- Memory usage

Run with: pytest tests/benchmarks/test_performance.py -v --benchmark-only
"""

import time
from pathlib import Path
from typing import Generator

import cv2
import numpy as np
import pytest

from cam_vision.config import FaceSettings, PlatesSettings
from cam_vision.events.store import EventStore
from cam_vision.face.gallery import FaceGallery
from cam_vision.face.recognizer import FaceRecognizer
from cam_vision.io.capture import OpenCVCapture
from cam_vision.pipeline.graph import GraphRunner
from cam_vision.plates.pipeline import PlateRecognizer
from cam_vision.types import BBox, Frame


def create_empty_gallery(tmp_path: Path) -> FaceGallery:
    """Create an empty face gallery for benchmarking."""
    gallery_dir = tmp_path / "gallery"
    gallery_dir.mkdir(exist_ok=True)
    cache_file = tmp_path / "gallery_cache.npz"
    gallery = FaceGallery(str(gallery_dir), str(cache_file))
    # Create empty cache
    gallery.person_ids = []
    gallery.embeddings = np.array([]).reshape(0, 512)
    gallery._loaded = True
    return gallery


@pytest.fixture
def sample_frame() -> Frame:
    """Create a sample 720p frame for benchmarking."""
    # 1280x720 RGB frame (realistic resolution)
    image = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    return Frame(
        image=image,
        ts_ms=int(time.time() * 1000),
        source_id="benchmark",
    )


@pytest.fixture
def face_frame() -> Frame:
    """Create a frame with a synthetic face for face recognition benchmarking."""
    # Create a 720p frame with a centered "face" (white rectangle)
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    # Add a face-like region (centered 200x200 white square)
    image[260:460, 540:740] = 255
    return Frame(
        image=image,
        ts_ms=int(time.time() * 1000),
        source_id="face_benchmark",
    )


@pytest.fixture
def plate_frame() -> Frame:
    """Create a frame with a synthetic license plate for ALPR benchmarking."""
    # Create a 720p frame with a license plate region
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    # Add a plate-like region (centered 150x400 white rectangle)
    image[285:435, 440:840] = 255
    return Frame(
        image=image,
        ts_ms=int(time.time() * 1000),
        source_id="plate_benchmark",
    )


@pytest.fixture
def temp_event_db(tmp_path: Path) -> Generator[EventStore, None, None]:
    """Create a temporary event database for benchmarking."""
    db_path = tmp_path / "benchmark.db"
    store = EventStore(db_url=f"sqlite:///{db_path}")
    store.open()
    yield store
    store.close()


# =============================================================================
# Latency Benchmarks
# =============================================================================


class TestLatencyBenchmarks:
    """Measure per-frame processing latency for each component."""

    def test_face_detection_latency(self, benchmark, face_frame: Frame, tmp_path: Path):
        """Benchmark face detection latency (detector + embedder)."""
        # Setup face recognizer with minimal gallery
        gallery = create_empty_gallery(tmp_path)
        recognizer = FaceRecognizer(gallery)
        recognizer.open()

        try:
            # Benchmark single frame processing
            result = benchmark(recognizer.process_frame, face_frame)
            # Should return iterator of events
            _ = list(result)
            # Note: may be empty if no faces detected (synthetic frame)
        finally:
            recognizer.close()

    def test_plate_detection_latency(self, benchmark, plate_frame: Frame, tmp_path: Path):
        """Benchmark plate detection + OCR latency."""
        # Setup plate recognizer without whitelist/blacklist
        settings = PlatesSettings(
            model_path=None,  # Will auto-download
            whitelist_path=None,
            blacklist_path=None,
        )
        recognizer = PlateRecognizer(settings)
        recognizer.open()

        try:
            # Benchmark single frame processing
            result = benchmark(recognizer.process_frame, plate_frame)
            _ = list(result)
        finally:
            recognizer.close()

    def test_frame_capture_latency(self, benchmark, tmp_path: Path):
        """Benchmark frame read latency from file source."""
        # Create a short test video (10 frames)
        test_video = tmp_path / "test.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(test_video), fourcc, 30.0, (640, 480))
        for _ in range(10):
            frame_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            writer.write(frame_img)
        writer.release()

        # Benchmark frame reading
        capture = OpenCVCapture(
            source_type="file",
            source_url=str(test_video),
            fps_target=30,
        )
        capture.open()

        try:
            result = benchmark(capture.read)
            assert result is not None  # Should successfully read frame
        finally:
            capture.close()

    def test_event_storage_latency(self, benchmark, temp_event_db: EventStore):
        """Benchmark event persistence latency."""
        from cam_vision.types import Detection, DetectionKind, Event, FaceMatch

        # Create a sample event
        event = Event(
            type="face_match",
            payload=FaceMatch(
                person_id="test_person",
                similarity=0.85,
                detection=Detection(
                    kind=DetectionKind.FACE,
                    bbox=BBox(100, 100, 200, 200),
                    score=0.95,
                ),
            ),
            frame_source_id="benchmark",
            ts_ms=int(time.time() * 1000),
        )

        # Benchmark event insertion
        result = benchmark(temp_event_db.add_event, event)
        assert result is not None  # Should return event ID


# =============================================================================
# Throughput Benchmarks
# =============================================================================


class TestThroughputBenchmarks:
    """Measure frames-per-second (FPS) for different configurations."""

    def test_face_recognition_throughput(self, sample_frame: Frame, tmp_path: Path):
        """Measure face recognition FPS on continuous frames."""
        gallery = create_empty_gallery(tmp_path)
        recognizer = FaceRecognizer(gallery)
        recognizer.open()

        try:
            # Process 100 frames and measure throughput
            num_frames = 100
            start_time = time.perf_counter()

            for _ in range(num_frames):
                list(recognizer.process_frame(sample_frame))

            elapsed = time.perf_counter() - start_time
            fps = num_frames / elapsed

            print(f"\nFace Recognition Throughput: {fps:.2f} FPS")
            print(f"Per-frame latency: {1000 * elapsed / num_frames:.2f} ms")

            # Store metrics for reporting
            assert fps > 0  # Sanity check
        finally:
            recognizer.close()

    def test_plate_recognition_throughput(self, sample_frame: Frame):
        """Measure plate recognition FPS on continuous frames."""
        settings = PlatesSettings(
            model_path=None,
            whitelist_path=None,
            blacklist_path=None,
        )
        recognizer = PlateRecognizer(settings)
        recognizer.open()

        try:
            # Process 50 frames (YOLO + OCR is slower)
            num_frames = 50
            start_time = time.perf_counter()

            for _ in range(num_frames):
                list(recognizer.process_frame(sample_frame))

            elapsed = time.perf_counter() - start_time
            fps = num_frames / elapsed

            print(f"\nPlate Recognition Throughput: {fps:.2f} FPS")
            print(f"Per-frame latency: {1000 * elapsed / num_frames:.2f} ms")

            assert fps > 0
        finally:
            recognizer.close()

    def test_end_to_end_throughput(self, tmp_path: Path):
        """Measure end-to-end pipeline throughput (capture → process → store)."""
        # Create a test video
        test_video = tmp_path / "test.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(test_video), fourcc, 30.0, (640, 480))
        num_frames = 30  # 1 second of video at 30 FPS
        for _ in range(num_frames):
            frame_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            writer.write(frame_img)
        writer.release()

        # Setup pipeline
        db_path = tmp_path / "events.db"
        event_store = EventStore(db_url=f"sqlite:///{db_path}")
        event_store.open()

        capture = OpenCVCapture(
            source_type="file",
            source_url=str(test_video),
            fps_target=30,
        )

        # Use face recognizer as processor
        gallery = create_empty_gallery(tmp_path)
        processor = FaceRecognizer(gallery)

        from cam_vision.events.sink import EventStoreSink

        sink = EventStoreSink(event_store=event_store, websocket_manager=None)

        runner = GraphRunner(
            frame_source=capture,
            processors=[processor],
            sinks=[sink],
        )

        try:
            start_time = time.perf_counter()
            frames_processed = 0

            # Run pipeline until video ends
            runner.open()
            while runner.run_once():
                frames_processed += 1

            elapsed = time.perf_counter() - start_time
            fps = frames_processed / elapsed if elapsed > 0 else 0

            print(f"\nEnd-to-End Pipeline Throughput: {fps:.2f} FPS")
            print(f"Total frames processed: {frames_processed}")
            print(f"Total time: {elapsed:.2f} s")

            assert frames_processed > 0
        finally:
            runner.close()
            event_store.close()


# =============================================================================
# Multi-Stream Benchmarks
# =============================================================================


class TestMultiStreamBenchmarks:
    """Measure capacity for handling multiple simultaneous streams."""

    def test_sequential_streams_throughput(self, tmp_path: Path):
        """Measure throughput when processing multiple streams sequentially."""
        num_streams = 3
        frames_per_stream = 20

        # Create test videos
        test_videos = []
        for i in range(num_streams):
            video_path = tmp_path / f"stream_{i}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))
            for _ in range(frames_per_stream):
                frame_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                writer.write(frame_img)
            writer.release()
            test_videos.append(video_path)

        # Process each stream sequentially
        face_settings = FaceSettings(gallery_path=str(tmp_path / "empty_gallery"))
        total_frames = 0
        start_time = time.perf_counter()

        for video_path in test_videos:
            capture = OpenCVCapture(
                source_type="file",
                source_url=str(video_path),
                fps_target=30,
            )
            processor = FaceRecognizer(face_settings)
            processor.open()
            capture.open()

            try:
                frame_count = 0
                while True:
                    frame = capture.read()
                    if frame is None:
                        break
                    list(processor.process_frame(frame))
                    frame_count += 1
                total_frames += frame_count
            finally:
                capture.close()
                processor.close()

        elapsed = time.perf_counter() - start_time
        aggregate_fps = total_frames / elapsed if elapsed > 0 else 0

        print(f"\nSequential Streams ({num_streams} streams):")
        print(f"  Total frames: {total_frames}")
        print(f"  Total time: {elapsed:.2f} s")
        print(f"  Aggregate throughput: {aggregate_fps:.2f} FPS")
        print(f"  Per-stream average: {aggregate_fps / num_streams:.2f} FPS")

        assert total_frames == num_streams * frames_per_stream

    def test_simulated_concurrent_streams(self, sample_frame: Frame, tmp_path: Path):
        """Simulate concurrent stream processing by round-robin frame processing."""
        num_streams = 5
        frames_per_stream = 20

        # Create separate processor for each stream
        processors = []
        gallery = create_empty_gallery(tmp_path)
        for _ in range(num_streams):
            proc = FaceRecognizer(gallery)
            proc.open()
            processors.append(proc)

        try:
            start_time = time.perf_counter()

            # Round-robin processing
            for frame_idx in range(frames_per_stream):
                for proc in processors:
                    list(proc.process_frame(sample_frame))

            elapsed = time.perf_counter() - start_time
            total_frames = num_streams * frames_per_stream
            aggregate_fps = total_frames / elapsed if elapsed > 0 else 0

            print(f"\nSimulated Concurrent Streams ({num_streams} streams):")
            print(f"  Total frames: {total_frames}")
            print(f"  Total time: {elapsed:.2f} s")
            print(f"  Aggregate throughput: {aggregate_fps:.2f} FPS")
            print(f"  Per-stream average: {aggregate_fps / num_streams:.2f} FPS")

            assert total_frames > 0
        finally:
            for proc in processors:
                proc.close()


# =============================================================================
# Memory Usage Benchmarks
# =============================================================================


class TestMemoryBenchmarks:
    """Measure memory footprint of components."""

    def test_model_loading_memory(self, tmp_path: Path):
        """Measure memory before/after loading face and plate models."""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Baseline memory
        baseline_mb = process.memory_info().rss / 1024 / 1024

        # Load face recognizer
        face_settings = FaceSettings(gallery_path=str(tmp_path / "empty_gallery"))
        face_recognizer = FaceRecognizer(face_settings)
        face_recognizer.open()
        after_face_mb = process.memory_info().rss / 1024 / 1024
        face_overhead = after_face_mb - baseline_mb

        # Load plate recognizer
        plate_settings = PlatesSettings(model_path=None)
        plate_recognizer = PlateRecognizer(plate_settings)
        plate_recognizer.open()
        after_plate_mb = process.memory_info().rss / 1024 / 1024
        plate_overhead = after_plate_mb - after_face_mb

        print("\nMemory Usage:")
        print(f"  Baseline: {baseline_mb:.1f} MB")
        print(f"  Face model overhead: +{face_overhead:.1f} MB")
        print(f"  Plate model overhead: +{plate_overhead:.1f} MB")
        print(f"  Total: {after_plate_mb:.1f} MB")

        face_recognizer.close()
        plate_recognizer.close()

        # Verify models were loaded
        assert face_overhead > 0
        assert plate_overhead > 0

    def test_event_storage_memory(self, tmp_path: Path):
        """Measure memory growth with event storage."""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        db_path = tmp_path / "memory_test.db"
        event_store = EventStore(db_url=f"sqlite:///{db_path}")
        event_store.open()

        baseline_mb = process.memory_info().rss / 1024 / 1024

        # Insert 1000 events
        from cam_vision.types import Detection, DetectionKind, Event, FaceMatch

        num_events = 1000
        for i in range(num_events):
            event = Event(
                type="face_match",
                payload=FaceMatch(
                    person_id=f"person_{i % 10}",
                    similarity=0.85,
                    detection=Detection(
                        kind=DetectionKind.FACE,
                        bbox=BBox(100, 100, 200, 200),
                        score=0.95,
                    ),
                ),
                frame_source_id="memory_test",
                ts_ms=int(time.time() * 1000) + i,
            )
            event_store.add_event(event)

        after_mb = process.memory_info().rss / 1024 / 1024
        overhead = after_mb - baseline_mb
        per_event_kb = (overhead * 1024) / num_events

        print(f"\nEvent Storage Memory ({num_events} events):")
        print(f"  Memory overhead: +{overhead:.2f} MB")
        print(f"  Per-event: ~{per_event_kb:.2f} KB")

        event_store.close()

        assert overhead >= 0  # Memory should increase or stay same


# =============================================================================
# API Performance Benchmarks
# =============================================================================


class TestAPIBenchmarks:
    """Measure API response times."""

    def test_event_query_latency(self, benchmark, tmp_path: Path):
        """Benchmark event query latency."""
        from cam_vision.types import Detection, DetectionKind, Event, FaceMatch

        db_path = tmp_path / "api_test.db"
        event_store = EventStore(db_url=f"sqlite:///{db_path}")
        event_store.open()

        # Insert 100 events
        for i in range(100):
            event = Event(
                type="face_match",
                payload=FaceMatch(
                    person_id=f"person_{i % 10}",
                    similarity=0.85,
                    detection=Detection(
                        kind=DetectionKind.FACE,
                        bbox=BBox(100, 100, 200, 200),
                        score=0.95,
                    ),
                ),
                frame_source_id="api_test",
                ts_ms=int(time.time() * 1000) + i,
            )
            event_store.add_event(event)

        try:
            # Benchmark query all events
            result = benchmark(event_store.get_events, limit=100)
            assert len(result) == 100
        finally:
            event_store.close()

    def test_event_insertion_throughput(self, tmp_path: Path):
        """Measure event insertion throughput."""
        from cam_vision.types import Detection, DetectionKind, Event, FaceMatch

        db_path = tmp_path / "insertion_test.db"
        event_store = EventStore(db_url=f"sqlite:///{db_path}")
        event_store.open()

        num_events = 500
        start_time = time.perf_counter()

        for i in range(num_events):
            event = Event(
                type="face_match",
                payload=FaceMatch(
                    person_id=f"person_{i % 10}",
                    similarity=0.85,
                    detection=Detection(
                        kind=DetectionKind.FACE,
                        bbox=BBox(100, 100, 200, 200),
                        score=0.95,
                    ),
                ),
                frame_source_id="insertion_test",
                ts_ms=int(time.time() * 1000) + i,
            )
            event_store.add_event(event)

        elapsed = time.perf_counter() - start_time
        events_per_sec = num_events / elapsed if elapsed > 0 else 0

        print("\nEvent Insertion Throughput:")
        print(f"  Events inserted: {num_events}")
        print(f"  Time: {elapsed:.2f} s")
        print(f"  Throughput: {events_per_sec:.1f} events/sec")

        event_store.close()

        assert events_per_sec > 0
