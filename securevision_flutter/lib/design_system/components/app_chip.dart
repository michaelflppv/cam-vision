import 'package:flutter/material.dart';
import '../app_spacing.dart';
import '../app_typography.dart';

/// A minimal chip/badge component following Swiss Minimalist design.
/// Replaces inline chip widgets with consistent styling.
///
/// Features:
/// - Off-white background
/// - 1px solid border
/// - 4px border radius
/// - Compact padding (8px horizontal, 4px vertical)
/// - Optional text color customization
class AppChip extends StatelessWidget {
  const AppChip({
    super.key,
    required this.label,
    this.color,
  });

  /// The text to display inside the chip.
  final String label;

  /// Optional text color. If null, uses theme secondary color.
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectiveColor = color ?? theme.colorScheme.secondary;

    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        border: Border.all(
          color: theme.colorScheme.outline,
          width: 1.0,
        ),
        borderRadius: BorderRadius.circular(4.0),
      ),
      child: Text(
        label,
        style: AppTypography.labelSmall.copyWith(
          color: effectiveColor,
        ),
      ),
    );
  }
}
