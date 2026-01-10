import 'package:securevision_flutter/core/models/detection.dart';

class Event {
  const Event({
    required this.id,
    required this.type,
    required this.timestamp,
    required this.detection,
    this.imagePath,
    this.metadata = const {},
  });

  final String id;
  final String type;
  final DateTime timestamp;
  final Detection detection;
  final String? imagePath;
  final Map<String, dynamic> metadata;

  factory Event.fromJson(Map<String, dynamic> json) {
    final rawDetection = json['detection'];
    final detectionJson = rawDetection is Map
        ? Map<String, dynamic>.from(rawDetection)
        : const <String, dynamic>{};
    final rawMetadata = json['metadata'];
    final metadata = rawMetadata is Map
        ? Map<String, dynamic>.from(rawMetadata)
        : const <String, dynamic>{};
    return Event(
      id: json['id'] as String? ?? 'event-0',
      type: json['type'] as String? ?? 'unknown',
      timestamp: _parseTimestamp(json['timestamp']),
      detection: Detection.fromJson(detectionJson),
      imagePath: json['image_path'] as String?,
      metadata: metadata,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type,
      'timestamp': timestamp.toIso8601String(),
      'detection': detection.toJson(),
      if (imagePath != null) 'image_path': imagePath,
      if (metadata.isNotEmpty) 'metadata': metadata,
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
