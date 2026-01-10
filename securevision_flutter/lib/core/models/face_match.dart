class FaceMatch {
  const FaceMatch({
    required this.personId,
    required this.similarity,
    this.label,
  });

  final String personId;
  final double similarity;
  final String? label;

  factory FaceMatch.fromJson(Map<String, dynamic> json) {
    return FaceMatch(
      personId: json['person_id'] as String? ?? 'unknown',
      similarity: (json['similarity'] as num?)?.toDouble() ?? 0.0,
      label: json['label'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'person_id': personId,
      'similarity': similarity,
      if (label != null) 'label': label,
    };
  }
}
