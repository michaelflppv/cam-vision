enum SourceType { device, rtsp, httpMjpeg, file, rtmp, unknown }

SourceType sourceTypeFromString(String? value) {
  switch (value) {
    case 'device':
      return SourceType.device;
    case 'rtsp':
      return SourceType.rtsp;
    case 'http':
    case 'http_mjpeg':
      return SourceType.httpMjpeg;
    case 'file':
      return SourceType.file;
    case 'rtmp':
      return SourceType.rtmp;
    default:
      return SourceType.unknown;
  }
}

String sourceTypeToString(SourceType sourceType) {
  switch (sourceType) {
    case SourceType.device:
      return 'device';
    case SourceType.rtsp:
      return 'rtsp';
    case SourceType.httpMjpeg:
      return 'http_mjpeg';
    case SourceType.file:
      return 'file';
    case SourceType.rtmp:
      return 'rtmp';
    case SourceType.unknown:
      return 'unknown';
  }
}

class SourceConfig {
  const SourceConfig({
    required this.sourceType,
    this.uri,
    this.deviceIndex,
    this.targetFps,
  });

  final SourceType sourceType;
  final String? uri;
  final int? deviceIndex;
  final int? targetFps;

  factory SourceConfig.device({int deviceIndex = 0, int? targetFps}) {
    return SourceConfig(
      sourceType: SourceType.device,
      deviceIndex: deviceIndex,
      targetFps: targetFps,
    );
  }

  factory SourceConfig.fromJson(Map<String, dynamic> json) {
    final url = (json['url'] ?? json['uri']) as String?;
    return SourceConfig(
      sourceType: sourceTypeFromString(json['type'] as String?),
      uri: url,
      deviceIndex: (json['device_index'] as num?)?.toInt(),
      targetFps: (json['target_fps'] as num?)?.toInt(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': sourceTypeToString(sourceType),
      if (uri != null) 'url': uri,
      if (deviceIndex != null) 'device_index': deviceIndex,
      if (targetFps != null) 'target_fps': targetFps,
    };
  }
}
