import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/constants.dart';
import 'features/auth/login_screen.dart';
import 'features/receipts/receipts_screen.dart';
import 'features/receipts/ocr_review_screen.dart';
import 'features/warranties/warranties_screen.dart';
import 'features/subscriptions/subscriptions_screen.dart';
import 'features/sync/sync_status_screen.dart';

final _router = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/receipts',
      builder: (context, state) => const ReceiptsScreen(),
    ),
    GoRoute(
      path: '/ocr-review',
      builder: (context, state) => const OcrReviewScreen(),
    ),
    GoRoute(
      path: '/warranties',
      builder: (context, state) => const WarrantiesScreen(),
    ),
    GoRoute(
      path: '/subscriptions',
      builder: (context, state) => const SubscriptionsScreen(),
    ),
    GoRoute(
      path: '/sync',
      builder: (context, state) => const SyncStatusScreen(),
    ),
  ],
);

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    const ProviderScope(
      child: VaultlyApp(),
    ),
  );
}

class VaultlyApp extends StatelessWidget {
  const VaultlyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Vaultly',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppConstants.primary,
          surface: AppConstants.background,
        ),
      ),
      routerConfig: _router,
      debugShowCheckedModeBanner: false,
    );
  }
}
