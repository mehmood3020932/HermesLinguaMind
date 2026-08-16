import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// String extensions
extension StringX on String {
  String get capitalize {
    if (isEmpty) return this;
    return '${this[0].toUpperCase()}${substring(1)}';
  }

  String get titleCase {
    return split(' ').map((final word) => word.capitalize).join(' ');
  }

  String get truncateEllipsis {
    if (length <= 20) return this;
    return '${substring(0, 17)}...';
  }

  bool get isValidEmail {
    final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    return emailRegex.hasMatch(this);
  }

  bool get isStrongPassword {
    if (length < 8) return false;
    final hasUpper = contains(RegExp('[A-Z]'));
    final hasLower = contains(RegExp('[a-z]'));
    final hasDigit = contains(RegExp('[0-9]'));
    final hasSpecial = contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'));
    return hasUpper && hasLower && hasDigit && hasSpecial;
  }
}

/// DateTime extensions
extension DateTimeX on DateTime {
  String get formattedDate => DateFormat('MMM d, y').format(this);
  String get formattedTime => DateFormat('h:mm a').format(this);
  String get formattedDateTime => DateFormat('MMM d, y • h:mm a').format(this);
  String get relativeTime {
    final now = DateTime.now();
    final diff = now.difference(this);

    if (diff.inSeconds < 60) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    if (diff.inDays < 30) return '${(diff.inDays / 7).floor()}w ago';
    if (diff.inDays < 365) return '${(diff.inDays / 30).floor()}mo ago';
    return '${(diff.inDays / 365).floor()}y ago';
  }

  bool get isToday {
    final now = DateTime.now();
    return year == now.year && month == now.month && day == now.day;
  }

  bool get isYesterday {
    final yesterday = DateTime.now().subtract(const Duration(days: 1));
    return year == yesterday.year &&
        month == yesterday.month &&
        day == yesterday.day;
  }
}

/// Duration extensions
extension DurationX on Duration {
  String get formatted {
    final minutes = inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = inSeconds.remainder(60).toString().padLeft(2, '0');
    if (inHours > 0) {
      final hours = inHours.toString().padLeft(2, '0');
      return '$hours:$minutes:$seconds';
    }
    return '$minutes:$seconds';
  }
}

/// Number extensions
extension NumberX on num {
  String get compact {
    if (this >= 1000000) return '${(this / 1000000).toStringAsFixed(1)}M';
    if (this >= 1000) return '${(this / 1000).toStringAsFixed(1)}K';
    return toString();
  }

  String get ordinal {
    if (this == 11 || this == 12 || this == 13) return '${this}th';
    switch (this % 10) {
      case 1:
        return '${this}st';
      case 2:
        return '${this}nd';
      case 3:
        return '${this}rd';
      default:
        return '${this}th';
    }
  }
}

/// BuildContext extensions
extension BuildContextX on BuildContext {
  ThemeData get theme => Theme.of(this);
  ColorScheme get colors => Theme.of(this).colorScheme;
  TextTheme get textTheme => Theme.of(this).textTheme;
  Size get screenSize => MediaQuery.of(this).size;
  EdgeInsets get padding => MediaQuery.of(this).padding;
  double get screenWidth => MediaQuery.of(this).size.width;
  double get screenHeight => MediaQuery.of(this).size.height;
}
