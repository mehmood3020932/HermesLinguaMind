import 'package:flutter/animation.dart';

/// Motion design tokens for the Aurora Glass design system.
///
/// Never hand-roll a `Duration(milliseconds: ...)` or `Curves.something`
/// directly in a widget — reference these tokens so every animation in the
/// app breathes at the same rhythm.
class AppMotion {
  AppMotion._();

  // === Durations ===
  static const Duration instant = Duration(milliseconds: 120);
  static const Duration fast = Duration(milliseconds: 220);
  static const Duration normal = Duration(milliseconds: 360);
  static const Duration slow = Duration(milliseconds: 560);
  static const Duration ambient = Duration(milliseconds: 4200);
  static const Duration ambientSlow = Duration(milliseconds: 9000);

  // === Curves ===
  /// Snappy, slightly overshooting — for buttons, chips, taps.
  static const Curve punchy = Curves.easeOutBack;

  /// Smooth deceleration — for page content, cards entering.
  static const Curve reveal = Curves.easeOutCubic;

  /// Gentle in-and-out — for glows, breathing effects, ambient loops.
  static const Curve breathe = Curves.easeInOutSine;

  /// Elastic pop — for celebratory / reward moments.
  static const Curve celebrate = Curves.elasticOut;
}
