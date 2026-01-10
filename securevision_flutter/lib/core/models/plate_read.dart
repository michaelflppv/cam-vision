class PlateRead {
  const PlateRead({
    required this.plate,
    required this.confidence,
    this.listType,
  });

  final String plate;
  final double confidence;
  final String? listType;

  factory PlateRead.fromJson(Map<String, dynamic> json) {
    return PlateRead(
      plate: json['plate'] as String? ?? 'unknown',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      listType: json['list_type'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'plate': plate,
      'confidence': confidence,
      if (listType != null) 'list_type': listType,
    };
  }
}
