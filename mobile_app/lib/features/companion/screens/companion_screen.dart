import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/glass_card.dart';
import 'package:hermes_linguamind/data/models/avatar_models.dart';
import 'package:hermes_linguamind/features/auth/providers/auth_provider.dart';
import 'package:hermes_linguamind/features/companion/providers/avatar_provider.dart';
import 'package:hermes_linguamind/features/companion/widgets/animated_avatar_widget.dart';
import 'package:hermes_linguamind/features/companion/widgets/avatar_video_widget.dart';
import 'package:hermes_linguamind/features/companion/widgets/chat_input_bar.dart';
import 'package:hermes_linguamind/features/companion/widgets/thinking_dots.dart';

class CompanionScreen extends ConsumerStatefulWidget {
  const CompanionScreen({super.key});

  @override
  ConsumerState<CompanionScreen> createState() => _CompanionScreenState();
}

class _CompanionScreenState extends ConsumerState<CompanionScreen> {
  @override
  void initState() {
    super.initState();
    // Kick off the avatar session as soon as the screen opens — there's
    // no separate "start call" step. Tries the real OpenTalking video
    // first, and automatically falls back to the animated lip-synced
    // character if that isn't available (see AvatarNotifier.startSession).
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final avatarState = ref.read(avatarProvider);
      if (avatarState.connectionState == AvatarConnectionState.idle) {
        final authUser = ref.read(authStateProvider).value?.user;
        ref.read(avatarProvider.notifier).startSession(
          'hermes-default',
          userId: authUser?.id ?? 'guest',
          sessionContext: {
            'native_language': authUser?.nativeLanguage ?? 'en',
            'target_language': authUser?.targetLanguage ?? 'en',
            'cefr_level': authUser?.cefrLevel ?? 'A1',
          },
        );
      }
    });
  }

  @override
  void dispose() {
    // Fire-and-forget: tear down the connection and let the backend know
    // the session ended, without blocking navigation.
    ref.read(avatarProvider.notifier).endSession();
    super.dispose();
  }

  @override
  Widget build(final BuildContext context) {
    final avatarState = ref.watch(avatarProvider);

    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              flex: 3,
              child: Center(
                child: Padding(
                  padding: EdgeInsets.all(16.w),
                  child: _buildAvatar(avatarState),
                ),
              ),
            ),
            Expanded(
              flex: 2,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.transparent,
                      AppTheme.darkBase.withValues(alpha: 0.8),
                    ],
                  ),
                ),
                child: ListView.builder(
                  reverse: true,
                  padding: EdgeInsets.symmetric(
                    horizontal: 16.w,
                    vertical: 8.h,
                  ),
                  itemCount: avatarState.transcript.length,
                  itemBuilder: (final context, final index) {
                    final entry = avatarState.transcript[avatarState
                            .transcript
                            .length -
                        1 -
                        index];
                    return _buildMessageBubble(entry);
                  },
                ),
              ),
            ),
            if (avatarState.isSending)
              Padding(
                padding: EdgeInsets.all(16.w),
                child: const ThinkingDots(),
              ),
            if (avatarState.connectionState == AvatarConnectionState.failed)
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 16.w),
                child: GlassCard(
                  padding: EdgeInsets.all(12.w),
                  backgroundColor: AppTheme.error.withValues(alpha: 0.1),
                  borderColor: AppTheme.error.withValues(alpha: 0.3),
                  child: Row(
                    children: [
                      Icon(
                        Icons.error_outline,
                        color: AppTheme.error,
                        size: 20.w,
                      ),
                      SizedBox(width: 8.w),
                      Expanded(
                        child: Text(
                          avatarState.error ?? 'Avatar connection lost',
                          style: AppTheme.bodySmall.copyWith(
                            color: AppTheme.error,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ChatInputBar(
              onSend: (final message) {
                ref.read(avatarProvider.notifier).sendTextMessage(message);
              },
              onVoiceStart: () =>
                  ref.read(avatarProvider.notifier).startVoiceCapture(),
              onVoiceEnd: () =>
                  ref.read(avatarProvider.notifier).stopVoiceCaptureAndSend(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAvatar(final AvatarState avatarState) {
    if (avatarState.renderMode == AvatarRenderMode.animatedFallback) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: AspectRatio(
          aspectRatio: 3 / 4,
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: AppTheme.surfaceGradient,
              border: Border.all(color: AppTheme.borderGlow, width: 1.5),
            ),
            child: AnimatedAvatarWidget(
              viseme: avatarState.currentViseme,
              emotion: avatarState.currentEmotion,
              isListening: avatarState.isListening,
              isSpeaking: avatarState.isSpeaking,
            ),
          ),
        ),
      );
    }

    return AvatarVideoWidget(
      renderer: ref.read(avatarProvider.notifier).webrtcService.remoteRenderer,
      connectionState: avatarState.connectionState,
      characterName: avatarState.session?.character.displayName,
    );
  }

  Widget _buildMessageBubble(final AvatarTranscriptEntry entry) {
    final isUser = entry.isUser;

    return Align(
          alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
          child: Container(
            margin: EdgeInsets.only(
              bottom: 8.h,
              left: isUser ? 48.w : 0,
              right: isUser ? 0 : 48.w,
            ),
            padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
            decoration: BoxDecoration(
              gradient: isUser
                  ? LinearGradient(
                      colors: [
                        AppTheme.violet.withValues(alpha: 0.28),
                        AppTheme.violet.withValues(alpha: 0.12),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    )
                  : null,
              color: isUser ? null : AppTheme.darkSurface,
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(16.r),
                topRight: Radius.circular(16.r),
                bottomLeft: Radius.circular(isUser ? 16.r : 4.r),
                bottomRight: Radius.circular(isUser ? 4.r : 16.r),
              ),
              border: Border.all(
                color: isUser
                    ? AppTheme.violet.withValues(alpha: 0.35)
                    : AppTheme.borderSubtle,
              ),
              boxShadow: isUser
                  ? [
                      BoxShadow(
                        color: AppTheme.violet.withValues(alpha: 0.12),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      ),
                    ]
                  : null,
            ),
            child: Text(
              entry.text,
              style: AppTheme.bodyLarge.copyWith(color: AppTheme.textPrimary),
            ),
          ),
        )
        .animate(key: ValueKey(entry.timestamp.microsecondsSinceEpoch))
        .fadeIn(duration: const Duration(milliseconds: 320))
        .slideY(
          begin: 0.25,
          end: 0,
          duration: const Duration(milliseconds: 320),
          curve: Curves.easeOutCubic,
        )
        .scaleXY(
          begin: 0.94,
          end: 1,
          duration: const Duration(milliseconds: 320),
          curve: Curves.easeOutCubic,
        );
  }
}
