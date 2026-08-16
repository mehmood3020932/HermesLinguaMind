import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

/// Aurora Glass Design System
/// Dark base #0B0E1A, duotone accents violet #7C5CFF + aqua #33E6CC
class AppTheme {
  AppTheme._();

  // === Base Colors ===
  static const Color darkBase = Color(0xFF0B0E1A);
  static const Color darkElevated = Color(0xFF14182B);
  static const Color darkSurface = Color(0xFF1A1F35);
  static const Color darkSurfaceHover = Color(0xFF222842);

  // === Accent Colors ===
  static const Color violet = Color(0xFF7C5CFF);
  static const Color violetLight = Color(0xFF9B82FF);
  static const Color violetDark = Color(0xFF5A3FD6);
  static const Color aqua = Color(0xFF33E6CC);
  static const Color aquaLight = Color(0xFF5EEDDA);
  static const Color aquaDark = Color(0xFF20B8A3);

  // === Semantic Colors ===
  static const Color success = Color(0xFF33E6CC);
  static const Color warning = Color(0xFFFFB347);
  static const Color error = Color(0xFFFF6B6B);
  static const Color info = Color(0xFF7C5CFF);

  // === Text Colors ===
  static const Color textPrimary = Color(0xFFF0F2F8);
  static const Color textSecondary = Color(0xFF8B92A8);
  static const Color textTertiary = Color(0xFF5A6078);
  static const Color textInverse = Color(0xFF0B0E1A);

  // === Border & Divider ===
  static const Color borderSubtle = Color(0xFF2A3050);
  static const Color borderGlow = Color(0x337C5CFF);
  static const Color divider = Color(0xFF1E2340);

  // === Overlay ===
  static const Color overlay = Color(0xCC0B0E1A);
  static const Color scrim = Color(0x990B0E1A);

