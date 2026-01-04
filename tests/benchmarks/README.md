# SecureVision Performance Benchmarks

This directory contains comprehensive benchmarking and accuracy testing for the SecureVision pipeline.

## Overview

The benchmark suite measures:

1. **Processing Speed**: Latency and throughput for all components
2. **Accuracy**: Face verification and plate OCR precision/recall
3. **Scalability**: Multi-stream capacity and resource usage
4. **Stability**: Long-running load tests

## Setup

### Install Dependencies

```bash
# Install all benchmark dependencies
poetry install --with dev

# Or install individually
poetry add --group dev pytest-benchmark jupyter matplotlib seaborn pandas tqdm psutil
```

## Benchmarks

### 1. Performance Benchmarks (`test_performance.py`)

Measures processing latency and throughput for all pipeline components.

**Run all performance tests:**
```bash
pytest tests/benchmarks/test_performance.py -v -s
```

**Run with pytest-benchmark integration:**
```bash
pytest tests/benchmarks/test_performance.py -v --benchmark-only
```

**Metrics measured:**
- Face detection latency (mean, median, P95, P99)
- Plate detection + OCR latency
- Frame capture latency
- Event storage latency
- End-to-end pipeline throughput (FPS)
- Multi-stream aggregate throughput

**Sample output:**
```
Face Recognition Throughput: 24.5 FPS
Plate Recognition Throughput: 8.3 FPS
End-to-End Pipeline Throughput: 18.7 FPS
```

### 2. Accuracy Benchmarks (`test_accuracy.py`)

Measures recognition accuracy and tracking performance.

**Run all accuracy tests:**
```bash
pytest tests/benchmarks/test_accuracy.py -v -s
```

**Metrics measured:**
- Face similarity score distributions
- Precision/Recall/F1 at different thresholds
- Plate OCR character accuracy
- Plate OCR full-plate accuracy
- Track ID persistence
- Multi-object tracking accuracy
- Occlusion recovery rate

**Sample output:**
```
=== Face Threshold Analysis ===
Threshold    Precision    Recall       F1           Accuracy
0.35         0.942        0.890        0.915        0.925

=== Plate OCR Accuracy ===
Character accuracy: 94.2% (452/480)
Plate accuracy:     85.0% (17/20)
```

### 3. Load Tests (`test_load.py`)

Stress tests the system with multiple simultaneous streams.

**Run load tests:**
```bash
pytest tests/benchmarks/test_load.py -v -s
```

**Run with custom stream count:**
```python
# Edit test_load.py and modify stream_counts variable
stream_counts = [1, 2, 3, 4, 5, 8, 10]
```

**Metrics measured:**
- Single stream baseline performance
- Multi-stream capacity (sequential and concurrent)
- Sustained load stability (30+ seconds)
- CPU usage scaling
- Memory growth rate
- Real RTSP stream handling (optional, requires URL)

**Sample output:**
```
=== Multi-Stream Capacity Test ===
1 streams:
  Total frames:     150
  Aggregate FPS:    25.3
  Per-stream FPS:   25.3

3 streams:
  Total frames:     450
  Aggregate FPS:    45.2
  Per-stream FPS:   15.1

5 streams:
  Total frames:     750
  Aggregate FPS:    52.1
  Per-stream FPS:   10.4
```

**Real RTSP stream testing:**
```bash
# Set RTSP URL and remove @pytest.mark.skip decorator
export RTSP_URL="rtsp://user:pass@192.168.1.100:554/stream"
pytest tests/benchmarks/test_load.py::TestRealRTSP::test_real_rtsp_stream -v -s
```

### 4. Interactive Notebook (`notebooks/performance_analysis.ipynb`)

Jupyter notebook for interactive benchmarking with visualizations.

**Launch notebook:**
```bash
# Start Jupyter
poetry run jupyter notebook

# Open notebooks/performance_analysis.ipynb
```

**Features:**
- Interactive latency benchmarking with histograms
- Throughput comparison charts
- Multi-stream scaling visualizations
- Memory usage profiling
- Precision-Recall curves
- Threshold optimization
- Exportable CSV results
- Comprehensive summary reports

**Generated outputs:**
- `performance_report.txt` - Text summary
- `benchmark_latencies.csv` - Raw latency data
- `benchmark_streams.csv` - Stream capacity data
- `benchmark_accuracy.csv` - Accuracy metrics

## Understanding Results

### Latency Metrics

**Good targets:**
- Face detection: < 50ms per frame (enables 20+ FPS)
- Plate detection: < 100ms per frame (enables 10+ FPS)
- Event storage: < 5ms per event

**P95/P99 percentiles:**
- P95: 95% of requests are faster than this
- P99: 99% of requests are faster than this
- Use P95 for capacity planning (ignore rare outliers)

