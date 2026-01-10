import 'package:flutter/material.dart';

/// Swiss Minimalist button component with primary and secondary variants.
///
/// Primary: Solid black background, white text, 30px pill radius, no elevation
/// Secondary: Transparent background, 1px black border, black text, 30px pill
enum AppButtonVariant {
  /// Solid black button for primary actions.
  primary,

  /// Outlined button for secondary actions.
  secondary,
}

/// A button component following Swiss Minimalist design.
/// Uses Material FilledButton and OutlinedButton styled via theme.
class AppButton extends StatelessWidget {
  const AppButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.variant = AppButtonVariant.primary,
    this.icon,
  });

  /// The button label text.
  final String label;

  /// Callback when button is pressed.
  final VoidCallback? onPressed;

  /// Button variant: primary (solid) or secondary (outlined).
  final AppButtonVariant variant;

  /// Optional icon to display before the label.
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    if (variant == AppButtonVariant.primary) {
      // Primary button: Solid black background
      return icon != null
          ? FilledButton.icon(
              onPressed: onPressed,
              icon: Icon(icon),
              label: Text(label),
            )
          : FilledButton(
              onPressed: onPressed,
              child: Text(label),
            );
    } else {
      // Secondary button: Transparent with black border
      return icon != null
          ? OutlinedButton.icon(
              onPressed: onPressed,
              icon: Icon(icon),
              label: Text(label),
            )
          : OutlinedButton(
              onPressed: onPressed,
              child: Text(label),
            );
    }
  }
}
