# SecureVision Benchmarking Quick Start Guide

This guide helps you quickly gather performance metrics for your SecureVision deployment.

## Installation

```bash
# Install all dependencies including benchmarking tools
poetry install --with dev
```

## Quick Performance Check

### 1. Basic Performance Test (5 minutes)

Run the core performance benchmarks to get latency and throughput metrics:

```bash
poetry run pytest tests/benchmarks/test_performance.py -v -s
```

**What you'll learn:**
- Face detection latency (ms per frame)
- Plate recognition latency (ms per frame)
- Maximum achievable FPS for each component
- End-to-end pipeline throughput

**Expected output:**
```
Face Recognition Latency:
  Mean:   42.3 ms
  Median: 41.2 ms
  P95:    48.7 ms

Face Recognition Throughput: 23.6 FPS
Plate Recognition Throughput: 9.4 FPS
```

### 2. Multi-Stream Capacity Test (10 minutes)

Find out how many simultaneous RTSP streams your system can handle:

```bash
poetry run pytest tests/benchmarks/test_load.py::TestMultiStreamLoad::test_multi_stream_capacity -v -s
```

**What you'll learn:**
- Maximum number of streams at 10+ FPS per stream
- Aggregate system throughput
- Per-stream performance degradation

**Expected output:**
```
1 streams: Aggregate 24.5 FPS, Per-stream 24.5 FPS
2 streams: Aggregate 42.1 FPS, Per-stream 21.0 FPS
3 streams: Aggregate 51.3 FPS, Per-stream 17.1 FPS
5 streams: Aggregate 60.2 FPS, Per-stream 12.0 FPS ← Sweet spot
```

### 3. Accuracy Analysis (5 minutes)

Evaluate face verification and plate OCR accuracy:

```bash
poetry run pytest tests/benchmarks/test_accuracy.py -v -s
```

**What you'll learn:**
- Optimal face similarity threshold
- Precision, Recall, and F1 scores
- Plate OCR character/plate accuracy
- Tracking consistency

**Expected output:**
```
=== Face Threshold Analysis ===
Optimal threshold (max F1): 0.37
  Precision: 0.945
  Recall:    0.893
  F1:        0.918

=== Plate OCR Accuracy ===
Character accuracy: 92.5%
Plate accuracy:     83.3%
```

## Interactive Analysis (Recommended)

For visual analysis with charts and detailed insights:

```bash
# Launch Jupyter
poetry run jupyter notebook

# Open: notebooks/performance_analysis.ipynb
# Run all cells (Cell → Run All)
```

**What you'll get:**
- Interactive latency histograms
- Throughput comparison charts
- Multi-stream scaling graphs
- Memory usage profiling
- Precision-Recall curves
- Exportable CSV data
- Comprehensive PDF-ready report

## Key Metrics Explained

### Processing Speed

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Face detection latency | < 40ms | < 60ms | > 60ms |
| Plate recognition latency | < 80ms | < 120ms | > 120ms |
| Single stream FPS | > 20 FPS | > 10 FPS | < 10 FPS |

### Multi-Stream Capacity

**Rule of thumb:** Your system can handle **N streams** where:
- Per-stream FPS stays ≥ 10 FPS
- CPU usage stays < 80%
- Memory usage is sustainable

**Example:**
- 4-core CPU @ 3.0 GHz: 3-5 streams
- 8-core CPU @ 3.5 GHz: 6-10 streams
- 16-core CPU @ 4.0 GHz: 12-20 streams

### Accuracy Targets

| Metric | Security Mode | Balanced | Convenience |
|--------|---------------|----------|-------------|
| Face threshold | 0.50+ | 0.35-0.45 | 0.25-0.30 |
| False positive rate | < 1% | < 5% | < 10% |
| False negative rate | < 10% | < 5% | < 1% |

## Real RTSP Stream Testing

To test with your actual camera:

```bash
# 1. Edit tests/benchmarks/test_load.py
# 2. Remove @pytest.mark.skip from test_real_rtsp_stream
# 3. Run:

export RTSP_URL="rtsp://username:password@192.168.1.100:554/stream"
poetry run pytest tests/benchmarks/test_load.py::TestRealRTSP::test_real_rtsp_stream -v -s
```

## Common Scenarios

### "How many cameras can my server handle?"

```bash
# Run capacity test
poetry run pytest tests/benchmarks/test_load.py::TestMultiStreamLoad::test_multi_stream_capacity -v -s

# Look for where per-stream FPS drops below 10
# That's your maximum recommended stream count
```

### "Why is my FPS so low?"

```bash
# Profile memory and CPU
poetry run pytest tests/benchmarks/test_load.py::TestResourceUsage -v -s

# Check:
# - CPU usage (should be < 80% at target load)
# - Memory growth rate (should be < 5 MB/sec)
# - Model overhead (face ~150MB, plate ~300MB)
```

