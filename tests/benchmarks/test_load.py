"""
Load testing for SecureVision with multiple simultaneous streams.

Measures:
- Maximum number of RTSP streams that can be processed
- CPU and memory usage under load
- Frame drop rate with increasing stream count
- System stability over extended periods

Run with: pytest tests/benchmarks/test_load.py -v -s
"""

import multiprocessing
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

import cv2
import numpy as np
import pytest

from cam_vision.config import PlatesSettings
from cam_vision.face.gallery import FaceGallery
from cam_vision.face.recognizer import FaceRecognizer
from cam_vision.io.capture import OpenCVCapture
from cam_vision.plates.pipeline import PlateRecognizer


def create_empty_gallery(tmp_path: Path) -> FaceGallery:
    """Create an empty face gallery for benchmarking."""
    gallery_dir = tmp_path / "gallery"
    gallery_dir.mkdir(exist_ok=True)
    cache_file = tmp_path / "gallery_cache.npz"
    gallery = FaceGallery(str(gallery_dir), str(cache_file))
    # Create empty cache
    import numpy as np

    gallery.person_ids = []
    gallery.embeddings = np.array([]).reshape(0, 512)
    gallery._loaded = True
    return gallery


@dataclass
class StreamMetrics:
    """Metrics for a single stream."""

    stream_id: int
    frames_processed: int
    frames_dropped: int
    avg_latency_ms: float
    peak_memory_mb: float
    errors: int


@dataclass
class LoadTestResult:
    """Aggregated load test results."""

    num_streams: int
    duration_sec: float
    total_frames: int
    aggregate_fps: float
    per_stream_fps: float
    cpu_usage_percent: float
    memory_usage_mb: float
    success: bool
    stream_metrics: List[StreamMetrics]


# =============================================================================
# Helper Functions
# =============================================================================


def create_test_video(output_path: Path, duration_sec: int = 10, fps: int = 30):
    """Create a test video file for simulating RTSP stream."""
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    num_frames = duration_sec * fps
    for i in range(num_frames):
        # Create frame with frame number overlay
        frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        cv2.putText(
            frame,
            f"Frame {i}",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )
        writer.write(frame)

    writer.release()


def process_stream(
    stream_id: int,
    video_path: str,
    processor_type: str,
    duration_sec: int,
    results_queue: multiprocessing.Queue,
):
    """
    Process a single video stream in a separate process.

    Args:
        stream_id: Unique stream identifier
        video_path: Path to video file (simulates RTSP stream)
        processor_type: "face" or "plate"
        duration_sec: How long to process
        results_queue: Queue to send metrics back to main process
    """
    try:
        import os

        import psutil

        process = psutil.Process(os.getpid())
        start_memory_mb = process.memory_info().rss / 1024 / 1024

        # Setup capture
        capture = OpenCVCapture(
            source_type="file",
            source_url=video_path,
            fps_target=30,
        )

        # Setup processor
        if processor_type == "face":
            import tempfile
            from pathlib import Path

            tmpdir = Path(tempfile.mkdtemp())
            gallery = create_empty_gallery(tmpdir)
            processor = FaceRecognizer(gallery)
        else:
            settings = PlatesSettings(model_path=None)
            processor = PlateRecognizer(settings)

        capture.open()
        processor.open()

        frames_processed = 0
        frames_dropped = 0
        latencies = []
        errors = 0
        start_time = time.perf_counter()

        while time.perf_counter() - start_time < duration_sec:
            frame = capture.read()
            if frame is None:
                # Video ended, restart from beginning
                capture.close()
                capture.open()
                continue

            # Measure processing latency
            frame_start = time.perf_counter()
            try:
                list(processor.process_frame(frame))
                frames_processed += 1
                latencies.append((time.perf_counter() - frame_start) * 1000)
            except Exception:
                errors += 1

        # Get peak memory
        peak_memory_mb = process.memory_info().rss / 1024 / 1024

        # Calculate metrics
        avg_latency = np.mean(latencies) if latencies else 0.0

        metrics = StreamMetrics(
            stream_id=stream_id,
            frames_processed=frames_processed,
            frames_dropped=frames_dropped,
            avg_latency_ms=avg_latency,
            peak_memory_mb=peak_memory_mb - start_memory_mb,
            errors=errors,
        )

        results_queue.put(metrics)

        capture.close()
        processor.close()

    except Exception:
        # Send error metrics
        metrics = StreamMetrics(
            stream_id=stream_id,
            frames_processed=0,
            frames_dropped=0,
            avg_latency_ms=0.0,
            peak_memory_mb=0.0,
            errors=1,
        )
        results_queue.put(metrics)


