import 'package:flutter/material.dart';
import 'app_colors.dart';
import 'app_typography.dart';
import 'app_borders.dart';
import 'app_spacing.dart';

/// Swiss Minimalist theme configuration for SecureVision.
/// Replaces Material 3 seed-based colors with strict monochrome palette.
class AppTheme {
  AppTheme._(); // Private constructor to prevent instantiation

  /// Light theme with Swiss Minimalist design.
  static ThemeData lightTheme() {
    final textTheme = AppTypography.buildTextTheme();

    return ThemeData(
      useMaterial3: true,

      // ========== COLOR SCHEME (NOT seed-based) ==========
      colorScheme: const ColorScheme.light(
        // Primary: Black for primary actions
        primary: AppColors.jetBlack,
        onPrimary: AppColors.pureWhite,

        // Secondary: Dark grey
        secondary: AppColors.darkGrey,
        onSecondary: AppColors.pureWhite,

        // Tertiary: Medium grey
        tertiary: AppColors.mediumGrey,
        onTertiary: AppColors.pureWhite,

        // Error: Burnt orange (muted)
        error: AppColors.burntOrange,
        onError: AppColors.pureWhite,

        // Surface: Pure white backgrounds
        surface: AppColors.pureWhite,
        onSurface: AppColors.jetBlack,

        // Surface variants
        surfaceContainerHighest: AppColors.offWhite,
        surfaceContainerHigh: AppColors.offWhite,
        surfaceContainer: AppColors.pureWhite,

        // Outline: Light grey borders
        outline: AppColors.lightGrey,
        outlineVariant: AppColors.lightGrey,

        // Shadow: Minimal (barely used)
        shadow: AppColors.transparent,
      ),

      // ========== TYPOGRAPHY ==========
      textTheme: textTheme,

      // ========== COMPONENT THEMES ==========

      // Cards: Flat, 1px border, minimal radius
      cardTheme: CardThemeData(
        color: AppColors.pureWhite,
        elevation: 0, // NO shadow
        shadowColor: AppColors.transparent,
        shape: RoundedRectangleBorder(
          side: const BorderSide(
            color: AppColors.lightGrey,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        margin: EdgeInsets.zero,
      ),

      // Primary Button: Solid black, pill shape
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.jetBlack,
          foregroundColor: AppColors.pureWhite,
          elevation: 0,
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.xl,
            vertical: AppSpacing.md,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: AppBorders.pillRadius,
          ),
          textStyle: AppTypography.labelLarge,
        ),
      ),

      // Secondary Button: Transparent, black border
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.jetBlack,
          backgroundColor: AppColors.transparent,
          elevation: 0,
          side: const BorderSide(
            color: AppColors.jetBlack,
            width: AppBorders.thin,
          ),
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.xl,
            vertical: AppSpacing.md,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: AppBorders.pillRadius,
          ),
          textStyle: AppTypography.labelLarge,
        ),
      ),

      // Text Button: Minimal, no background
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.jetBlack,
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.lg,
            vertical: AppSpacing.sm,
          ),
          textStyle: AppTypography.labelLarge,
        ),
      ),

      // Inputs: Minimal with thin border
      inputDecorationTheme: InputDecorationTheme(
        filled: false,
        fillColor: AppColors.transparent,
        border: OutlineInputBorder(
          borderSide: const BorderSide(
            color: AppColors.lightGrey,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        enabledBorder: OutlineInputBorder(
          borderSide: const BorderSide(
            color: AppColors.lightGrey,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: const BorderSide(
            color: AppColors.jetBlack,
            width: AppBorders.medium,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        errorBorder: OutlineInputBorder(
          borderSide: const BorderSide(
            color: AppColors.burntOrange,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderSide: const BorderSide(
            color: AppColors.burntOrange,
            width: AppBorders.medium,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: AppSpacing.md,
        ),
        labelStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.darkGrey,
        ),
        hintStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.mediumGrey,
        ),
      ),

      // AppBar: Flat, no shadow
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.pureWhite,
        foregroundColor: AppColors.jetBlack,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: AppTypography.headline3.copyWith(
          color: AppColors.jetBlack,
        ),
        iconTheme: const IconThemeData(
          color: AppColors.jetBlack,
        ),
      ),

      // Chips: Flat, 1px border
      chipTheme: ChipThemeData(
        backgroundColor: AppColors.offWhite,
        deleteIconColor: AppColors.darkGrey,
        labelStyle: AppTypography.labelSmall,
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.sm,
          vertical: AppSpacing.xs,
        ),
        shape: RoundedRectangleBorder(
          side: const BorderSide(
            color: AppColors.lightGrey,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        elevation: 0,
        shadowColor: AppColors.transparent,
      ),

      // Scaffold: Pure white, no gradient
      scaffoldBackgroundColor: AppColors.pureWhite,

      // Dividers: 1px grey
      dividerTheme: const DividerThemeData(
        color: AppColors.lightGrey,
        thickness: AppBorders.thin,
        space: 0,
      ),

      // Navigation: Flat, minimal
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: AppColors.pureWhite,
        elevation: 0,
        height: 80,
        indicatorColor: AppColors.offWhite,
        indicatorShape: RoundedRectangleBorder(
          borderRadius: AppBorders.minimalRadius,
        ),
        labelTextStyle: WidgetStateProperty.all(
          AppTypography.labelSmall.copyWith(
            color: AppColors.darkGrey,
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          return IconThemeData(
            color: states.contains(WidgetState.selected)
                ? AppColors.jetBlack
                : AppColors.darkGrey,
          );
        }),
      ),

      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: AppColors.pureWhite,
        elevation: 0,
        indicatorColor: AppColors.offWhite,
        indicatorShape: RoundedRectangleBorder(
          borderRadius: AppBorders.minimalRadius,
        ),
        labelType: NavigationRailLabelType.all,
        selectedIconTheme: const IconThemeData(
          color: AppColors.jetBlack,
        ),
        unselectedIconTheme: const IconThemeData(
          color: AppColors.darkGrey,
        ),
        selectedLabelTextStyle: AppTypography.labelSmall.copyWith(
          color: AppColors.jetBlack,
        ),
        unselectedLabelTextStyle: AppTypography.labelSmall.copyWith(
          color: AppColors.darkGrey,
        ),
      ),

      // Dialog: Flat, bordered
      dialogTheme: DialogThemeData(
        backgroundColor: AppColors.pureWhite,
        elevation: 0,
        shape: RoundedRectangleBorder(
          side: const BorderSide(
            color: AppColors.lightGrey,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        titleTextStyle: AppTypography.headline3.copyWith(
          color: AppColors.jetBlack,
        ),
        contentTextStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.darkGrey,
        ),
      ),

      // Bottom Sheet: Flat, minimal
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: AppColors.pureWhite,
        elevation: 0,
        shape: RoundedRectangleBorder(
          side: BorderSide(
            color: AppColors.lightGrey,
            width: AppBorders.thin,
          ),
          borderRadius: BorderRadius.vertical(
            top: Radius.circular(AppBorders.minimal),
          ),
        ),
      ),

      // Snackbar: Flat, dark
      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.jetBlack,
        contentTextStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.pureWhite,
        ),
        elevation: 0,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: AppBorders.minimalRadius,
        ),
      ),
    );
  }

  /// Dark theme with Swiss Minimalist design.
  static ThemeData darkTheme() {
    final textTheme = AppTypography.buildTextTheme();

    return ThemeData(
      useMaterial3: true,

      // ========== COLOR SCHEME (Dark Mode) ==========
      colorScheme: const ColorScheme.dark(
        // Primary: Almost white for primary actions
        primary: AppColors.almostWhite,
        onPrimary: AppColors.deepCharcoal,

        // Secondary: Light grey
        secondary: AppColors.lightTextGrey,
        onSecondary: AppColors.deepCharcoal,

        // Tertiary: Medium grey
        tertiary: AppColors.mediumGrey,
        onTertiary: AppColors.deepCharcoal,

        // Error: Burnt orange (muted)
        error: AppColors.burntOrangeDark,
        onError: AppColors.deepCharcoal,

        // Surface: Deep charcoal backgrounds
        surface: AppColors.deepCharcoal,
        onSurface: AppColors.almostWhite,

        // Surface variants
        surfaceContainerHighest: AppColors.mediumCharcoal,
        surfaceContainerHigh: AppColors.mediumCharcoal,
        surfaceContainer: AppColors.deepCharcoal,

        // Outline: Border charcoal
        outline: AppColors.borderCharcoal,
        outlineVariant: AppColors.borderCharcoal,

        // Shadow: Minimal
        shadow: AppColors.transparent,
      ),

      // ========== TYPOGRAPHY ==========
      textTheme: textTheme,

      // ========== COMPONENT THEMES ==========
      // Similar to light theme but with dark colors

      cardTheme: CardThemeData(
        color: AppColors.deepCharcoal,
        elevation: 0,
        shadowColor: AppColors.transparent,
        shape: RoundedRectangleBorder(
          side: const BorderSide(
            color: AppColors.borderCharcoal,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        margin: EdgeInsets.zero,
      ),

      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.almostWhite,
          foregroundColor: AppColors.deepCharcoal,
          elevation: 0,
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.xl,
            vertical: AppSpacing.md,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: AppBorders.pillRadius,
          ),
          textStyle: AppTypography.labelLarge,
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.almostWhite,
          backgroundColor: AppColors.transparent,
          elevation: 0,
          side: const BorderSide(
            color: AppColors.almostWhite,
            width: AppBorders.thin,
          ),
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.xl,
            vertical: AppSpacing.md,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: AppBorders.pillRadius,
          ),
          textStyle: AppTypography.labelLarge,
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: false,
        fillColor: AppColors.transparent,
        border: OutlineInputBorder(
          borderSide: const BorderSide(
            color: AppColors.borderCharcoal,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        enabledBorder: OutlineInputBorder(
          borderSide: const BorderSide(
            color: AppColors.borderCharcoal,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: const BorderSide(
            color: AppColors.almostWhite,
            width: AppBorders.medium,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        errorBorder: OutlineInputBorder(
          borderSide: const BorderSide(
            color: AppColors.burntOrangeDark,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: AppSpacing.md,
        ),
        labelStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.lightTextGrey,
        ),
        hintStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.mediumGrey,
        ),
      ),

      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.deepCharcoal,
        foregroundColor: AppColors.almostWhite,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: AppTypography.headline3.copyWith(
          color: AppColors.almostWhite,
        ),
        iconTheme: const IconThemeData(
          color: AppColors.almostWhite,
        ),
      ),

      scaffoldBackgroundColor: AppColors.deepCharcoal,

      dividerTheme: const DividerThemeData(
        color: AppColors.borderCharcoal,
        thickness: AppBorders.thin,
        space: 0,
      ),

      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: AppColors.deepCharcoal,
        elevation: 0,
        height: 80,
        indicatorColor: AppColors.mediumCharcoal,
        indicatorShape: RoundedRectangleBorder(
          borderRadius: AppBorders.minimalRadius,
        ),
        labelTextStyle: WidgetStateProperty.all(
          AppTypography.labelSmall.copyWith(
            color: AppColors.lightTextGrey,
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          return IconThemeData(
            color: states.contains(WidgetState.selected)
                ? AppColors.almostWhite
                : AppColors.lightTextGrey,
          );
        }),
      ),

      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: AppColors.deepCharcoal,
        elevation: 0,
        indicatorColor: AppColors.mediumCharcoal,
        indicatorShape: RoundedRectangleBorder(
          borderRadius: AppBorders.minimalRadius,
        ),
        labelType: NavigationRailLabelType.all,
        selectedIconTheme: const IconThemeData(
          color: AppColors.almostWhite,
        ),
        unselectedIconTheme: const IconThemeData(
          color: AppColors.lightTextGrey,
        ),
        selectedLabelTextStyle: AppTypography.labelSmall.copyWith(
          color: AppColors.almostWhite,
        ),
        unselectedLabelTextStyle: AppTypography.labelSmall.copyWith(
          color: AppColors.lightTextGrey,
        ),
      ),

      dialogTheme: DialogThemeData(
        backgroundColor: AppColors.deepCharcoal,
        elevation: 0,
        shape: RoundedRectangleBorder(
          side: const BorderSide(
            color: AppColors.borderCharcoal,
            width: AppBorders.thin,
          ),
          borderRadius: AppBorders.minimalRadius,
        ),
        titleTextStyle: AppTypography.headline3.copyWith(
          color: AppColors.almostWhite,
        ),
        contentTextStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.lightTextGrey,
        ),
      ),

      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.almostWhite,
        contentTextStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.deepCharcoal,
        ),
        elevation: 0,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: AppBorders.minimalRadius,
        ),
      ),
    );
  }
}
