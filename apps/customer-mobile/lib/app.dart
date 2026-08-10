import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'application/providers.dart';
import 'presentation/screens/restaurant_selection_screen.dart';
import 'presentation/theme/app_theme.dart';

/// Tema aplicado no `MaterialApp` raiz (não numa tela individual) — assim
/// `MenuScreen` e `ProductDetailScreen` (rotas separadas via `Navigator`)
/// ficam com a MESMA cor de marca, em vez de cada uma herdar um `Theme`
/// diferente. Antes de um restaurante ser selecionado (`restaurantProvider`
/// ainda nulo/carregando), cai no acento padrão do app — cada tenant só
/// sobrescreve depois que o próprio branding carrega.
class CustomerApp extends ConsumerWidget {
  const CustomerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final brandColor = AppTheme.colorFromHex(ref.watch(restaurantProvider).valueOrNull?.primaryColor);

    return MaterialApp(
      title: 'Cardápio Digital — Restaurant Apps',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(primary: brandColor),
      home: const RestaurantSelectionScreen(),
    );
  }
}
