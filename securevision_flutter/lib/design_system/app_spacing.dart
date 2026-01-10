/// Swiss Minimalist spacing scale based on a 4px unit.
/// Prevents magic numbers and ensures consistent whitespace throughout the app.
class AppSpacing {
  AppSpacing._(); // Private constructor to prevent instantiation

  // Base unit: 4px
  static const double unit = 4.0;

  // ========== SPACING SCALE ==========

  static const double xs = unit; // 4px
  static const double sm = unit * 2; // 8px
  static const double md = unit * 3; // 12px
  static const double lg = unit * 4; // 16px
  static const double xl = unit * 6; // 24px
  static const double xxl = unit * 8; // 32px
  static const double xxxl = unit * 12; // 48px

  // ========== SEMANTIC ALIASES ==========
  // Named constants for common use cases

  static const double cardPadding = xl; // 24px - padding inside cards
  static const double screenPadding = xl; // 24px - padding on screen edges (aggressive whitespace)
  static const double sectionGap = lg; // 16px - gap between sections
  static const double elementGap = md; // 12px - gap between related elements
  static const double tightGap = sm; // 8px - minimal gap between tight elements
}
