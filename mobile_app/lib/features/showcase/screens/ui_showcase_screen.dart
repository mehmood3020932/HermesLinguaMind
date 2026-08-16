import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/widgets/widgets.dart';

/// Living style guide for the Aurora Glass design system's newest
/// widgets — reachable from Settings → Appearance → "Preview new UI".
/// Not user-facing marketing copy, just a working reference so the team
/// can see every new animated primitive in one place before using them
/// across real screens.
class UiShowcaseScreen extends StatefulWidget {
  const UiShowcaseScreen({super.key});

  @override
  State<UiShowcaseScreen> createState() => _UiShowcaseScreenState();
}

class _UiShowcaseScreenState extends State<UiShowcaseScreen> {
  double _progress = 0.35;

  @override
  Widget build(final BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: AuroraBackground(
        intensity: 0.9,
        child: SafeArea(
          child: ListView(
            padding: EdgeInsets.all(20.w),
            children: [
              Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).maybePop(),
                    icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
                  ),
                  Expanded(
                    child: AnimatedGradientText(
                      'Aurora Glass — New Widgets',
                      style: AppTheme.displayMedium,
                    ),
                  ),
                ],
              ),
              SizedBox(height: 24.h),

              GlassCardPro(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('GlassCardPro', style: AppTheme.headlineLarge),
                    SizedBox(height: 8.h),
                    Text(
                      'A rotating gradient border for hero moments — '
                      'featured lessons, streak cards, companion highlights.',
                      style: AppTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              SizedBox(height: 20.h),

              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('LiquidProgressBar', style: AppTheme.headlineLarge),
                    SizedBox(height: 12.h),
                    LiquidProgressBar(progress: _progress, height: 20.h),
                    SizedBox(height: 12.h),
                    Slider(
                      value: _progress,
                      activeColor: AppTheme.aqua,
                      onChanged: (final v) => setState(() => _progress = v),
                    ),
                  ],
                ),
              ),
              SizedBox(height: 20.h),

              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('PulseGlowButton', style: AppTheme.headlineLarge),
                    SizedBox(height: 12.h),
                    Center(
                      child: PulseGlowButton(
                        label: 'Start Lesson',
                        icon: Icons.play_arrow_rounded,
                        onPressed: () {},
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(height: 20.h),

              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('ParticleBurst', style: AppTheme.headlineLarge),
                    SizedBox(height: 12.h),
                    Text(
                      'Fires once from a tap position — used for streak '
                      'saves, perfect scores, level-ups.',
                      style: AppTheme.bodyMedium,
                    ),
                    SizedBox(height: 12.h),
                    Center(
                      child: Builder(
                        builder: (final btnContext) {
                          return SecondaryButton(
                            label: 'Celebrate 🎉',
                            onPressed: () {
                              final box =
                                  btnContext.findRenderObject() as RenderBox?;
                              final center = box != null
                                  ? box.localToGlobal(
                                      box.size.center(Offset.zero),
                                    )
                                  : const Offset(200, 400);
                              ParticleBurst.fire(btnContext, center: center);
                            },
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(height: 40.h),
            ],
          ),
        ),
      ),
    );
  }
}
