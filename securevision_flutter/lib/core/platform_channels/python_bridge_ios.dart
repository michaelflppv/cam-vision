import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:securevision_flutter/core/models/event.dart';
import 'package:securevision_flutter/core/models/frame.dart';
import 'package:securevision_flutter/core/models/onvif_discovery.dart';
import 'package:securevision_flutter/core/models/source_config.dart';
import 'package:securevision_flutter/core/platform_channels/python_bridge.dart';

class PythonBridgeIOS implements PythonBridge {
  PythonBridgeIOS({Map<String, String>? assetPaths})
      : _assetPaths = assetPaths ?? {};

  final Map<String, String> _assetPaths;

  static const MethodChannel _channel = MethodChannel('securevision/python_bridge');
  static const EventChannel _frameChannel = EventChannel('securevision/python_frames');
  static const EventChannel _eventChannel = EventChannel('securevision/python_events');

  @override
  Future<void> initialize(Map<String, dynamic> config) async {
    // Merge asset paths into config
    final enrichedConfig = Map<String, dynamic>.from(config);
    enrichedConfig.addAll(_assetPaths);

    // Set environment variables for Python to use
    if (_assetPaths.containsKey('gallery_path')) {
      Platform.environment['SECUREVISION__FACE__GALLERY_PATH'] =
          _assetPaths['gallery_path']!;
    }
    if (_assetPaths.containsKey('gallery_cache')) {
      Platform.environment['SECUREVISION__FACE__GALLERY_CACHE'] =
          _assetPaths['gallery_cache']!;
    }
    if (_assetPaths.containsKey('weights_path')) {
      Platform.environment['SECUREVISION__PLATES__DETECTOR__MODEL_PATH'] =
          _assetPaths['weights_path']!;
    }

    await _channel.invokeMethod('initialize', enrichedConfig);
  }

  @override
  Future<void> startCapture(SourceConfig source) async {
    await _channel.invokeMethod('startCapture', source.toJson());
  }

  @override
  Future<void> stopCapture() async {
    await _channel.invokeMethod('stopCapture');
  }

  @override
  Stream<Frame> getFrameStream() {
    return _frameChannel
        .receiveBroadcastStream()
        .map(_normalizePayload)
        .where((payload) => payload['status'] != 'empty')
        .map(Frame.fromJson);
  }

  @override
  Stream<Event> getEventStream() {
    return _eventChannel
        .receiveBroadcastStream()
        .map(_normalizePayload)
        .where((payload) => payload['status'] != 'empty')
        .map(Event.fromJson);
  }

  @override
  Future<void> enrollFace(Uint8List imageBytes, String personId) async {
    await _channel.invokeMethod('enrollFace', {
      'person_id': personId,
      'image_base64': base64Encode(imageBytes),
    });
  }

  @override
  Future<void> updatePlateList(String type, List<String> plates) async {
    await _channel.invokeMethod('updatePlateList', {
      'list_type': type,
      'plates': plates,
    });
  }

  @override
  Future<List<OnvifDiscoveryResult>> discoverOnvif(
    OnvifDiscoveryRequest request,
  ) {
    throw UnimplementedError('ONVIF discovery is not available on iOS.');
  }

  Map<String, dynamic> _normalizePayload(dynamic payload) {
    if (payload is String) {
      return _unwrapEnvelope(jsonDecode(payload) as Map<String, dynamic>);
    }
    if (payload is Map) {
      return _unwrapEnvelope(Map<String, dynamic>.from(payload));
    }
    throw FormatException('Unsupported payload type: ${payload.runtimeType}');
  }

  Map<String, dynamic> _unwrapEnvelope(Map<String, dynamic> payload) {
    final rawInner = payload['payload'];
    if (rawInner is Map) {
      return Map<String, dynamic>.from(rawInner);
    }
    return payload;
  }
}