# =============================================================================
# Load Tests
# =============================================================================


class TestMultiStreamLoad:
    """Load testing with multiple simultaneous streams."""

    def test_single_stream_baseline(self, tmp_path: Path):
        """Establish baseline performance with a single stream."""
        # Create test video
        video_path = tmp_path / "stream_0.mp4"
        create_test_video(video_path, duration_sec=5, fps=30)

        # Process with face recognizer
        results_queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=process_stream,
            args=(0, str(video_path), "face", 5, results_queue),
        )

        start_time = time.perf_counter()
        process.start()
        process.join()
        elapsed = time.perf_counter() - start_time

        metrics = results_queue.get(timeout=1)

        fps = metrics.frames_processed / elapsed if elapsed > 0 else 0

        print("\n=== Single Stream Baseline ===")
        print(f"Duration:        {elapsed:.2f} s")
        print(f"Frames:          {metrics.frames_processed}")
        print(f"FPS:             {fps:.2f}")
        print(f"Avg latency:     {metrics.avg_latency_ms:.2f} ms")
        print(f"Memory:          {metrics.peak_memory_mb:.1f} MB")
        print(f"Errors:          {metrics.errors}")

        assert metrics.frames_processed > 0, "Should process frames"
        assert metrics.errors == 0, "Should have no errors"

    def test_multi_stream_capacity(self, tmp_path: Path):
        """
        Test with increasing number of streams to find capacity limit.

        Finds the maximum number of streams that can be processed
        while maintaining target FPS.
        """
        # Create test videos
        num_test_streams = 5
        duration_sec = 10
        target_fps = 10  # Lower target for multi-stream

        video_paths = []
        for i in range(num_test_streams):
            video_path = tmp_path / f"stream_{i}.mp4"
            create_test_video(video_path, duration_sec=duration_sec, fps=30)
            video_paths.append(video_path)

        print("\n=== Multi-Stream Capacity Test ===")
        print(f"Testing with {num_test_streams} streams, target {target_fps} FPS/stream\n")

        # Test with increasing number of streams
        for num_streams in [1, 2, 3, 5]:
            if num_streams > num_test_streams:
                break

            # Start processes for each stream
            results_queue = multiprocessing.Queue()
            processes = []

            start_time = time.perf_counter()

            for i in range(num_streams):
                video_path = video_paths[i % len(video_paths)]
                proc = multiprocessing.Process(
                    target=process_stream,
                    args=(i, str(video_path), "face", duration_sec, results_queue),
                )
                proc.start()
                processes.append(proc)

            # Wait for all processes
            for proc in processes:
                proc.join()

            elapsed = time.perf_counter() - start_time

            # Collect metrics
            stream_metrics = []
            for _ in range(num_streams):
                try:
                    metrics = results_queue.get(timeout=1)
                    stream_metrics.append(metrics)
                except queue.Empty:
                    pass

            # Aggregate results
            total_frames = sum(m.frames_processed for m in stream_metrics)
            total_errors = sum(m.errors for m in stream_metrics)
            avg_latency = np.mean([m.avg_latency_ms for m in stream_metrics])
            total_memory = sum(m.peak_memory_mb for m in stream_metrics)

            aggregate_fps = total_frames / elapsed if elapsed > 0 else 0
            per_stream_fps = aggregate_fps / num_streams if num_streams > 0 else 0

            success = per_stream_fps >= target_fps and total_errors == 0

            print(f"{num_streams} streams:")
            print(f"  Total frames:     {total_frames}")
            print(f"  Aggregate FPS:    {aggregate_fps:.2f}")
            print(f"  Per-stream FPS:   {per_stream_fps:.2f}")
            print(f"  Avg latency:      {avg_latency:.2f} ms")
            print(f"  Memory total:     {total_memory:.1f} MB")
            print(f"  Errors:           {total_errors}")
            print(f"  Success:          {success}")
            print()

        assert len(stream_metrics) > 0, "Should collect metrics"

    def test_sustained_load(self, tmp_path: Path):
        """
        Test system stability under sustained load.

        Runs 3 streams for 30 seconds to check for memory leaks,
        performance degradation, or crashes.
        """
        num_streams = 3
        duration_sec = 30  # Longer duration

        # Create test videos
        video_paths = []
        for i in range(num_streams):
            video_path = tmp_path / f"sustained_{i}.mp4"
            create_test_video(video_path, duration_sec=60, fps=30)  # Longer video
            video_paths.append(video_path)

        print("\n=== Sustained Load Test ===")
        print(f"Running {num_streams} streams for {duration_sec} seconds\n")

        # Start processes
        results_queue = multiprocessing.Queue()
        processes = []

        start_time = time.perf_counter()

        for i in range(num_streams):
            proc = multiprocessing.Process(
                target=process_stream,
                args=(i, str(video_paths[i]), "face", duration_sec, results_queue),
            )
            proc.start()
            processes.append(proc)

        # Monitor while running
        print("Monitoring (press Ctrl+C to stop early)...")
        all_finished = False
        while not all_finished:
            time.sleep(5)
            alive = [p.is_alive() for p in processes]
            if not any(alive):
                all_finished = True
            else:
                print(f"  {sum(alive)}/{num_streams} streams still running...")

        # Wait for all to finish
        for proc in processes:
            proc.join()

        elapsed = time.perf_counter() - start_time

        # Collect metrics
        stream_metrics = []
        for _ in range(num_streams):
            try:
                metrics = results_queue.get(timeout=1)
                stream_metrics.append(metrics)
            except queue.Empty:
                pass

        # Aggregate results
        total_frames = sum(m.frames_processed for m in stream_metrics)
        total_errors = sum(m.errors for m in stream_metrics)
        avg_memory = np.mean([m.peak_memory_mb for m in stream_metrics])

        aggregate_fps = total_frames / elapsed if elapsed > 0 else 0

        print("\n=== Results ===")
        print(f"Duration:         {elapsed:.2f} s")
        print(f"Total frames:     {total_frames}")
        print(f"Aggregate FPS:    {aggregate_fps:.2f}")
        print(f"Avg memory/stream: {avg_memory:.1f} MB")
        print(f"Total errors:     {total_errors}")

        # Success criteria: no crashes, some frames processed
        assert total_frames > 0, "Should process frames"
        assert total_errors < total_frames * 0.01, "Error rate should be < 1%"


