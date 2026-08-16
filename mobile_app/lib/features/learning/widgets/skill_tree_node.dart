import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/features/learning/providers/learning_provider.dart';

class SkillTreeNode extends StatelessWidget {
  const SkillTreeNode({required this.lesson, super.key, this.onTap});

  final Lesson lesson;
  final VoidCallback? onTap;

  IconData get _lessonIcon {
    switch (lesson.type) {
      case LessonType.vocabulary:
        return Icons.book_outlined;
      case LessonType.grammar:
        return Icons.menu_book_outlined;
      case LessonType.listening:
        return Icons.headphones_outlined;
      case LessonType.speaking:
        return Icons.mic_outlined;
      case LessonType.reading:
        return Icons.article_outlined;
      case LessonType.writing:
        return Icons.edit_outlined;
    }
  }

  Color get _lessonColor {
    switch (lesson.type) {
      case LessonType.vocabulary:
        return AppTheme.violet;
      case LessonType.grammar:
        return AppTheme.aqua;
      case LessonType.listening:
        return const Color(0xFF5B8DEF);
      case LessonType.speaking:
        return AppTheme.success;
      case LessonType.reading:
        return const Color(0xFFFFB347);
      case LessonType.writing:
        return const Color(0xFFFF69B4);
    }
  }

  @override
  Widget build(final BuildContext context) {
    final isCompleted = lesson.isCompleted;
    final canStart = onTap != null;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 80.w,
        padding: EdgeInsets.all(12.w),
        decoration: BoxDecoration(
          color: isCompleted
              ? _lessonColor.withValues(alpha: 0.15)
              : canStart
              ? AppTheme.darkSurface
              : AppTheme.darkElevated,
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(
            color: isCompleted
                ? _lessonColor
                : canStart
                ? AppTheme.borderSubtle
                : Colors.transparent,
            width: isCompleted ? 2 : 1,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 40.w,
              height: 40.h,
              decoration: BoxDecoration(
                color: isCompleted
                    ? _lessonColor
                    : _lessonColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12.r),
              ),
              child: Icon(
                isCompleted ? Icons.check_rounded : _lessonIcon,
                color: isCompleted ? AppTheme.textInverse : _lessonColor,
                size: 20.w,
              ),
            ),
            SizedBox(height: 8.h),
            Text(
              lesson.title,
              style: AppTheme.labelSmall.copyWith(
                color: canStart ? AppTheme.textPrimary : AppTheme.textTertiary,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            SizedBox(height: 4.h),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.star_rounded, size: 10.w, color: AppTheme.warning),
                SizedBox(width: 2.w),
                Text(
                  '${lesson.xpReward}',
                  style: AppTheme.labelSmall.copyWith(fontSize: 9.sp),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
