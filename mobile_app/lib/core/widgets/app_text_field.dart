import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:hermes_linguamind/core/theme/app_theme.dart';

/// Hermes-styled text input with floating label and icon support.
class AppTextField extends StatelessWidget {
  const AppTextField({
    super.key,
    this.controller,
    this.labelText,
    this.hintText,
    this.helperText,
    this.errorText,
    this.prefixIcon,
    this.suffixIcon,
    this.keyboardType,
    this.textInputAction,
    this.obscureText = false,
    this.maxLines = 1,
    this.minLines,
    this.maxLength,
    this.validator,
    this.onChanged,
    this.onSubmitted,
    this.onTap,
    this.readOnly = false,
    this.enabled = true,
    this.autofocus = false,
    this.focusNode,
    this.textCapitalization = TextCapitalization.none,
    this.inputFormatters,
    this.autocorrect = true,
    this.enableSuggestions = true,
    this.textAlign = TextAlign.start,
  });

  final TextEditingController? controller;
  final String? labelText;
  final String? hintText;
  final String? helperText;
  final String? errorText;
  final Widget? prefixIcon;
  final Widget? suffixIcon;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final bool obscureText;
  final int? maxLines;
  final int? minLines;
  final int? maxLength;
  final String? Function(String?)? validator;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final VoidCallback? onTap;
  final bool readOnly;
  final bool enabled;
  final bool autofocus;
  final FocusNode? focusNode;
  final TextCapitalization textCapitalization;
  final List<TextInputFormatter>? inputFormatters;
  final bool autocorrect;
  final bool enableSuggestions;
  final TextAlign textAlign;

  @override
  Widget build(final BuildContext context) {
    return TextFormField(
      controller: controller,
      focusNode: focusNode,
      decoration: InputDecoration(
        labelText: labelText,
        hintText: hintText,
        helperText: helperText,
        errorText: errorText,
        prefixIcon: prefixIcon != null
            ? Padding(
                padding: EdgeInsets.only(left: 12.w, right: 8.w),
                child: prefixIcon,
              )
            : null,
        suffixIcon: suffixIcon != null
            ? Padding(
                padding: EdgeInsets.only(left: 8.w, right: 12.w),
                child: suffixIcon,
              )
            : null,
        prefixIconConstraints: BoxConstraints(minWidth: 44.w, minHeight: 44.h),
        suffixIconConstraints: BoxConstraints(minWidth: 44.w, minHeight: 44.h),
      ),
      style: AppTheme.bodyLarge,
      keyboardType: keyboardType,
      textInputAction: textInputAction,
      obscureText: obscureText,
      maxLines: maxLines,
      minLines: minLines,
      maxLength: maxLength,
      validator: validator,
      onChanged: onChanged,
      onFieldSubmitted: onSubmitted,
      onTap: onTap,
      readOnly: readOnly,
      enabled: enabled,
      autofocus: autofocus,
      textCapitalization: textCapitalization,
      inputFormatters: inputFormatters,
      autocorrect: autocorrect,
      enableSuggestions: enableSuggestions,
      textAlign: textAlign,
      cursorColor: AppTheme.violet,
      cursorRadius: const Radius.circular(1),
    );
  }
}
