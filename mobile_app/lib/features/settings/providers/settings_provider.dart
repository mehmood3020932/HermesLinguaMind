import 'package:flutter_riverpod/flutter_riverpod.dart';

class AppSettings {
  const AppSettings({
    this.isDarkMode = true,
    this.notificationsEnabled = true,
    this.soundEnabled = true,
    this.hapticsEnabled = true,
    this.autoPlayAudio = true,
    this.fontScale = 1.0,
    this.selectedLanguage = 'en',
  });

  final bool isDarkMode;
  final bool notificationsEnabled;
  final bool soundEnabled;
  final bool hapticsEnabled;
  final bool autoPlayAudio;
  final double fontScale;
  final String selectedLanguage;

  AppSettings copyWith({
    final bool? isDarkMode,
    final bool? notificationsEnabled,
    final bool? soundEnabled,
    final bool? hapticsEnabled,
    final bool? autoPlayAudio,
    final double? fontScale,
    final String? selectedLanguage,
  }) => AppSettings(
    isDarkMode: isDarkMode ?? this.isDarkMode,
    notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
    soundEnabled: soundEnabled ?? this.soundEnabled,
    hapticsEnabled: hapticsEnabled ?? this.hapticsEnabled,
    autoPlayAudio: autoPlayAudio ?? this.autoPlayAudio,
    fontScale: fontScale ?? this.fontScale,
    selectedLanguage: selectedLanguage ?? this.selectedLanguage,
  );
}

class SettingsNotifier extends StateNotifier<AppSettings> {
  SettingsNotifier() : super(const AppSettings());

  void toggleDarkMode({required final bool value}) =>
      state = state.copyWith(isDarkMode: value);
  void toggleNotifications({required final bool value}) =>
      state = state.copyWith(notificationsEnabled: value);
  void toggleSound({required final bool value}) =>
      state = state.copyWith(soundEnabled: value);
  void toggleHaptics({required final bool value}) =>
      state = state.copyWith(hapticsEnabled: value);
  void toggleAutoPlayAudio({required final bool value}) =>
      state = state.copyWith(autoPlayAudio: value);
  void setFontScale(final double value) =>
      state = state.copyWith(fontScale: value);
  void setLanguage(final String value) =>
      state = state.copyWith(selectedLanguage: value);
}

final settingsProvider = StateNotifierProvider<SettingsNotifier, AppSettings>((
  final ref,
) {
  return SettingsNotifier();
});
