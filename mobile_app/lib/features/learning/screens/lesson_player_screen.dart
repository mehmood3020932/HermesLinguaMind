import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/primary_button.dart';
import 'package:hermes_linguamind/features/learning/providers/learning_provider.dart';

class LessonPlayerScreen extends ConsumerStatefulWidget {
  const LessonPlayerScreen({required this.lessonId, super.key});
  final String lessonId;

  @override
  ConsumerState<LessonPlayerScreen> createState() => _LessonPlayerScreenState();
}

class _LessonPlayerScreenState extends ConsumerState<LessonPlayerScreen> {
  int _currentQuestion = 0;
  int _score = 0;
  bool _answered = false;
  int? _selectedAnswer;

  final List<Map<String, dynamic>> _questions = [
    {
      'type': 'multiple_choice',
      'question': 'How do you say "Hello" in Spanish?',
      'options': ['Hola', 'Bonjour', 'Ciao', 'Hallo'],
      'correct': 0,
    },
    {
      'type': 'multiple_choice',
      'question': 'What does "Gracias" mean?',
      'options': ['Please', 'Thank you', 'Goodbye', 'Sorry'],
      'correct': 1,
    },
    {
      'type': 'multiple_choice',
      'question': 'How do you say "Good morning"?',
      'options': ['Buenas noches', 'Buenos días', 'Buenas tardes', 'Hola'],
      'correct': 1,
    },
  ];

  void _selectAnswer(final int index) {
    if (_answered) return;
    setState(() {
      _selectedAnswer = index;
      _answered = true;
      if (index == _questions[_currentQuestion]['correct']) {
        _score++;
      }
    });
  }

  void _nextQuestion() {
    if (_currentQuestion < _questions.length - 1) {
      setState(() {
        _currentQuestion++;
        _answered = false;
        _selectedAnswer = null;
      });
    } else {
      _completeLesson();
    }
  }

  void _completeLesson() {
    final lessonId = widget.lessonId;
    const unitId = 'unit_1';
    ref.read(learningProvider.notifier).completeLesson(lessonId, unitId);

    context.go(
      AppRoutes.lessonComplete,
      extra: {
        'lessonId': lessonId,
        'xpEarned': _score * 10,
        'coinsEarned': _score * 5,
        'streakDays': 7,
      },
    );
  }

  @override
  Widget build(final BuildContext context) {
    final question = _questions[_currentQuestion];
    final progress = (_currentQuestion + 1) / _questions.length;

    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: AppTheme.textPrimary),
          onPressed: context.pop,
        ),
        title: ClipRRect(
          borderRadius: BorderRadius.circular(4.r),
          child: LinearProgressIndicator(
            value: progress,
            backgroundColor: AppTheme.darkElevated,
            valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.violet),
            minHeight: 8.h,
          ),
        ),
        actions: [
          Padding(
            padding: EdgeInsets.only(right: 16.w),
            child: Center(
              child: Text(
                '${_currentQuestion + 1}/${_questions.length}',
                style: AppTheme.labelMedium,
              ),
            ),
          ),
        ],
      ),
      body: Padding(
        padding: EdgeInsets.all(24.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: EdgeInsets.all(20.w),
              decoration: BoxDecoration(
                color: AppTheme.darkSurface,
                borderRadius: BorderRadius.circular(16.r),
                border: Border.all(color: AppTheme.borderSubtle),
              ),
              child: Text(
                question['question'] as String,
                style: AppTheme.headlineLarge,
              ),
            ),
            SizedBox(height: 32.h),
            Expanded(
              child: ListView.separated(
                itemCount: (question['options'] as List).length,
                separatorBuilder: (_, _) => SizedBox(height: 12.h),
                itemBuilder: (final context, final index) {
                  final option = (question['options'] as List)[index] as String;
                  final isSelected = _selectedAnswer == index;
                  final isCorrect = index == question['correct'];
                  final showResult = _answered;

                  Color borderColor = AppTheme.borderSubtle;
                  Color bgColor = AppTheme.darkSurface;
                  if (showResult) {
                    if (isCorrect) {
                      borderColor = AppTheme.success;
                      bgColor = AppTheme.success.withValues(alpha: 0.1);
                    } else if (isSelected && !isCorrect) {
                      borderColor = AppTheme.error;
                      bgColor = AppTheme.error.withValues(alpha: 0.1);
                    }
                  } else if (isSelected) {
                    borderColor = AppTheme.violet;
                    bgColor = AppTheme.violet.withValues(alpha: 0.1);
                  }

                  return GestureDetector(
                    onTap: () => _selectAnswer(index),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      padding: EdgeInsets.all(16.w),
                      decoration: BoxDecoration(
                        color: bgColor,
                        borderRadius: BorderRadius.circular(12.r),
                        border: Border.all(color: borderColor, width: 2),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 32.w,
                            height: 32.h,
                            decoration: BoxDecoration(
                              color: showResult && isCorrect
                                  ? AppTheme.success
                                  : showResult && isSelected && !isCorrect
                                  ? AppTheme.error
                                  : isSelected
                                  ? AppTheme.violet
                                  : AppTheme.darkElevated,
                              shape: BoxShape.circle,
                            ),
                            child: Center(
                              child: showResult && isCorrect
                                  ? Icon(
                                      Icons.check,
                                      size: 16.w,
                                      color: AppTheme.textInverse,
                                    )
                                  : showResult && isSelected && !isCorrect
                                  ? Icon(
                                      Icons.close,
                                      size: 16.w,
                                      color: AppTheme.textInverse,
                                    )
                                  : Text(
                                      String.fromCharCode(65 + index),
                                      style: AppTheme.labelMedium.copyWith(
                                        color: isSelected
                                            ? AppTheme.textInverse
                                            : AppTheme.textSecondary,
                                      ),
                                    ),
                            ),
                          ),
                          SizedBox(width: 16.w),
                          Expanded(
                            child: Text(option, style: AppTheme.bodyLarge),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            if (_answered)
              PrimaryButton(
                label: _currentQuestion < _questions.length - 1
                    ? 'Next'
                    : 'Complete Lesson',
                onPressed: _nextQuestion,
              ),
            SizedBox(height: 16.h),
          ],
        ),
      ),
    );
  }
}
