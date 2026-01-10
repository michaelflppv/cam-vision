import 'package:securevision_flutter/core/models/detection.dart';

class Frame {
  const Frame({
    required this.id,
    required this.timestamp,
    required this.width,
    required this.height,
    required this.detections,
    this.sourceId,
    this.imageBase64,
  });

  final String id;
  final DateTime timestamp;
  final int width;
  final int height;
  final List<Detection> detections;
  final String? sourceId;
  final String? imageBase64;

  factory Frame.fromJson(Map<String, dynamic> json) {
    final rawDetections = (json['detections'] as List<dynamic>?) ?? const [];
    final detections = <Detection>[];
    for (final raw in rawDetections) {
      if (raw is Map) {
        detections.add(Detection.fromJson(Map<String, dynamic>.from(raw)));
      }
    }
    return Frame(
      id: json['id'] as String? ?? 'frame-0',
      timestamp: _parseTimestamp(json['timestamp']),
      width: (json['width'] as num?)?.toInt() ?? 0,
      height: (json['height'] as num?)?.toInt() ?? 0,
      detections: detections,
      sourceId: json['source_id'] as String?,
      imageBase64: json['image_base64'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'timestamp': timestamp.toIso8601String(),
      'width': width,
      'height': height,
      'detections': detections.map((detection) => detection.toJson()).toList(),
      if (sourceId != null) 'source_id': sourceId,
      if (imageBase64 != null) 'image_base64': imageBase64,
    };
  }
}

DateTime _parseTimestamp(dynamic value) {
  if (value is int) {
    return DateTime.fromMillisecondsSinceEpoch(value, isUtc: true);
  }
  if (value is String) {
    return DateTime.tryParse(value) ?? DateTime.fromMillisecondsSinceEpoch(0, isUtc: true);
  }
  return DateTime.fromMillisecondsSinceEpoch(0, isUtc: true);
}
