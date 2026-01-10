import 'package:flutter/material.dart';
import '../app_borders.dart';
import '../app_spacing.dart';

/// A flat, bordered card component following Swiss Minimalist design.
/// Replaces inline Container decorations with gradients and shadows.
///
/// Features:
/// - Flat background (no shadows, no gradients)
/// - 1px solid border
/// - 4px border radius
/// - Generous 24px padding by default
/// - Optional tap interaction
class AppCard extends StatelessWidget {
  const AppCard({
    super.key,
    required this.child,
    this.padding,
    this.onTap,
    this.borderColor,
  });

  /// The widget to display inside the card.
  final Widget child;

  /// Padding inside the card. Defaults to 24px (AppSpacing.cardPadding).
  final EdgeInsets? padding;

  /// Optional tap callback. If provided, the card becomes interactive.
  final VoidCallback? onTap;

  /// Optional custom border color. Defaults to theme outline color.
  final Color? borderColor;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectiveBorderColor = borderColor ?? theme.colorScheme.outline;

    final container = Container(
      padding: padding ?? const EdgeInsets.all(AppSpacing.cardPadding),
      decoration: AppBorders.cardDecoration(
        background: theme.colorScheme.surface,
        borderColor: effectiveBorderColor,
      ),
      child: child,
    );

    // Add tap interaction if callback provided
    if (onTap != null) {
      return InkWell(
        onTap: onTap,
        borderRadius: AppBorders.minimalRadius,
        child: container,
      );
    }

    return container;
  }
}
