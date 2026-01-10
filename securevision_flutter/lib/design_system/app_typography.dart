import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Swiss Minimalist typography scale using Inter font.
/// Hierarchy is achieved via size and weight, not color.
class AppTypography {
  AppTypography._(); // Private constructor to prevent instantiation

  // Base font family - Inter as primary choice
  static String get fontFamily => GoogleFonts.inter().fontFamily!;

  // Alternate option: Uncomment to use Manrope instead
  // static String get fontFamily => GoogleFonts.manrope().fontFamily!;

  // ========== HEADLINES ==========
  // Negative letter spacing for tight, refined headlines

  static final headline1 = TextStyle(
    fontFamily: fontFamily,
    fontSize: 32,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.5,
    height: 1.2,
  );

  static final headline2 = TextStyle(
    fontFamily: fontFamily,
    fontSize: 24,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.5,
    height: 1.3,
  );

  static final headline3 = TextStyle(
    fontFamily: fontFamily,
    fontSize: 20,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.3,
    height: 1.3,
  );

  // ========== BODY TEXT ==========
  // Relaxed line height (1.5) for readability

  static final bodyLarge = TextStyle(
    fontFamily: fontFamily,
    fontSize: 16,
    fontWeight: FontWeight.w400,
    height: 1.5,
  );

  static final bodyMedium = TextStyle(
    fontFamily: fontFamily,
    fontSize: 14,
    fontWeight: FontWeight.w400,
    height: 1.5,
  );

  static final bodySmall = TextStyle(
    fontFamily: fontFamily,
    fontSize: 12,
    fontWeight: FontWeight.w400,
    height: 1.4,
  );

  // ========== LABELS ==========
  // Compact line height for UI elements

  static final labelLarge = TextStyle(
    fontFamily: fontFamily,
    fontSize: 14,
    fontWeight: FontWeight.w500,
    height: 1.2,
  );

  static final labelMedium = TextStyle(
    fontFamily: fontFamily,
    fontSize: 12,
    fontWeight: FontWeight.w500,
    height: 1.2,
  );

  static final labelSmall = TextStyle(
    fontFamily: fontFamily,
    fontSize: 10,
    fontWeight: FontWeight.w500,
    letterSpacing: 0.5, // Uppercase labels
    height: 1.2,
  );

  // ========== HELPERS ==========

  /// Build a complete Material TextTheme from the typography scale.
  static TextTheme buildTextTheme() {
    return TextTheme(
      // Display styles (largest)
      displayLarge: headline1,
      displayMedium: headline2,
      displaySmall: headline3,

      // Headline styles
      headlineLarge: headline1,
      headlineMedium: headline2,
      headlineSmall: headline3,

      // Title styles
      titleLarge: headline3,
      titleMedium: bodyLarge.copyWith(fontWeight: FontWeight.w600),
      titleSmall: bodyMedium.copyWith(fontWeight: FontWeight.w600),

      // Body styles
      bodyLarge: bodyLarge,
      bodyMedium: bodyMedium,
      bodySmall: bodySmall,

      // Label styles
      labelLarge: labelLarge,
      labelMedium: labelMedium,
      labelSmall: labelSmall,
    );
  }
}
