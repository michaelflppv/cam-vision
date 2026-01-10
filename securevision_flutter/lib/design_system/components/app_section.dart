import 'package:flutter/material.dart';
import '../app_spacing.dart';
import '../app_typography.dart';
import 'app_card.dart';

/// A section container component with title, subtitle, and content.
/// Replaces _SectionCard in settings_screen.dart and PanelShell in detection_card.dart.
///
/// Features:
/// - Wrapped in AppCard (flat, bordered)
/// - Headline title with negative letter spacing
/// - Optional subtitle
/// - 12px gap between header and content
class AppSection extends StatelessWidget {
  const AppSection({
    super.key,
    required this.title,
    this.subtitle,
    required this.child,
  });

  /// The section title (headline).
  final String title;

  /// Optional subtitle for additional context.
  final String? subtitle;

  /// The content to display below the header.
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Title
          Text(
            title,
            style: AppTypography.headline3,
          ),

          // Optional subtitle
          if (subtitle != null) ...[
            const SizedBox(height: AppSpacing.xs),
            Text(
              subtitle!,
              style: AppTypography.bodySmall.copyWith(
                color: theme.colorScheme.secondary,
              ),
            ),
          ],

          // Gap between header and content
          const SizedBox(height: AppSpacing.md),

          // Content
          child,
        ],
      ),
    );
  }
}
