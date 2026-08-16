import 'package:flutter/material.dart';
import 'package:hermes_linguamind/core/theme/app_motion.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// A premium call-to-action button with a slow breathing gradient glow
/// and a punchy scale-down-then-elastic-back tap response. Reserve for
/// the single most important action on a screen (start lesson, claim
/// reward) — using it everywhere would drown out its own emphasis.
class PulseGlowButton extends StatefulWidget {
  const PulseGlowButton({
    required this.label,
    required this.onPressed,
    super.key,
    this.icon,
    this.width,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final double? width;

  @override
  State<PulseGlowButton> createState() => _PulseGlowButtonState();
}

class _PulseGlowButtonState extends State<PulseGlowButton>
    with TickerProviderStateMixin {
  late final AnimationController _glowController;
  late final AnimationController _tapController;
  late final Animation<double> _scaleAnim;

  @override
  void initState() {
    super.initState();
    _glowController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat(reverse: true);

    _tapController = AnimationController(
      vsync: this,
      duration: AppMotion.fast,
      lowerBound: 0.0,
      upperBound: 1.0,
      value: 1.0,
    );
    _scaleAnim = CurvedAnimation(
      parent: _tapController,
      curve: AppMotion.punchy,
    );
  }

  @override
  void dispose() {
    _glowController.dispose();
    _tapController.dispose();
    super.dispose();
  }

  void _onTapDown(final TapDownDetails _) {
    if (widget.onPressed == null) return;
    _tapController.animateTo(0.92, duration: AppMotion.instant);
  }

  void _onTapUp(final TapUpDetails _) {
    if (widget.onPressed == null) return;
    _tapController.animateTo(1.0, curve: AppMotion.punchy);
  }

  void _onTapCancel() {
    _tapController.animateTo(1.0, curve: AppMotion.punchy);
  }

  @override
  Widget build(final BuildContext context) {
    final disabled = widget.onPressed == null;

    return GestureDetector(
      onTapDown: _onTapDown,
      onTapUp: _onTapUp,
      onTapCancel: _onTapCancel,
      onTap: widget.onPressed,
      child: AnimatedBuilder(
        animation: Listenable.merge([_glowController, _tapController]),
        builder: (final context, final _) {
          final glow = disabled ? 0.0 : _glowController.value;
          return Transform.scale(
            scale: _scaleAnim.value,
            child: Container(
              width: widget.width,
              padding: const EdgeInsets.symmetric(
                horizontal: 28,
                vertical: 16,
              ),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                gradient: disabled
                    ? null
                    : AppTheme.primaryGradient,
                color: disabled ? AppTheme.darkSurfaceHover : null,
                boxShadow: disabled
                    ? null
                    : [
                        BoxShadow(
                          color: AppTheme.violet.withValues(
                            alpha: 0.25 + glow * 0.25,
                          ),
                          blurRadius: 16 + glow * 14,
                          spreadRadius: glow * 2,
                        ),
                      ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (widget.icon != null) ...[
                    Icon(
                      widget.icon,
                      color: disabled
                          ? AppTheme.textTertiary
                          : AppTheme.textPrimary,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                  ],
                  Text(
                    widget.label,
                    style: AppTheme.headlineMedium.copyWith(
                      color: disabled
                          ? AppTheme.textTertiary
                          : AppTheme.textPrimary,
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