### "What face threshold should I use?"

```bash
# Run threshold analysis
poetry run pytest tests/benchmarks/test_accuracy.py::TestFaceVerificationAccuracy::test_face_threshold_analysis -v -s

# Or use interactive notebook for visual analysis
poetry run jupyter notebook notebooks/performance_analysis.ipynb
```

### "Is my plate OCR accurate enough?"

```bash
# Test OCR accuracy
poetry run pytest tests/benchmarks/test_accuracy.py::TestPlateOCRAccuracy -v -s

# Character accuracy should be > 90%
# Plate accuracy should be > 80%
# Multi-frame confirmation helps compensate
```

## Performance Optimization Tips

### If FPS is too low:

1. **Reduce resolution:** 720p instead of 1080p
   ```bash
   SECUREVISION__VIDEO__RESIZE_WIDTH=1280
   SECUREVISION__VIDEO__RESIZE_HEIGHT=720
   ```

2. **Lower target FPS:** 10-15 FPS is often sufficient
   ```bash
   SECUREVISION__VIDEO__FPS_TARGET=10
   ```

3. **Disable expensive features:**
   ```bash
   SECUREVISION__FACE__BLUR_DETECTION=false
   ```

### If accuracy is too low:

1. **Increase face threshold:**
   ```bash
   SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.45
   ```

2. **Require more confirmation frames:**
   ```bash
   SECUREVISION__TRACKING__FRAMES_REQUIRED=5
   ```

3. **Enable quality gates:**
   ```bash
   SECUREVISION__FACE__MIN_FACE_SIZE=50
   SECUREVISION__FACE__BLUR_DETECTION=true
   ```

### If you're getting false positives:

1. **Tighten thresholds:**
   ```bash
   SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.50
   SECUREVISION__PLATES__CONFIDENCE_THRESHOLD=0.70
   ```

2. **Increase confirmation frames:**
   ```bash
   SECUREVISION__TRACKING__FRAMES_REQUIRED=5
   ```

3. **Enable cooldown:**
   ```bash
   SECUREVISION__EVENTS__DEDUP_COOLDOWN_SEC=60
   ```

## Exporting Results

All metrics can be exported to CSV for further analysis:

```python
# In Jupyter notebook (notebooks/performance_analysis.ipynb)
# Run the "Export Metrics" cell at the end

# Generates:
# - performance_report.txt (summary)
# - benchmark_latencies.csv (raw data)
# - benchmark_streams.csv (capacity data)
# - benchmark_accuracy.csv (accuracy metrics)
```

## Continuous Monitoring

For production deployments, run benchmarks periodically:

```bash
# Weekly performance check
poetry run pytest tests/benchmarks/test_performance.py --benchmark-json=weekly_$(date +%Y%m%d).json

# Compare against baseline
poetry run pytest tests/benchmarks/test_performance.py \
  --benchmark-compare=baseline.json \
  --benchmark-compare-fail=mean:10%  # Fail if >10% slower
```

## Need Help?

See detailed documentation:
- `tests/benchmarks/README.md` - Full benchmark documentation
- `notebooks/performance_analysis.ipynb` - Interactive analysis
- `CLAUDE.md` - Project architecture and design decisions

## Summary Checklist

Run this complete benchmark suite:

```bash
# 1. Performance benchmarks (~5 min)
poetry run pytest tests/benchmarks/test_performance.py -v -s

# 2. Accuracy benchmarks (~5 min)
poetry run pytest tests/benchmarks/test_accuracy.py -v -s

# 3. Multi-stream capacity (~10 min)
poetry run pytest tests/benchmarks/test_load.py -v -s

# 4. Interactive analysis (optional, ~15 min)
poetry run jupyter notebook notebooks/performance_analysis.ipynb
```

**You should now have:**
- ✅ Processing latency metrics (ms per frame)
- ✅ Throughput capacity (FPS per component)
- ✅ Multi-stream capacity (max simultaneous streams)
- ✅ Accuracy metrics (precision, recall, F1)
- ✅ Resource usage profile (CPU, memory)
- ✅ Optimal configuration recommendations

## Quick Reference Table

| Test | Command | Time | What It Tells You |
|------|---------|------|-------------------|
| Performance | `pytest tests/benchmarks/test_performance.py -v -s` | 5 min | Latency & throughput |
| Accuracy | `pytest tests/benchmarks/test_accuracy.py -v -s` | 5 min | Precision, recall, F1 |
| Capacity | `pytest tests/benchmarks/test_load.py -v -s` | 10 min | Max streams |
| Interactive | `jupyter notebook notebooks/performance_analysis.ipynb` | 15 min | Visual analysis |

---

**Next Steps:**
1. Run the quick performance test
2. Review the output to understand your baseline
3. Use the interactive notebook for detailed analysis
4. Optimize configuration based on results
5. Re-run benchmarks to verify improvements
