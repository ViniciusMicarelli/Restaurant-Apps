import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'application/session_providers.dart';
import 'presentation/screens/pin_login_screen.dart';
import 'presentation/screens/table_map_screen.dart';
import 'presentation/theme/app_theme.dart';

class WaiterApp extends ConsumerWidget {
  const WaiterApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionControllerProvider);

    return MaterialApp(
      title: 'Garçom — Restaurant Apps',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      home: session == null ? const PinLoginScreen() : const TableMapScreen(),
    );
  }
}
