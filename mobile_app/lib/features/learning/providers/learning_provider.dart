import 'package:flutter_riverpod/flutter_riverpod.dart';

class Lesson {
  const Lesson({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    required this.xpReward,
    required this.coinReward,
    required this.durationMinutes,
    required this.cefrLevel,
    this.isCompleted = false,
    this.isLocked = false,
    this.progress = 0.0,
  });

  final String id;
  final String title;
  final String description;
  final LessonType type;
  final int xpReward;
  final int coinReward;
  final int durationMinutes;
  final String cefrLevel;
  final bool isCompleted;
  final bool isLocked;
  final double progress;

  Lesson copyWith({
    final bool? isCompleted,
    final bool? isLocked,
    final double? progress,
  }) => Lesson(
    id: id,
    title: title,
    description: description,
    type: type,
    xpReward: xpReward,
    coinReward: coinReward,
    durationMinutes: durationMinutes,
    cefrLevel: cefrLevel,
    isCompleted: isCompleted ?? this.isCompleted,
    isLocked: isLocked ?? this.isLocked,
    progress: progress ?? this.progress,
  );
}

enum LessonType { vocabulary, grammar, listening, speaking, reading, writing }

class CurriculumUnit {
  const CurriculumUnit({
    required this.id,
    required this.title,
    required this.description,
    required this.lessons,
    required this.requiredXp,
    this.isUnlocked = false,
  });

  final String id;
  final String title;
  final String description;
  final List<Lesson> lessons;
  final int requiredXp;
  final bool isUnlocked;

  int get completedLessons => lessons.where((final l) => l.isCompleted).length;
  int get totalLessons => lessons.length;
  double get completionRate =>
      totalLessons > 0 ? completedLessons / totalLessons : 0;
}

class LearningState {
  const LearningState({
    this.units = const [],
    this.isLoading = false,
    this.error,
    this.totalXp = 0,
    this.streakDays = 0,
  });

  final List<CurriculumUnit> units;
  final bool isLoading;
  final String? error;
  final int totalXp;
  final int streakDays;

  LearningState copyWith({
    final List<CurriculumUnit>? units,
    final bool? isLoading,
    final String? error,
    final int? totalXp,
    final int? streakDays,
  }) => LearningState(
    units: units ?? this.units,
    isLoading: isLoading ?? this.isLoading,
    error: error,
    totalXp: totalXp ?? this.totalXp,
    streakDays: streakDays ?? this.streakDays,
  );
}

class LearningNotifier extends StateNotifier<LearningState> {
  LearningNotifier() : super(const LearningState()) {
    _loadCurriculum();
  }

  Future<void> _loadCurriculum() async {
    state = state.copyWith(isLoading: true);
    await Future<void>.delayed(const Duration(milliseconds: 800));

    final units = [
      const CurriculumUnit(
        id: 'unit_1',
        title: 'Basics',
        description: 'Foundation vocabulary and greetings',
        isUnlocked: true,
        requiredXp: 0,
        lessons: [
          Lesson(
            id: 'l1_1',
            title: 'Hello & Goodbye',
            description: 'Learn basic greetings',
            type: LessonType.vocabulary,
            xpReward: 10,
            coinReward: 5,
            durationMinutes: 5,
            cefrLevel: 'A1',
            isCompleted: true,
          ),
          Lesson(
            id: 'l1_2',
            title: 'Numbers 1-20',
            description: 'Count from one to twenty',
            type: LessonType.vocabulary,
            xpReward: 15,
            coinReward: 5,
            durationMinutes: 8,
            cefrLevel: 'A1',
          ),
          Lesson(
            id: 'l1_3',
            title: 'Introduce Yourself',
            description: 'Tell others who you are',
            type: LessonType.speaking,
            xpReward: 20,
            coinReward: 10,
            durationMinutes: 10,
            cefrLevel: 'A1',
          ),
        ],
      ),
      const CurriculumUnit(
        id: 'unit_2',
        title: 'Daily Life',
        description: 'Common phrases for everyday situations',
        isUnlocked: true,
        requiredXp: 45,
        lessons: [
          Lesson(
            id: 'l2_1',
            title: 'At the Cafe',
            description: 'Order food and drinks',
            type: LessonType.listening,
            xpReward: 15,
            coinReward: 5,
            durationMinutes: 8,
            cefrLevel: 'A1',
          ),
          Lesson(
            id: 'l2_2',
            title: 'Directions',
            description: 'Ask for and give directions',
            type: LessonType.vocabulary,
            xpReward: 20,
            coinReward: 10,
            durationMinutes: 10,
            cefrLevel: 'A1',
          ),
          Lesson(
            id: 'l2_3',
            title: 'Shopping',
            description: 'Buy things at a store',
            type: LessonType.speaking,
            xpReward: 25,
            coinReward: 10,
            durationMinutes: 12,
            cefrLevel: 'A1',
          ),
          Lesson(
            id: 'l2_4',
            title: 'Time & Schedule',
            description: 'Talk about appointments',
            type: LessonType.grammar,
            xpReward: 20,
            coinReward: 10,
            durationMinutes: 10,
            cefrLevel: 'A1',
          ),
        ],
      ),
      const CurriculumUnit(
        id: 'unit_3',
        title: 'Travel',
        description: 'Navigate airports, hotels, and transport',
        requiredXp: 125,
        lessons: [
          Lesson(
            id: 'l3_1',
            title: 'At the Airport',
            description: 'Check-in and boarding',
            type: LessonType.listening,
            xpReward: 25,
            coinReward: 10,
            durationMinutes: 12,
            cefrLevel: 'A2',
          ),
          Lesson(
            id: 'l3_2',
            title: 'Hotel Check-in',
            description: 'Book and check into hotels',
            type: LessonType.speaking,
            xpReward: 30,
            coinReward: 15,
            durationMinutes: 15,
            cefrLevel: 'A2',
          ),
          Lesson(
            id: 'l3_3',
            title: 'Public Transport',
            description: 'Buy tickets and ask routes',
            type: LessonType.vocabulary,
            xpReward: 20,
            coinReward: 10,
            durationMinutes: 10,
            cefrLevel: 'A2',
          ),
        ],
      ),
    ];

    state = state.copyWith(
      units: units,
      isLoading: false,
      totalXp: 45,
      streakDays: 7,
    );
  }

  void completeLesson(final String lessonId, final String unitId) {
    final updatedUnits = state.units.map((final unit) {
      if (unit.id == unitId) {
        final updatedLessons = unit.lessons.map((final lesson) {
          if (lesson.id == lessonId) {
            return lesson.copyWith(isCompleted: true, progress: 1);
          }
          return lesson;
        }).toList();
        return CurriculumUnit(
          id: unit.id,
          title: unit.title,
          description: unit.description,
          lessons: updatedLessons,
          requiredXp: unit.requiredXp,
          isUnlocked: unit.isUnlocked,
        );
      }
      return unit;
    }).toList();

    state = state.copyWith(units: updatedUnits);
  }
}

final learningProvider = StateNotifierProvider<LearningNotifier, LearningState>(
  (final ref) => LearningNotifier(),
);
