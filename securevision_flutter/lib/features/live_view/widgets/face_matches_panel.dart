import 'package:flutter/material.dart';
import 'package:securevision_flutter/core/models/detection.dart';
import 'package:securevision_flutter/design_system/app_colors.dart';
import 'package:securevision_flutter/features/live_view/widgets/detection_card.dart';

class FaceMatchesPanel extends StatelessWidget {
  const FaceMatchesPanel({super.key, required this.detections});

  final List<Detection> detections;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return PanelShell(
      title: 'Face Matches',
      subtitle: 'Confirmed and unknown faces',
      child: detections.isEmpty
          ? Text(
              'No face detections yet.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.secondary,
              ),
            )
          : Column(
              children: [
                for (final detection in detections)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _buildCard(context, detection),
                  ),
              ],
            ),
    );
  }

  Widget _buildCard(BuildContext context, Detection detection) {
    final match = detection.faceMatch;
    final title = match?.label ?? match?.personId ?? 'Unknown face';
    final subtitle = match == null
        ? 'No match found'
        : 'Similarity ${(match.similarity * 100).toStringAsFixed(1)}%';
    final accent =
        match == null ? AppColors.mediumGrey : AppColors.mutedSage;
    return DetectionCard(
      detection: detection,
      accent: accent,
      title: title,
      subtitle: subtitle,
    );
  }
}