### Throughput Metrics

**Target FPS by use case:**
- Security monitoring: 10-15 FPS (good balance)
- Traffic monitoring: 15-20 FPS (capture fast vehicles)
- Indoor monitoring: 5-10 FPS (people move slower)

**Multi-stream capacity:**
- **Per-stream FPS** should stay above your target
- **Aggregate FPS** shows total system capacity
- Recommended: Keep per-stream FPS ≥ 10 for real-time

### Accuracy Metrics

**Face verification:**
- **Default threshold**: 0.35 (balanced precision/recall)
- **High security**: 0.50+ (fewer false positives)
- **Convenience**: 0.25-0.30 (fewer false negatives)
- **F1 Score**: Harmonic mean of precision/recall (good overall metric)

**Plate OCR:**
- **Character accuracy**: Should be > 90%
- **Plate accuracy**: Should be > 80%
- Multi-frame confirmation helps compensate for OCR errors

### Resource Usage

**Memory:**
- Face model: ~100-150 MB
- Plate model: ~200-300 MB
- Processing overhead: ~10-50 MB per stream

**CPU:**
- Single stream: 20-40% of one core (varies by CPU)
- Multi-stream: Scales linearly until saturation
- Monitor `avg_cpu` to find capacity limit

## Example Workflows

### Find Maximum Stream Capacity

```bash
# Run multi-stream test
pytest tests/benchmarks/test_load.py::TestMultiStreamLoad::test_multi_stream_capacity -v -s

# Analyze output to find where per-stream FPS drops below 10
```

### Optimize Face Threshold

```bash
# Run threshold analysis
pytest tests/benchmarks/test_accuracy.py::TestFaceVerificationAccuracy::test_face_threshold_analysis -v -s

# Or use interactive notebook for visualizations
jupyter notebook notebooks/performance_analysis.ipynb
```

### Profile Memory Leaks

```bash
# Run memory growth test
pytest tests/benchmarks/test_load.py::TestResourceUsage::test_memory_growth_rate -v -s

# Check slope output - should be < 5 MB/sec
```

### End-to-End Pipeline Test

```bash
# Create test video and run full pipeline
pytest tests/benchmarks/test_performance.py::TestThroughputBenchmarks::test_end_to_end_throughput -v -s
```

## Continuous Benchmarking

### Track Performance Over Time

```bash
# Run benchmarks and save results
pytest tests/benchmarks/test_performance.py --benchmark-only --benchmark-json=results.json

# Compare against baseline
pytest tests/benchmarks/test_performance.py --benchmark-only --benchmark-compare=baseline.json
```

### Automated Regression Detection

Add to CI/CD pipeline:

```yaml
# .github/workflows/benchmark.yml
- name: Run benchmarks
  run: |
    poetry run pytest tests/benchmarks/test_performance.py \
      --benchmark-only \
      --benchmark-compare=baseline.json \
      --benchmark-compare-fail=mean:10%
```

## Interpreting Common Issues

### Low FPS

**Symptoms:** FPS below 10 for single stream

**Possible causes:**
- CPU too slow (check with `top` or `htop`)
- Large frame resolution (try 720p instead of 1080p)
- Slow disk I/O (event storage bottleneck)

**Solutions:**
- Reduce `fps_target` in config
- Resize frames before processing
- Use faster storage (SSD vs HDD)

### Memory Growth

**Symptoms:** Memory increases over time

**Possible causes:**
- Event retention not running
- Unclosed resources
- Large frame buffers

**Solutions:**
- Check `retention_days` in config
- Verify `close()` is called on all components
- Reduce frame buffer sizes

### High Latency Variance

**Symptoms:** Large difference between mean and P99

**Possible causes:**
- Garbage collection pauses (Python GC)
- System load spikes
- Network timeouts (for RTSP)

**Solutions:**
- Use dedicated hardware
- Tune Python GC settings
- Add connection retry logic

### Poor Accuracy

**Symptoms:** High false positive/negative rate

**Possible causes:**
- Wrong similarity threshold
- Poor quality input (blur, low resolution)
- Insufficient multi-frame confirmation

**Solutions:**
- Adjust `similarity_threshold` in config
- Enable `blur_detection`
- Increase `frames_required` for tracking

## Contributing

When adding new benchmarks:

1. Add test to appropriate file (`test_performance.py`, `test_accuracy.py`, `test_load.py`)
2. Use descriptive docstrings explaining what's measured
3. Print results in standardized format
4. Update this README with new metrics

## References

- [pytest-benchmark docs](https://pytest-benchmark.readthedocs.io/)
- [InsightFace performance](https://github.com/deepinsight/insightface)
- [YOLOv8 benchmarks](https://docs.ultralytics.com/modes/benchmark/)
