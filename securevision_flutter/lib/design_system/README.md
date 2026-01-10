# SecureVision Swiss Minimalist Design System

## Overview

This design system implements a strict Swiss Minimalist aesthetic inspired by OpenAI's visual identity. The system prioritizes:

- **Flat surfaces** - No gradients, no shadows
- **Monochrome palette** - Black, white, grey with muted accents
- **Typography hierarchy** - Via size and weight, not color
- **Minimal borders** - 1px solid, 4px radius
- **Generous whitespace** - 24px minimum card padding

## Color Palette

### Light Mode
- **Pure White** (`#FFFFFF`) - Primary surface
- **Off White** (`#F9F9F9`) - Secondary surface
- **Light Grey** (`#E5E5E5`) - Borders
- **Jet Black** (`#000000`) - Primary text
- **Dark Grey** (`#40414F`) - Secondary text
- **Medium Grey** (`#6B6C7E`) - Tertiary text
- **Muted Sage** (`#10A37F`) - Success/positive
- **Burnt Orange** (`#EF4146`) - Error/alert

### Dark Mode
- **Deep Charcoal** (`#202123`) - Primary surface
- **Medium Charcoal** (`#2B2D31`) - Secondary surface
- **Border Charcoal** (`#3E3F45`) - Borders
- **Almost White** (`#ECECF1`) - Primary text
- **Light Grey** (`#B4B4C3`) - Secondary text

## Typography

**Font:** Inter (via Google Fonts)

### Scale
- **headline1**: 32px, weight 600, letter-spacing -0.5
- **headline2**: 24px, weight 600, letter-spacing -0.5
- **headline3**: 20px, weight 600, letter-spacing -0.3
- **bodyLarge**: 16px, weight 400, line-height 1.5
- **bodyMedium**: 14px, weight 400, line-height 1.5
- **bodySmall**: 12px, weight 400, line-height 1.4
- **labelLarge**: 14px, weight 500
- **labelMedium**: 12px, weight 500
- **labelSmall**: 10px, weight 500, letter-spacing 0.5

## Spacing

**Base unit:** 4px

- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 24px (card padding)
- **xxl**: 32px
- **xxxl**: 48px

## Components

### AppCard
Flat card with 1px border and 4px radius.

```dart
AppCard(
  padding: EdgeInsets.all(AppSpacing.cardPadding), // 24px
  borderColor: AppColors.lightGrey,
  onTap: () {}, // Optional
  child: // ...
)
```

### AppButton
Primary (solid black) or secondary (outlined) pill-shaped button.

```dart
AppButton(
  label: 'Submit',
  onPressed: () {},
  variant: AppButtonVariant.primary, // or .secondary
  icon: Icons.check, // Optional
)
```

### AppChip
Minimal badge/tag component.

```dart
AppChip(
  label: 'LIVE',
  color: AppColors.mutedSage, // Optional
)
```

### AppSection
Section container with title, subtitle, and content.

```dart
AppSection(
  title: 'Video Source',
  subtitle: 'Choose device camera or remote stream',
  child: // ...
)
```

## Usage Guidelines

### Do's ✅
- Use AppCard for all card-like surfaces
- Use AppButton for all primary/secondary actions
- Use AppChip for status badges and labels
- Use AppSection for grouped settings/content
- Use 24px minimum padding inside cards
- Use 4px border radius for all rectangular elements
- Use 1px solid borders for all dividers
- Use monochrome colors with sparing accent usage

### Don'ts ❌
- Don't use gradients
- Don't use BoxShadow
- Don't use border radius > 4px (except 30px pills for buttons)
- Don't use bright Material colors (primary, secondary, tertiary)
- Don't use color for text hierarchy (use size/weight instead)
- Don't add elevation to any component
- Don't create inline Container decorations (use components)

## Migration from Material Design

| Material | Swiss Minimalist |
|----------|-----------------|
| `theme.colorScheme.primary` | `AppColors.jetBlack` |
| `theme.colorScheme.secondary` | `AppColors.darkGrey` |
| `theme.colorScheme.tertiary` | `AppColors.mediumGrey` |
| `theme.colorScheme.error` | `AppColors.burntOrange` |
| `theme.colorScheme.surfaceVariant` | `AppColors.offWhite` |
| `theme.colorScheme.onSurfaceVariant` | `AppColors.darkGrey` |
| `FilledButton` | `AppButton(variant: primary)` |
| `OutlinedButton` | `AppButton(variant: secondary)` |
| `Card` with gradient | `AppCard` |
| Inline Container with decoration | `AppCard` |

---

**Last Updated:** 2026-01-10
**Design System Version:** 1.0
**Flutter Version:** 3.x
**Material Design:** 3 (customized)
