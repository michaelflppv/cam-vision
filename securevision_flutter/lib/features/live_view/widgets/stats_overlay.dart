import 'package:flutter/material.dart';
import 'package:securevision_flutter/design_system/app_borders.dart';
import 'package:securevision_flutter/design_system/app_colors.dart';
import 'package:securevision_flutter/design_system/app_spacing.dart';
import 'package:securevision_flutter/design_system/components/app_chip.dart';

class StatsOverlay extends StatelessWidget {
  const StatsOverlay({
    super.key,
    required this.isRunning,
    required this.fps,
    required this.detectionCount,
  });

  final bool isRunning;
  final double fps;
  final int detectionCount;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface.withValues(alpha: 0.9),
        borderRadius: AppBorders.minimalRadius,
        border: Border.all(
          color: theme.colorScheme.outline,
          width: AppBorders.thin,
        ),
      ),
      child: Wrap(
        spacing: 8,
        runSpacing: 6,
        children: [
          AppChip(
            label: isRunning ? 'LIVE' : 'STOP',
            color: isRunning ? AppColors.mutedSage : AppColors.burntOrange,
          ),
          AppChip(
            label: 'fps ${fps.toStringAsFixed(1)}',
            color: theme.colorScheme.onSurface,
          ),
          AppChip(
            label: 'det $detectionCount',
            color: theme.colorScheme.secondary,
          ),
        ],
      ),
    );
  }
}