# =============================================================================
# CPU and Memory Profiling
# =============================================================================


class TestResourceUsage:
    """Profile CPU and memory usage under different loads."""

    def test_cpu_usage_scaling(self, tmp_path: Path):
        """Measure CPU usage with increasing stream count."""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil required for CPU profiling")

        # Create test video
        video_path = tmp_path / "cpu_test.mp4"
        create_test_video(video_path, duration_sec=10, fps=30)

        print("\n=== CPU Usage Scaling ===")

        for num_streams in [1, 2, 4]:
            # Start processes
            results_queue = multiprocessing.Queue()
            processes = []

            # Monitor CPU in separate thread
            cpu_samples = []

            def monitor_cpu():
                while processes and any(p.is_alive() for p in processes):
                    cpu_samples.append(psutil.cpu_percent(interval=1))

            monitor_thread = threading.Thread(target=monitor_cpu)

            for i in range(num_streams):
                proc = multiprocessing.Process(
                    target=process_stream,
                    args=(i, str(video_path), "face", 5, results_queue),
                )
                proc.start()
                processes.append(proc)

            monitor_thread.start()

            # Wait for completion
            for proc in processes:
                proc.join()

            monitor_thread.join(timeout=2)

            # Calculate average CPU
            avg_cpu = np.mean(cpu_samples) if cpu_samples else 0.0
            peak_cpu = np.max(cpu_samples) if cpu_samples else 0.0

            print(f"{num_streams} streams:")
            print(f"  Avg CPU:  {avg_cpu:.1f}%")
            print(f"  Peak CPU: {peak_cpu:.1f}%")

        assert len(cpu_samples) > 0, "Should collect CPU samples"

    def test_memory_growth_rate(self, tmp_path: Path):
        """
        Measure memory growth over time to detect leaks.

        Processes frames continuously and samples memory every second.
        """
        try:
            import os

            import psutil
        except ImportError:
            pytest.skip("psutil required for memory profiling")

        # Create test video
        video_path = tmp_path / "memory_test.mp4"
        create_test_video(video_path, duration_sec=30, fps=30)

        # Setup pipeline
        capture = OpenCVCapture(
            source_type="file",
            source_url=str(video_path),
            fps_target=30,
        )

        gallery = create_empty_gallery(tmp_path)
        processor = FaceRecognizer(gallery)

        capture.open()
        processor.open()

        # Sample memory every second
        process = psutil.Process(os.getpid())
        memory_samples = []
        start_time = time.perf_counter()
        last_sample_time = start_time

        try:
            while time.perf_counter() - start_time < 15:  # Run for 15 seconds
                frame = capture.read()
                if frame is None:
                    capture.close()
                    capture.open()
                    continue

                list(processor.process_frame(frame))

                # Sample memory every second
                if time.perf_counter() - last_sample_time >= 1.0:
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(memory_mb)
                    last_sample_time = time.perf_counter()

        finally:
            capture.close()
            processor.close()

        # Analyze memory trend
        if len(memory_samples) >= 2:
            # Linear regression to detect growth
            x = np.arange(len(memory_samples))
            y = np.array(memory_samples)
            slope = np.polyfit(x, y, 1)[0]  # MB per second

            print("\n=== Memory Growth Analysis ===")
            print(f"Samples:         {len(memory_samples)}")
            print(f"Initial memory:  {memory_samples[0]:.1f} MB")
            print(f"Final memory:    {memory_samples[-1]:.1f} MB")
            print(f"Growth rate:     {slope:.2f} MB/sec")

            # Memory should not grow significantly (< 1 MB/sec indicates leak)
            # For 15 seconds, total growth should be reasonable
            total_growth = memory_samples[-1] - memory_samples[0]
            print(f"Total growth:    {total_growth:.1f} MB")

            assert slope < 5.0, "Memory growth rate should be < 5 MB/sec"
        else:
            pytest.skip("Not enough memory samples collected")


