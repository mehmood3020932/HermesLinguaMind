import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';
import 'package:hermes_linguamind/core/utils/validators.dart';
import 'package:hermes_linguamind/core/widgets/app_text_field.dart';
import 'package:hermes_linguamind/core/widgets/primary_button.dart';
import 'package:hermes_linguamind/features/profile/providers/profile_provider.dart';

class EditProfileScreen extends ConsumerStatefulWidget {
  const EditProfileScreen({super.key});

  @override
  ConsumerState<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends ConsumerState<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _displayNameController;
  late TextEditingController _bioController;

  @override
  void initState() {
    super.initState();
    final user = ref.read(profileProvider).user;
    _displayNameController = TextEditingController(
      text: user?.displayName ?? '',
    );
    _bioController = TextEditingController(text: user?.bio ?? '');
  }

  @override
  void dispose() {
    _displayNameController.dispose();
    _bioController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    await ref
        .read(profileProvider.notifier)
        .updateProfile(
          displayName: _displayNameController.text.trim(),
          bio: _bioController.text.trim(),
        );
    if (mounted) context.pop();
  }

  @override
  Widget build(final BuildContext context) {
    final state = ref.watch(profileProvider);

    return Scaffold(
      backgroundColor: AppTheme.darkBase,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
          onPressed: context.pop,
        ),
        title: Text('Edit Profile', style: AppTheme.headlineLarge),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.all(24.w),
          child: Form(
            key: _formKey,
            child: Column(
              children: [
                Container(
                  width: 100.w,
                  height: 100.h,
                  decoration: BoxDecoration(
                    gradient: AppTheme.primaryGradient,
                    borderRadius: BorderRadius.circular(30.r),
                  ),
                  child: Center(
                    child: Icon(
                      Icons.camera_alt_outlined,
                      size: 32.w,
                      color: AppTheme.textInverse,
                    ),
                  ),
                ),
                SizedBox(height: 32.h),
                AppTextField(
                  controller: _displayNameController,
                  labelText: 'Display Name',
                  hintText: 'Your display name',
                  validator: Validators.displayName,
                  textCapitalization: TextCapitalization.words,
                ),
                SizedBox(height: 16.h),
                AppTextField(
                  controller: _bioController,
                  labelText: 'Bio',
                  hintText: 'Tell us about yourself',
                  maxLines: 4,
                  validator: Validators.bio,
                  textCapitalization: TextCapitalization.sentences,
                ),
                SizedBox(height: 32.h),
                PrimaryButton(
                  label: 'Save Changes',
                  onPressed: _save,
                  isLoading: state.isLoading,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
