import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/constants/app_routes.dart';
import 'package:hermes_linguamind/core/constants/demo_credentials.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/utils/validators.dart';
import 'package:hermes_linguamind/core/widgets/app_text_field.dart';
import 'package:hermes_linguamind/core/widgets/primary_button.dart';
import 'package:hermes_linguamind/core/widgets/secondary_button.dart';
import 'package:hermes_linguamind/features/auth/providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    await ref
        .read(authStateProvider.notifier)
        .login(_emailController.text.trim(), _passwordController.text);
  }

  @override
  Widget build(final BuildContext context) {
    final authState = ref.watch(authStateProvider);

    ref.listen(authStateProvider, (_, final next) {
      next.whenOrNull(
        data: (final state) {
          if (state.isAuthenticated) {
            context.go(AppRoutes.home);
          }
        },
      );
    });

    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.all(24.w),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(height: 48.h),
                Text('Welcome Back', style: AppTheme.displayLarge),
                SizedBox(height: 8.h),
                Text(
                  'Sign in to continue your journey',
                  style: AppTheme.bodyMedium,
                ),
                SizedBox(height: 48.h),
                AppTextField(
                  controller: _emailController,
                  labelText: 'Email',
                  hintText: 'Enter your email',
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  prefixIcon: const Icon(
                    Icons.email_outlined,
                    color: AppTheme.textTertiary,
                  ),
                  validator: Validators.email,
                  autocorrect: false,
                ),
                SizedBox(height: 16.h),
                AppTextField(
                  controller: _passwordController,
                  labelText: 'Password',
                  hintText: 'Enter your password',
                  obscureText: _obscurePassword,
                  textInputAction: TextInputAction.done,
                  prefixIcon: const Icon(
                    Icons.lock_outline,
                    color: AppTheme.textTertiary,
                  ),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                      color: AppTheme.textTertiary,
                    ),
                    onPressed: () =>
                        setState(() => _obscurePassword = !_obscurePassword),
                  ),
                  validator: Validators.password,
                  onSubmitted: (_) => _login(),
                ),
                SizedBox(height: 12.h),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () => context.push(AppRoutes.forgotPassword),
                    child: Text(
                      'Forgot Password?',
                      style: AppTheme.labelMedium.copyWith(
                        color: AppTheme.aqua,
                      ),
                    ),
                  ),
                ),
                SizedBox(height: 24.h),
                if (authState.hasError)
                  Container(
                    padding: EdgeInsets.all(12.w),
                    decoration: BoxDecoration(
                      color: AppTheme.error.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12.r),
                      border: Border.all(
                        color: AppTheme.error.withValues(alpha: 0.3),
                      ),
                    ),
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
                            authState.error.toString(),
                            style: AppTheme.bodyMedium.copyWith(
                              color: AppTheme.error,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                SizedBox(height: 24.h),
                PrimaryButton(
                  label: 'Sign In',
                  onPressed: _login,
                  isLoading: authState.isLoading,
                ),
                SizedBox(height: 24.h),
                Row(
                  children: [
                    const Expanded(
                      child: Divider(color: AppTheme.borderSubtle),
                    ),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 16.w),
                      child: Text(
                        'or',
                        style: AppTheme.bodyMedium.copyWith(
                          color: AppTheme.textTertiary,
                        ),
                      ),
                    ),
                    const Expanded(
                      child: Divider(color: AppTheme.borderSubtle),
                    ),
                  ],
                ),
                SizedBox(height: 24.h),
                SecondaryButton(
                  label: 'Create Account',
                  onPressed: () => context.push(AppRoutes.register),
                ),
                SizedBox(height: 12.h),
                Center(
                  child: TextButton.icon(
                    onPressed: () {
                      _emailController.text = DemoCredentials.email;
                      _passwordController.text = DemoCredentials.password;
                    },
                    icon: const Icon(
                      Icons.rocket_launch_outlined,
                      size: 18,
                      color: AppTheme.textSecondary,
                    ),
                    label: Text(
                      'Fill demo account (see DEMO_CREDENTIALS.md)',
                      style: AppTheme.labelMedium.copyWith(
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