  // === Gradients ===
  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [violet, aqua],
  );

  static const LinearGradient surfaceGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [darkElevated, darkBase],
  );

  static const LinearGradient glowGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0x1A7C5CFF), Colors.transparent],
  );

  // === Typography ===
  static TextStyle displayLarge = TextStyle(
    fontFamily: 'SpaceGrotesk',
    fontSize: 40.sp,
    fontWeight: FontWeight.w700,
    color: textPrimary,
    letterSpacing: -0.5,
    height: 1.2,
  );

  static TextStyle displayMedium = TextStyle(
    fontFamily: 'SpaceGrotesk',
    fontSize: 28.sp,
    fontWeight: FontWeight.w700,
    color: textPrimary,
    letterSpacing: -0.3,
    height: 1.2,
  );

  static TextStyle headlineLarge = TextStyle(
    fontFamily: 'SpaceGrotesk',
    fontSize: 20.sp,
    fontWeight: FontWeight.w600,
    color: textPrimary,
    letterSpacing: -0.2,
    height: 1.3,
  );

  static TextStyle headlineMedium = TextStyle(
    fontFamily: 'SpaceGrotesk',
    fontSize: 18.sp,
    fontWeight: FontWeight.w600,
    color: textPrimary,
    height: 1.3,
  );

  static TextStyle bodyLarge = TextStyle(
    fontFamily: 'Inter',
    fontSize: 16.sp,
    fontWeight: FontWeight.w400,
    color: textPrimary,
    height: 1.5,
  );

  static TextStyle bodyMedium = TextStyle(
    fontFamily: 'Inter',
    fontSize: 14.sp,
    fontWeight: FontWeight.w400,
    color: textSecondary,
    height: 1.5,
  );

  static TextStyle bodySmall = TextStyle(
    fontFamily: 'Inter',
    fontSize: 12.sp,
    fontWeight: FontWeight.w400,
    color: textTertiary,
    height: 1.4,
  );

  static TextStyle labelLarge = TextStyle(
    fontFamily: 'Inter',
    fontSize: 14.sp,
    fontWeight: FontWeight.w600,
    color: textPrimary,
    letterSpacing: 0.5,
    height: 1.2,
  );

  static TextStyle labelMedium = TextStyle(
    fontFamily: 'Inter',
    fontSize: 12.sp,
    fontWeight: FontWeight.w500,
    color: textSecondary,
    letterSpacing: 0.5,
    height: 1.2,
  );

  static TextStyle labelSmall = TextStyle(
    fontFamily: 'Inter',
    fontSize: 10.sp,
    fontWeight: FontWeight.w500,
    color: textTertiary,
    letterSpacing: 0.5,
    height: 1.2,
  );

  // === Theme Data ===
  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBase,
      colorScheme: const ColorScheme.dark(
        primary: violet,
        secondary: aqua,
        surface: darkSurface,
        error: error,
        onPrimary: textInverse,
        onSecondary: textInverse,
        onSurface: textPrimary,
        onError: textInverse,
      ),
      textTheme: TextTheme(
        displayLarge: displayLarge,
        displayMedium: displayMedium,
        headlineLarge: headlineLarge,
        headlineMedium: headlineMedium,
        bodyLarge: bodyLarge,
        bodyMedium: bodyMedium,
        bodySmall: bodySmall,
        labelLarge: labelLarge,
        labelMedium: labelMedium,
        labelSmall: labelSmall,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: darkBase.withValues(alpha: 0.8),
        elevation: 0,
        centerTitle: true,
        titleTextStyle: headlineLarge,
        systemOverlayStyle: SystemUiOverlayStyle.light,
        iconTheme: const IconThemeData(color: textPrimary),
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: darkElevated,
        selectedItemColor: violet,
        unselectedItemColor: textTertiary,
        selectedLabelStyle: labelSmall,
        unselectedLabelStyle: labelSmall,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
      cardTheme: CardThemeData(
        color: darkSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16.r),
          side: const BorderSide(color: borderSubtle),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: darkElevated,
        contentPadding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12.r),
          borderSide: const BorderSide(color: borderSubtle),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12.r),
          borderSide: const BorderSide(color: borderSubtle),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12.r),
          borderSide: const BorderSide(color: violet, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12.r),
          borderSide: const BorderSide(color: error),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12.r),
          borderSide: const BorderSide(color: error, width: 2),
        ),
        labelStyle: bodyMedium,
        hintStyle: bodyMedium.copyWith(color: textTertiary),
        errorStyle: bodySmall.copyWith(color: error),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: violet,
          foregroundColor: textInverse,
          elevation: 0,
          padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 14.h),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12.r),
          ),
          textStyle: labelLarge,
          minimumSize: Size(double.infinity, 48.h),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: violet,
          side: const BorderSide(color: violet),
          padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 14.h),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12.r),
          ),
          textStyle: labelLarge,
          minimumSize: Size(double.infinity, 48.h),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: aqua,
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
          textStyle: labelMedium.copyWith(color: aqua),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: darkElevated,
        selectedColor: violet.withValues(alpha: 0.2),
        labelStyle: labelMedium,
        secondaryLabelStyle: labelMedium.copyWith(color: violet),
        padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20.r),
          side: const BorderSide(color: borderSubtle),
        ),
      ),
      dividerTheme: const DividerThemeData(
        color: divider,
        thickness: 1,
        space: 1,
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: darkSurface,
        contentTextStyle: bodyMedium,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12.r),
        ),
        behavior: SnackBarBehavior.floating,
        elevation: 4,
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: darkSurface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20.r),
        ),
        elevation: 8,
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: darkSurface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20.r)),
        ),
        elevation: 8,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((final states) {
          if (states.contains(WidgetState.selected)) return violet;
          return textTertiary;
        }),
        trackColor: WidgetStateProperty.resolveWith((final states) {
          if (states.contains(WidgetState.selected)) {
            return violet.withValues(alpha: 0.3);
          }
          return darkElevated;
        }),
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: violet,
        inactiveTrackColor: darkElevated,
        thumbColor: violet,
        overlayColor: violet.withValues(alpha: 0.2),
        trackHeight: 4.h,
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: violet,
        linearTrackColor: darkElevated,
        circularTrackColor: darkElevated,
      ),
      scrollbarTheme: ScrollbarThemeData(
        thumbColor: WidgetStateProperty.all(
          textTertiary.withValues(alpha: 0.5),
        ),
        trackColor: WidgetStateProperty.all(Colors.transparent),
        radius: Radius.circular(8.r),
        thickness: WidgetStateProperty.all(4.w),
      ),
    );
  }
}
