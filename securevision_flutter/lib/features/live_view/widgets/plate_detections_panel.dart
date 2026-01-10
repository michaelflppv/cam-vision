import 'package:flutter/material.dart';
import 'package:securevision_flutter/core/models/detection.dart';
import 'package:securevision_flutter/design_system/app_colors.dart';
import 'package:securevision_flutter/features/live_view/widgets/detection_card.dart';

class PlateDetectionsPanel extends StatelessWidget {
  const PlateDetectionsPanel({super.key, required this.detections});

  final List<Detection> detections;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return PanelShell(
      title: 'Plate Detections',
      subtitle: 'Recent license plate reads',
      child: detections.isEmpty
          ? Text(
              'No plates detected yet.',
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
    final read = detection.plateRead;
    final title = read?.plate ?? 'Unknown plate';
    final subtitle = read == null
        ? 'Awaiting OCR'
        : 'Confidence ${read.confidence.toStringAsFixed(1)}%';
    final listType = read?.listType;
    final accent = listType == 'blacklist'
        ? AppColors.burntOrange
        : listType == 'whitelist'
            ? AppColors.mutedSage
            : AppColors.darkGrey;
    return DetectionCard(
      detection: detection,
      accent: accent,
      title: title,
      subtitle: subtitle,
    );
  }
}
