import 'dart:typed_data';

import 'package:securevision_flutter/core/models/event.dart';
import 'package:securevision_flutter/core/models/frame.dart';
import 'package:securevision_flutter/core/models/onvif_discovery.dart';
import 'package:securevision_flutter/core/models/source_config.dart';

abstract class PythonBridge {
  Future<void> initialize(Map<String, dynamic> config);
  Future<void> startCapture(SourceConfig source);
  Future<void> stopCapture();
  Stream<Frame> getFrameStream();
  Stream<Event> getEventStream();
  Future<void> enrollFace(Uint8List imageBytes, String personId);
  Future<void> updatePlateList(String type, List<String> plates);
  Future<List<OnvifDiscoveryResult>> discoverOnvif(
    OnvifDiscoveryRequest request,
  );
}
