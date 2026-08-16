import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:shimmer/shimmer.dart';

/// Shimmer loading placeholder with Aurora Glass styling.
class LoadingShimmer extends StatelessWidget {
  const LoadingShimmer({
    super.key,
    this.width,
    this.height,
    this.borderRadius,
    this.child,
  });

  final double? width;
  final double? height;
  final double? borderRadius;
  final Widget? child;

  @override
  Widget build(final BuildContext context) {
    return Shimmer.fromColors(
      baseColor: AppTheme.darkElevated,
      highlightColor: AppTheme.darkSurfaceHover,
      child: Container(
        width: width ?? double.infinity,
        height: height ?? 16.h,
        decoration: BoxDecoration(
          color: AppTheme.darkElevated,
          borderRadius: BorderRadius.circular(borderRadius ?? 8.r),
        ),
        child: child,
      ),
    );
  }
}

/// Card-shaped shimmer placeholder.
class CardShimmer extends StatelessWidget {
  const CardShimmer({super.key, this.height, this.margin});

  final double? height;
  final EdgeInsetsGeometry? margin;

  @override
  Widget build(final BuildContext context) {
    return LoadingShimmer(
      height: height ?? 120.h,
      borderRadius: 16.r,
      child: Container(
        margin: margin ?? EdgeInsets.symmetric(vertical: 8.h, horizontal: 16.w),
      ),
    );
  }
}

/// List of shimmer placeholders.
class ListShimmer extends StatelessWidget {
  const ListShimmer({
    super.key,
    this.itemCount = 5,
    this.itemHeight,
    this.padding,
  });

  final int itemCount;
  final double? itemHeight;
  final EdgeInsetsGeometry? padding;

  @override
  Widget build(final BuildContext context) {
    return ListView.builder(
      padding: padding ?? EdgeInsets.symmetric(vertical: 8.h),
      itemCount: itemCount,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemBuilder: (final context, final index) {
        return CardShimmer(height: itemHeight);
      },
    );
  }
}
