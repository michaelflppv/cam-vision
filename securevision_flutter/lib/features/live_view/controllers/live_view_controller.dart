import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/core/models/frame.dart';
import 'package:securevision_flutter/core/models/source_config.dart';
import 'package:securevision_flutter/core/platform_channels/python_bridge.dart';

class LiveViewState {
  static const _noErrorChange = Object();

  const LiveViewState({
    this.isRunning = false,
    this.isStarting = false,
    this.latestFrame,
    this.latestImage,
    this.errorMessage,
    this.fps = 0,
  });

  final bool isRunning;
  final bool isStarting;
  final Frame? latestFrame;
  final Uint8List? latestImage;
  final String? errorMessage;
  final double fps;

  LiveViewState copyWith({
    bool? isRunning,
    bool? isStarting,
    Frame? latestFrame,
    Uint8List? latestImage,
    Object? errorMessage = _noErrorChange,
    double? fps,
  }) {
    return LiveViewState(
      isRunning: isRunning ?? this.isRunning,
      isStarting: isStarting ?? this.isStarting,
      latestFrame: latestFrame ?? this.latestFrame,
      latestImage: latestImage ?? this.latestImage,
      errorMessage: errorMessage == _noErrorChange
          ? this.errorMessage
          : errorMessage as String?,
      fps: fps ?? this.fps,
    );
  }
}

class LiveViewController extends StateNotifier<LiveViewState> {
  LiveViewController(this._bridge) : super(const LiveViewState());

  final PythonBridge _bridge;
  StreamSubscription<Frame>? _frameSubscription;
  final List<int> _frameTimes = [];

  Future<void> start({
    SourceConfig? source,
    bool enableFaces = true,
    bool enablePlates = true,
    int targetFps = 10,
  }) async {
    state = state.copyWith(isStarting: true, errorMessage: null);
    try {
      _frameTimes.clear();
      await _bridge.initialize({
        'enable_faces': enableFaces,
        'enable_plates': enablePlates,
        'enable_tracking': true,
        'target_fps': targetFps,
        'include_image': true,
      });
      await _bridge.startCapture(source ?? SourceConfig.device());
      await _frameSubscription?.cancel();
      _frameSubscription = _bridge.getFrameStream().listen(_handleFrame);
      state = state.copyWith(isRunning: true, isStarting: false);
    } catch (exc) {
      state = state.copyWith(
        isRunning: false,
        isStarting: false,
        errorMessage: exc.toString(),
      );
    }
  }

  Future<void> stop() async {
    await _frameSubscription?.cancel();
    _frameSubscription = null;
    try {
      await _bridge.stopCapture();
    } catch (_) {
      // Ignore stop errors for now.
    }
    _frameTimes.clear();
    state = state.copyWith(isRunning: false);
  }

  void _handleFrame(Frame frame) {
    _frameTimes.add(DateTime.now().millisecondsSinceEpoch);
    if (_frameTimes.length > 20) {
      _frameTimes.removeRange(0, _frameTimes.length - 20);
    }
    final fps = _calculateFps();
    Uint8List? imageBytes;
    final encoded = frame.imageBase64;
    if (encoded != null && encoded.isNotEmpty) {
      try {
        imageBytes = base64Decode(encoded);
      } catch (_) {
        imageBytes = null;
      }
    }
    state = state.copyWith(
      latestFrame: frame,
      latestImage: imageBytes,
      fps: fps,
    );
  }

  @override
  void dispose() {
    _frameSubscription?.cancel();
    _frameSubscription = null;
    super.dispose();
  }

  double _calculateFps() {
    if (_frameTimes.length < 2) {
      return 0;
    }
    final durationMs = _frameTimes.last - _frameTimes.first;
    if (durationMs <= 0) {
      return 0;
    }
    return (_frameTimes.length - 1) / (durationMs / 1000);
  }
}
