import 'package:flutter/material.dart';

/// Semantic color tokens for Aurora Glass design system.
/// Never use raw hex values directly in widgets — always reference these tokens.
class AppColors {
  AppColors._();

  // === Surface ===
  static const Color surface = Color(0xFF1A1F35);
  static const Color surfaceElevated = Color(0xFF222842);
  static const Color surfacePressed = Color(0xFF2A3050);

  // === Accent ===
  static const Color accentPrimary = Color(0xFF7C5CFF);
  static const Color accentSecondary = Color(0xFF33E6CC);

  // === Status ===
  static const Color accentSuccess = Color(0xFF33E6CC);
  static const Color accentWarning = Color(0xFFFFB347);
  static const Color accentDanger = Color(0xFFFF6B6B);
  static const Color accentInfo = Color(0xFF7C5CFF);

  // === Text ===
  static const Color textPrimary = Color(0xFFF0F2F8);
  static const Color textSecondary = Color(0xFF8B92A8);
  static const Color textMuted = Color(0xFF5A6078);
  static const Color textInverse = Color(0xFF0B0E1A);

  // === Border ===
  static const Color borderDefault = Color(0xFF2A3050);
  static const Color borderFocused = Color(0xFF7C5CFF);
  static const Color borderError = Color(0xFFFF6B6B);

  // === Background ===
  static const Color background = Color(0xFF0B0E1A);
  static const Color backgroundElevated = Color(0xFF14182B);

  // === Overlay ===
  static const Color overlayLight = Color(0x1AFFFFFF);
  static const Color overlayMedium = Color(0x4D000000);
  static const Color overlayHeavy = Color(0x99000000);

  // === Leaderboard Rank Colors ===
  static const Color rankGold = Color(0xFFFFD700);
  static const Color rankSilver = Color(0xFFC0C0C0);
  static const Color rankBronze = Color(0xFFCD7F32);

  // === Character Skin Colors ===
  static const List<Color> characterSkins = [
    Color(0xFF7C5CFF), // Violet (default)
    Color(0xFF33E6CC), // Aqua
    Color(0xFFFF6B6B), // Coral
    Color(0xFFFFB347), // Amber
    Color(0xFF5B8DEF), // Azure
    Color(0xFFFF69B4), // Hot Pink
    Color(0xFF50C878), // Emerald
    Color(0xFFFFA07A), // Salmon
  ];
}
