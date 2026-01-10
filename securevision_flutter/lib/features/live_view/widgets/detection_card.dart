import 'package:flutter/material.dart';
import 'package:securevision_flutter/core/models/detection.dart';
import 'package:securevision_flutter/design_system/app_spacing.dart';
import 'package:securevision_flutter/design_system/components/app_card.dart';
import 'package:securevision_flutter/design_system/components/app_chip.dart';
import 'package:securevision_flutter/design_system/components/app_section.dart';

class DetectionCard extends StatelessWidget {
  const DetectionCard({
    super.key,
    required this.detection,
    required this.accent,
    required this.title,
    required this.subtitle,
  });

  final Detection detection;
  final Color accent;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      padding: const EdgeInsets.all(AppSpacing.md),
      borderColor: accent,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 12,
            height: 12,
            margin: const EdgeInsets.only(top: 4),
            decoration: BoxDecoration(
              color: accent,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.secondary,
                  ),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: _buildChips(theme),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildChips(ThemeData theme) {
    final chips = <Widget>[];
    final confidence = _formatConfidence(detection.confidence);
    if (confidence.isNotEmpty) {
      chips.add(AppChip(label: 'conf $confidence'));
    }
    if (detection.trackId != null) {
      chips.add(AppChip(label: 'track ${detection.trackId}'));
    }
    if (detection.type == DetectionType.face && detection.faceMatch == null) {
      chips.add(const AppChip(label: 'unknown'));
    }
    if (detection.type == DetectionType.plate) {
      final listType = detection.plateRead?.listType;
      if (listType != null && listType.isNotEmpty) {
        chips.add(AppChip(label: listType));
      }
    }
    return chips;
  }

  String _formatConfidence(double value) {
    if (value <= 0) {
      return '';
    }
    final percent = value <= 1 ? value * 100 : value;
    return '${percent.toStringAsFixed(0)}%';
  }
}

/// Panel wrapper for detection lists.
/// Uses AppSection for consistent flat, bordered styling.
class PanelShell extends StatelessWidget {
  const PanelShell({
    super.key,
    required this.title,
    required this.subtitle,
    required this.child,
  });

  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(
        minHeight: 200, // Minimum height to keep panels equal
      ),
      child: AppSection(
        title: title,
        subtitle: subtitle,
        child: child,
      ),
    );
  }
}
