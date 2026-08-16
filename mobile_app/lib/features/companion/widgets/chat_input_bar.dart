import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

class ChatInputBar extends StatefulWidget {
  const ChatInputBar({
    required this.onSend,
    required this.onVoiceStart,
    required this.onVoiceEnd,
    super.key,
  });

  final ValueChanged<String> onSend;
  final VoidCallback onVoiceStart;
  final VoidCallback onVoiceEnd;

  @override
  State<ChatInputBar> createState() => _ChatInputBarState();
}

class _ChatInputBarState extends State<ChatInputBar> {
  final _controller = TextEditingController();
  bool _isRecording = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _send() {
    final text = _controller.text.trim();
    if (text.isNotEmpty) {
      widget.onSend(text);
      _controller.clear();
    }
  }

  @override
  Widget build(final BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
      decoration: const BoxDecoration(
        color: AppTheme.darkElevated,
        border: Border(top: BorderSide(color: AppTheme.borderSubtle)),
      ),
      child: SafeArea(
        child: Row(
          children: [
            GestureDetector(
              onTapDown: (_) {
                setState(() => _isRecording = true);
                widget.onVoiceStart();
              },
              onTapUp: (_) {
                setState(() => _isRecording = false);
                widget.onVoiceEnd();
              },
              onTapCancel: () {
                setState(() => _isRecording = false);
                widget.onVoiceEnd();
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 44.w,
                height: 44.h,
                decoration: BoxDecoration(
                  color: _isRecording
                      ? AppTheme.error.withValues(alpha: 0.2)
                      : AppTheme.darkSurface,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: _isRecording
                        ? AppTheme.error
                        : AppTheme.borderSubtle,
                  ),
                ),
                child: Icon(
                  _isRecording ? Icons.mic : Icons.mic_none,
                  color: _isRecording ? AppTheme.error : AppTheme.textSecondary,
                  size: 22.w,
                ),
              ),
            ),
            SizedBox(width: 12.w),
            Expanded(
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 16.w),
                decoration: BoxDecoration(
                  color: AppTheme.darkSurface,
                  borderRadius: BorderRadius.circular(24.r),
                  border: Border.all(color: AppTheme.borderSubtle),
                ),
                child: TextField(
                  controller: _controller,
                  style: AppTheme.bodyLarge,
                  decoration: InputDecoration(
                    hintText: 'Type a message...',
                    hintStyle: AppTheme.bodyMedium.copyWith(
                      color: AppTheme.textTertiary,
                    ),
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.symmetric(vertical: 12.h),
                  ),
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) => _send(),
                ),
              ),
            ),
            SizedBox(width: 12.w),
            GestureDetector(
              onTap: _send,
              child: Container(
                width: 44.w,
                height: 44.h,
                decoration: const BoxDecoration(
                  gradient: AppTheme.primaryGradient,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.send_rounded,
                  color: AppTheme.textInverse,
                  size: 20.w,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
