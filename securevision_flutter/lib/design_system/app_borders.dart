import 'package:flutter/material.dart';

/// Swiss Minimalist border system.
/// Strict 1px borders with minimal radii (4px for cards, 30px for pills).
/// No shadows, no gradients - flat design only.
class AppBorders {
  AppBorders._(); // Private constructor to prevent instantiation

  // ========== BORDER WIDTHS ==========

  static const double thin = 1.0;
  static const double medium = 1.5;

  // ========== BORDER RADII ==========

  static const double minimal = 4.0; // Cards, inputs - sharp but friendly
  static const double pill = 30.0; // Pill buttons
  static const double none = 0.0; // Sharp corners

  // ========== PREBUILT BORDERS ==========

  /// Creates a 1px solid border with the specified color.
  static Border border(Color color) => Border.all(
        color: color,
        width: thin,
      );

  /// Creates a 1.5px solid border with the specified color.
  static Border mediumBorder(Color color) => Border.all(
        color: color,
        width: medium,
      );

  // ========== PREBUILT BORDER RADII ==========

  static BorderRadius minimalRadius = BorderRadius.circular(minimal);
  static BorderRadius pillRadius = BorderRadius.circular(pill);
  static BorderRadius sharpRadius = BorderRadius.circular(none);

  // ========== DECORATION BUILDERS ==========

  /// Creates a flat card decoration with 1px border and minimal radius.
  /// NO shadows, NO gradients - strictly flat.
  static BoxDecoration cardDecoration({
    required Color background,
    required Color borderColor,
  }) {
    return BoxDecoration(
      color: background,
      border: border(borderColor),
      borderRadius: minimalRadius,
      // NO shadows, NO gradients
    );
  }

  /// Creates a pill-shaped decoration with 1px border and 30px radius.
  static BoxDecoration pillDecoration({
    required Color background,
    required Color borderColor,
  }) {
    return BoxDecoration(
      color: background,
      border: border(borderColor),
      borderRadius: pillRadius,
    );
  }

  /// Creates a sharp-cornered decoration with 1px border and no radius.
  static BoxDecoration sharpDecoration({
    required Color background,
    required Color borderColor,
  }) {
    return BoxDecoration(
      color: background,
      border: border(borderColor),
      borderRadius: sharpRadius,
    );
  }
}
