import 'package:flutter/material.dart';
import 'package:securevision_flutter/core/models/detection.dart';
import 'package:securevision_flutter/core/models/event.dart';
import 'package:securevision_flutter/design_system/app_borders.dart';
import 'package:securevision_flutter/design_system/app_colors.dart';
import 'package:securevision_flutter/design_system/app_spacing.dart';
import 'package:securevision_flutter/design_system/components/app_card.dart';

class EventCard extends StatelessWidget {
  const EventCard({super.key, required this.event, required this.onTap});

  final Event event;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final title = _titleFor(event);
    final subtitle = _subtitleFor(event);
    final timestamp = _formatTimestamp(event.timestamp);

    return AppCard(
      onTap: onTap,
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.sm),
            decoration: BoxDecoration(
              border: Border.all(
                color: theme.colorScheme.outline,
                width: AppBorders.thin,
              ),
              borderRadius: AppBorders.minimalRadius,
            ),
            child: Icon(
              _iconFor(event.detection.type),
              color: _accentColor(theme, event),
              size: 20,
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
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            timestamp,
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.secondary,
            ),
          ),
        ],
      ),
    );
  }

  String _titleFor(Event event) {
    switch (event.detection.type) {
      case DetectionType.face:
        return event.detection.faceMatch?.label ?? 'Unknown face';
      case DetectionType.plate:
        return event.detection.plateRead?.plate ?? 'Plate read';
      case DetectionType.unknown:
        return event.type;
    }
  }

  String _subtitleFor(Event event) {
    switch (event.detection.type) {
      case DetectionType.face:
        final similarity = event.detection.faceMatch?.similarity;
        if (similarity != null) {
          return 'Similarity ${(similarity * 100).toStringAsFixed(1)}%';
        }
        return 'Face match event';
      case DetectionType.plate:
        final listType = event.detection.plateRead?.listType;
        if (listType != null && listType.isNotEmpty) {
          return 'Listed on $listType';
        }
        return 'Plate read event';
      case DetectionType.unknown:
        return 'Detection event';
    }
  }

  Color _accentColor(ThemeData theme, Event event) {
    switch (event.detection.type) {
      case DetectionType.face:
        return event.detection.faceMatch == null
            ? AppColors.mediumGrey
            : AppColors.mutedSage;
      case DetectionType.plate:
        if (event.detection.plateRead?.listType == 'blacklist') {
          return AppColors.burntOrange;
        }
        if (event.detection.plateRead?.listType == 'whitelist') {
          return AppColors.mutedSage;
        }
        return AppColors.darkGrey;
      case DetectionType.unknown:
        return AppColors.mediumGrey;
    }
  }

  IconData _iconFor(DetectionType type) {
    switch (type) {
      case DetectionType.face:
        return Icons.person;
      case DetectionType.plate:
        return Icons.directions_car;
      case DetectionType.unknown:
        return Icons.visibility;
    }
  }

  String _formatTimestamp(DateTime value) {
    final local = value.toLocal();
    final month = local.month.toString().padLeft(2, '0');
    final day = local.day.toString().padLeft(2, '0');
    final hour = local.hour.toString().padLeft(2, '0');
    final minute = local.minute.toString().padLeft(2, '0');
    return '$month/$day $hour:$minute';
  }
}
