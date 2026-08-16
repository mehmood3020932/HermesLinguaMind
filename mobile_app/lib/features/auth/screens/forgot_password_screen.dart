import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/utils/validators.dart';
import 'package:hermes_linguamind/core/widgets/app_text_field.dart';
import 'package:hermes_linguamind/core/widgets/primary_button.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _sent = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState!.validate()) {
      setState(() => _sent = true);
    }
  }

  @override
  Widget build(final BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
          onPressed: context.pop,
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.all(24.w),
          child: _sent ? _buildSuccess() : _buildForm(),
        ),
      ),
    );
  }

  Widget _buildForm() {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Reset Password', style: AppTheme.displayLarge),
          SizedBox(height: 8.h),
          Text("Enter your email and we'll send you a link to reset your password.", style: AppTheme.bodyMedium),
          SizedBox(height: 32.h),
          AppTextField(
            controller: _emailController,
            labelText: 'Email',
            hintText: 'Enter your email',
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.done,
            prefixIcon: const Icon(Icons.email_outlined, color: AppTheme.textTertiary),
            validator: Validators.email,
            onSubmitted: (_) => _submit(),
          ),
          SizedBox(height: 24.h),
          PrimaryButton(label: 'Send Reset Link', onPressed: _submit),
        ],
      ),
    );
  }

  Widget _buildSuccess() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.mark_email_read_outlined, size: 80.w, color: AppTheme.success),
        SizedBox(height: 24.h),
        Text('Check Your Email', style: AppTheme.headlineLarge, textAlign: TextAlign.center),
        SizedBox(height: 8.h),
        Text(
          "We've sent a password reset link to ${_emailController.text}",
          style: AppTheme.bodyMedium,
          textAlign: TextAlign.center,
        ),
        SizedBox(height: 32.h),
        PrimaryButton(
          label: 'Back to Sign In',
          onPressed: () => context.pop(),
        ),
      ],
    );
  }
}
