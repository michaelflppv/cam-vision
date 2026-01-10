import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:securevision_flutter/core/models/event.dart';
import 'package:securevision_flutter/core/models/frame.dart';
import 'package:securevision_flutter/core/models/onvif_discovery.dart';
import 'package:securevision_flutter/core/models/source_config.dart';
import 'package:securevision_flutter/core/platform_channels/python_bridge.dart';

class PythonBridgeDesktop implements PythonBridge {
  PythonBridgeDesktop({String? pythonExecutable})
      : _pythonExecutable = pythonExecutable ?? 'python3';

  final String _pythonExecutable;
  Process? _process;
  StreamSubscription<String>? _stdoutSub;
  StreamSubscription<String>? _stderrSub;
  int _requestCounter = 0;
  final Map<String, Completer<Map<String, dynamic>>> _pendingRequests = {};

  final StreamController<Frame> _frameController = StreamController.broadcast();
  final StreamController<Event> _eventController = StreamController.broadcast();

  @override
  Stream<Frame> getFrameStream() => _frameController.stream;

  @override
  Stream<Event> getEventStream() => _eventController.stream;

  @override
  Future<void> initialize(Map<String, dynamic> config) async {
    await _ensureProcess();
    _sendCommand({'type': 'initialize', 'config': config});
  }

  @override
  Future<void> startCapture(SourceConfig source) async {
    await _ensureProcess();
    _sendCommand({'type': 'start_capture', 'source': source.toJson()});
  }

  @override
  Future<void> stopCapture() async {
    if (_process == null) {
      return;
    }
    _sendCommand({'type': 'stop_capture'});
  }

  @override
  Future<void> enrollFace(Uint8List imageBytes, String personId) async {
    _sendCommand({
      'type': 'enroll_face',
      'person_id': personId,
      'image_base64': base64Encode(imageBytes),
    });
  }

  @override
  Future<void> updatePlateList(String type, List<String> plates) async {
    _sendCommand({
      'type': 'update_plate_list',
      'list_type': type,
      'plates': plates,
    });
  }

  @override
  Future<List<OnvifDiscoveryResult>> discoverOnvif(
    OnvifDiscoveryRequest request,
  ) async {
    final response = await _sendRequest({
      'type': 'discover_onvif',
      'request': request.toJson(),
    });
    if (response['status'] == 'error') {
      throw StateError(response['message']?.toString() ?? 'onvif_error');
    }
    final rawDevices = response['devices'];
    if (rawDevices is! List) {
      return [];
    }
    return rawDevices
        .whereType<Map>()
        .map((device) => OnvifDiscoveryResult.fromJson(
              Map<String, dynamic>.from(device),
            ))
        .toList();
  }

  void _sendCommand(Map<String, dynamic> payload) {
    final process = _process;
    if (process == null) {
      throw StateError('Python subprocess is not running.');
    }
    process.stdin.writeln(jsonEncode(payload));
  }

  void _handleStdoutLine(String line) {
    if (line.trim().isEmpty) {
      return;
    }
    try {
      final payload = jsonDecode(line) as Map<String, dynamic>;
      final messageType = payload['type'];
      if (messageType == 'response') {
        final requestId = payload['request_id']?.toString();
        final completer = requestId == null ? null : _pendingRequests.remove(requestId);
        if (completer != null) {
          final rawInner = payload['payload'];
          final inner =
              rawInner is Map ? Map<String, dynamic>.from(rawInner) : payload;
          completer.complete(inner);
          return;
        }
      }
      final rawInner = payload['payload'];
      final inner =
          rawInner is Map ? Map<String, dynamic>.from(rawInner) : payload;
      switch (messageType) {
        case 'frame':
          _frameController.add(Frame.fromJson(inner));
          break;
        case 'event':
          _eventController.add(Event.fromJson(inner));
          break;
        default:
          stdout.writeln('[python] $line');
      }
    } on FormatException {
      stdout.writeln('[python] $line');
    }
  }

  Future<void> dispose() async {
    await _stdoutSub?.cancel();
    await _stderrSub?.cancel();
    _stdoutSub = null;
    _stderrSub = null;
    _process?.kill();
    _process = null;
    for (final completer in _pendingRequests.values) {
      if (!completer.isCompleted) {
        completer.completeError(StateError('python bridge disposed'));
      }
    }
    _pendingRequests.clear();
    await _frameController.close();
    await _eventController.close();
  }

  Future<Map<String, dynamic>> _sendRequest(
    Map<String, dynamic> payload,
  ) async {
    final id = (++_requestCounter).toString();
    payload['request_id'] = id;
    final completer = Completer<Map<String, dynamic>>();
    _pendingRequests[id] = completer;
    _sendCommand(payload);
    return completer.future.timeout(
      const Duration(seconds: 15),
      onTimeout: () {
        _pendingRequests.remove(id);
        throw TimeoutException('python request timed out');
      },
    );
  }

  Future<void> _ensureProcess() async {
    if (_process != null) {
      return;
    }
    // Determine working directory - go up one level from securevision_flutter
    final workingDir = _getProjectRoot();

    // Resolve script path relative to the new working directory
    final scriptPath = _resolveScriptPath(workingDir);

    _process = await Process.start(
      _pythonExecutable,
      ['-u', scriptPath],
      workingDirectory: workingDir,
    );
    _stdoutSub = _process!.stdout
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .listen(_handleStdoutLine);
    _stderrSub = _process!.stderr
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .listen((line) => stderr.writeln('[python] $line'));
  }

  static String _defaultScriptPath() {
    const candidates = [
      'cam_vision/flutter_bridge/desktop_bridge.py',
      '../cam_vision/flutter_bridge/desktop_bridge.py',
    ];
    for (final candidate in candidates) {
      if (File(candidate).existsSync()) {
        return candidate;
      }
    }
    return candidates.first;
  }

  static String? _getProjectRoot() {
    // Try to find project root by looking for cam_vision directory
    final candidates = [
      '..',  // One level up from securevision_flutter
      '.',   // Current directory
    ];

    for (final candidate in candidates) {
      final dir = Directory(candidate);
      if (!dir.existsSync()) continue;

      // Check if cam_vision directory exists here
      final cvDir = Directory('$candidate/cam_vision');
      if (cvDir.existsSync()) {
        return candidate;
      }
    }

    // Fallback: try to go up from current directory
    return '..';
  }

  static String _resolveScriptPath(String? workingDir) {
    // Script path relative to project root
    const scriptPathFromRoot = 'cam_vision/flutter_bridge/desktop_bridge.py';

    // Check if script exists at this path relative to working directory
    final testPath = workingDir != null
        ? '$workingDir/$scriptPathFromRoot'
        : scriptPathFromRoot;

    if (File(testPath).existsSync()) {
      return scriptPathFromRoot;
    }

    // Fallback to original logic
    return _defaultScriptPath();
  }
}
