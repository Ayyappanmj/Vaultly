import 'package:flutter/material.dart';

class AppConstants {
  static const String appName = 'Vaultly';
  static const String apiBaseUrl = 'http://10.0.2.2:8000/api/v1'; // Default Android emulator host

  // Colors
  static const Color primary = Color(0xFF4F46E5); // Indigo 600
  static const Color primaryDark = Color(0xFF3730A3); // Indigo 800
  static const Color background = Color(0xFFF8FAFC); // Slate 50
  static const Color surface = Colors.white;
  static const Color textPrimary = Color(0xFF0F172A); // Slate 900
  static const Color textSecondary = Color(0xFF64748B); // Slate 500
  static const Color border = Color(0xFFE2E8F0); // Slate 200

  // Status Colors
  static const Color statusActive = Color(0xFF10B981); // Emerald 500
  static const Color statusWarning = Color(0xFFF59E0B); // Amber 500
  static const Color statusDanger = Color(0xFFEF4444); // Rose 500
}
