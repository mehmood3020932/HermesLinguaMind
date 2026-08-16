import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/primary_button.dart';

/// Error state widget with retry action.
class ErrorState extends StatelessWidget {
  const ErrorState({
    super.key,
    this.title = 'Something went wrong',
    this.message = "We couldn't load this content. Please try again.",
    this.onRetry,
    this.icon,
  });

  final String title;
  final String message;
  final VoidCallback? onRetry;
  final Widget? icon;

  @override
  Widget build(final BuildContext context) {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(32.w),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            icon ??
                Icon(
                  Icons.error_outline_rounded,
                  size: 64.w,
                  color: AppTheme.textTertiary,
                ),
            SizedBox(height: 16.h),
            Text(
              title,
              style: AppTheme.headlineLarge,
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 8.h),
            Text(
              message,
              style: AppTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            if (onRetry != null) ...[
              SizedBox(height: 24.h),
              PrimaryButton(
                label: 'Try Again',
                onPressed: onRetry,
                width: 200.w,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Empty state widget for lists with no data.
class EmptyState extends StatelessWidget {
  const EmptyState({
    required this.title, super.key,
    this.message,
    this.actionLabel,
    this.onAction,
    this.icon,
  });

  final String title;
  final String? message;
  final String? actionLabel;
  final VoidCallback? onAction;
  final Widget? icon;

  @override
  Widget build(final BuildContext context) {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(32.w),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            icon ??
                Icon(
                  Icons.inbox_outlined,
                  size: 64.w,
                  color: AppTheme.textTertiary,
                ),
            SizedBox(height: 16.h),
            Text(
              title,
              style: AppTheme.headlineLarge,
              textAlign: TextAlign.center,
            ),
            if (message != null) ...[
              SizedBox(height: 8.h),
              Text(
                message!,
                style: AppTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
            ],
            if (actionLabel != null && onAction != null) ...[
              SizedBox(height: 24.h),
              PrimaryButton(
                label: actionLabel!,
                onPressed: onAction,
                width: 200.w,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
