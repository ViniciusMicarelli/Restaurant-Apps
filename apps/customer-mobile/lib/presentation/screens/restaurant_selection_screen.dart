import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../application/providers.dart';
import 'menu_screen.dart';

/// Tela inicial: o cliente informa o código (`slug`) do restaurante — na
/// prática, viria de um QR Code/deep link por mesa; aqui, entrada manual
/// (escopo Tier B — base sólida, sem leitor de QR Code nesta fase).
class RestaurantSelectionScreen extends ConsumerStatefulWidget {
  const RestaurantSelectionScreen({super.key});

  @override
  ConsumerState<RestaurantSelectionScreen> createState() => _RestaurantSelectionScreenState();
}

class _RestaurantSelectionScreenState extends ConsumerState<RestaurantSelectionScreen> {
  final _slugController = TextEditingController();

  @override
  void dispose() {
    _slugController.dispose();
    super.dispose();
  }

  void _openMenu() {
    final slug = _slugController.text.trim();
    if (slug.isEmpty) return;

    ref.read(restaurantSlugProvider.notifier).state = slug;
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const MenuScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.restaurant_menu, size: 56, color: Color(0xFFDC2626)),
              const SizedBox(height: 16),
              const Text(
                'Cardápio Digital',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              const Text(
                'Informe o código do restaurante para ver o cardápio.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13, color: Colors.grey),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: _slugController,
                decoration: const InputDecoration(
                  labelText: 'Código do restaurante',
                  hintText: 'ex: restaurante-demo',
                  border: OutlineInputBorder(),
                ),
                onSubmitted: (_) => _openMenu(),
              ),
              const SizedBox(height: 16),
              FilledButton(onPressed: _openMenu, child: const Text('Ver Cardápio')),
            ],
          ),
        ),
      ),
    );
  }
}
