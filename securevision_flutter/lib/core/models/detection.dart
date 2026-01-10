import 'package:securevision_flutter/core/models/face_match.dart';
import 'package:securevision_flutter/core/models/plate_read.dart';

enum DetectionType { face, plate, unknown }

DetectionType detectionTypeFromString(String? value) {
  switch (value) {
    case 'face':
      return DetectionType.face;
    case 'plate':
      return DetectionType.plate;
    default:
      return DetectionType.unknown;
  }
}

String detectionTypeToString(DetectionType type) {
  switch (type) {
    case DetectionType.face:
      return 'face';
    case DetectionType.plate:
      return 'plate';
    case DetectionType.unknown:
      return 'unknown';
  }
}

class BoundingBox {
  const BoundingBox({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
  });

  final double x;
  final double y;
  final double width;
  final double height;

  factory BoundingBox.fromJson(Map<String, dynamic> json) {
    return BoundingBox(
      x: (json['x'] as num?)?.toDouble() ?? 0.0,
      y: (json['y'] as num?)?.toDouble() ?? 0.0,
      width: (json['width'] as num?)?.toDouble() ?? 0.0,
      height: (json['height'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'x': x,
      'y': y,
      'width': width,
      'height': height,
    };
  }
}

class Detection {
  const Detection({
    required this.type,
    required this.confidence,
    required this.boundingBox,
    this.trackId,
    this.faceMatch,
    this.plateRead,
  });

  final DetectionType type;
  final double confidence;
  final BoundingBox boundingBox;
  final String? trackId;
  final FaceMatch? faceMatch;
  final PlateRead? plateRead;

  factory Detection.fromJson(Map<String, dynamic> json) {
    final rawBoundingBox = json['bounding_box'];
    final boundingBoxJson = rawBoundingBox is Map
        ? Map<String, dynamic>.from(rawBoundingBox)
        : const <String, dynamic>{};
    final rawTrackId = json['track_id'];
    final rawFaceMatch = json['face_match'];
    final rawPlateRead = json['plate_read'];
    return Detection(
      type: detectionTypeFromString(json['type'] as String?),
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      boundingBox: BoundingBox.fromJson(boundingBoxJson),
      trackId: rawTrackId?.toString(),
      faceMatch: rawFaceMatch is Map
          ? FaceMatch.fromJson(Map<String, dynamic>.from(rawFaceMatch))
          : null,
      plateRead: rawPlateRead is Map
          ? PlateRead.fromJson(Map<String, dynamic>.from(rawPlateRead))
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': detectionTypeToString(type),
      'confidence': confidence,
      'bounding_box': boundingBox.toJson(),
      if (trackId != null) 'track_id': trackId,
      if (faceMatch != null) 'face_match': faceMatch!.toJson(),
      if (plateRead != null) 'plate_read': plateRead!.toJson(),
    };
  }
}