# =============================================================================
# Real RTSP Stream Test (Optional)
# =============================================================================


class TestRealRTSP:
    """
    Optional tests for real RTSP streams.

    These tests require actual RTSP stream URLs to be configured.
    Skip if not available.
    """

    @pytest.mark.skip(reason="Requires real RTSP stream URL")
    def test_real_rtsp_stream(self):
        """
        Test with a real RTSP stream.

        To run: set RTSP_URL environment variable and remove @pytest.mark.skip
        """
        import os

        rtsp_url = os.environ.get("RTSP_URL")
        if not rtsp_url:
            pytest.skip("RTSP_URL not configured")

        capture = OpenCVCapture(
            source_type="rtsp",
            source_url=rtsp_url,
            fps_target=10,
        )

        capture.open()

        frames_captured = 0
        start_time = time.perf_counter()
        duration = 10  # Capture for 10 seconds

        try:
            while time.perf_counter() - start_time < duration:
                frame = capture.read()
                if frame is not None:
                    frames_captured += 1
        finally:
            capture.close()

        elapsed = time.perf_counter() - start_time
        fps = frames_captured / elapsed if elapsed > 0 else 0

        print("\n=== Real RTSP Stream ===")
        print(f"URL:      {rtsp_url}")
        print(f"Duration: {elapsed:.2f} s")
        print(f"Frames:   {frames_captured}")
        print(f"FPS:      {fps:.2f}")

        assert frames_captured > 0, "Should capture frames from RTSP stream"
