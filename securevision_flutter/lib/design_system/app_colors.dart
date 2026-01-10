import 'package:flutter/material.dart';

/// Swiss Minimalist color palette for the SecureVision app.
/// Strictly monochrome with muted earthy accents, inspired by OpenAI design.
class AppColors {
  AppColors._(); // Private constructor to prevent instantiation

  // ========== LIGHT MODE ==========

  // Backgrounds
  static const pureWhite = Color(0xFFFFFFFF); // Primary surface
  static const offWhite = Color(0xFFF9F9F9); // Secondary surface
  static const lightGrey = Color(0xFFE5E5E5); // Borders, dividers

  // Text
  static const jetBlack = Color(0xFF000000); // Primary text
  static const darkGrey = Color(0xFF40414F); // Secondary text
  static const mediumGrey = Color(0xFF6B6C7E); // Tertiary text

  // Accents (desaturated)
  static const mutedSage = Color(0xFF10A37F); // Success/positive
  static const burntOrange = Color(0xFFEF4146); // Error/alert
  static const neutralGrey = Color(0xFF8E8EA0); // Neutral badge

  // ========== DARK MODE ==========

  // Backgrounds
  static const deepCharcoal = Color(0xFF202123); // Primary surface
  static const mediumCharcoal = Color(0xFF2B2D31); // Secondary surface
  static const borderCharcoal = Color(0xFF3E3F45); // Borders

  // Text
  static const almostWhite = Color(0xFFECECF1); // Primary text
  static const lightTextGrey = Color(0xFFB4B4C3); // Secondary text

  // Accents (same as light, already muted)
  static const mutedSageDark = Color(0xFF10A37F);
  static const burntOrangeDark = Color(0xFFEF4146);

  // ========== FUNCTIONAL COLORS ==========

  static const transparent = Color(0x00000000);
}
