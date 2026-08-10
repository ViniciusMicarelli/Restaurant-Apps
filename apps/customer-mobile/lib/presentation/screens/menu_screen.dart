import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../application/providers.dart';
import '../../domain/entities/menu_entities.dart';
import '../widgets/rive/rive_loading_indicator.dart';
import 'product_detail_screen.dart';

class MenuScreen extends ConsumerStatefulWidget {
  const MenuScreen({super.key});

  @override
  ConsumerState<MenuScreen> createState() => _MenuScreenState();
}

class _MenuScreenState extends ConsumerState<MenuScreen> {
  String? _selectedCategoryId;

  @override
  Widget build(BuildContext context) {
    final restaurantAsync = ref.watch(restaurantProvider);
    final categoriesAsync = ref.watch(categoriesProvider);
    final productsAsync = ref.watch(productsProvider);

    return Scaffold(
      appBar: AppBar(
        title: restaurantAsync.when(
          data: (restaurant) => Text(restaurant?.tradeName ?? 'Cardápio'),
          loading: () => const Text('Carregando...'),
          error: (_, _) => const Text('Cardápio'),
        ),
      ),
      body: restaurantAsync.when(
        loading: () => const Center(child: RiveLoadingIndicator()),
        error: (error, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text('Restaurante não encontrado: $error', textAlign: TextAlign.center),
          ),
        ),
        data: (restaurant) {
          if (restaurant == null) {
            return const Center(child: Text('Nenhum restaurante selecionado.'));
          }
          return Column(
            children: [
              categoriesAsync.when(
                loading: () => const LinearProgressIndicator(),
                error: (error, _) => Padding(
                  padding: const EdgeInsets.all(12),
                  child: Text('Falha ao carregar categorias: $error'),
                ),
                data: (categories) => _CategoryChips(
                  categories: categories,
                  selectedCategoryId: _selectedCategoryId,
                  onSelect: (id) => setState(() => _selectedCategoryId = id),
                ),
              ),
              Expanded(
                child: productsAsync.when(
                  loading: () => const Center(child: RiveLoadingIndicator()),
                  error: (error, _) => Center(child: Text('Falha ao carregar produtos: $error')),
                  data: (products) {
                    final filtered = _selectedCategoryId == null
                        ? products
                        : products.where((p) => p.categoryId == _selectedCategoryId).toList();
                    if (filtered.isEmpty) {
                      return const Center(child: Text('Nenhum produto encontrado.'));
                    }
                    return ListView.builder(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      itemCount: filtered.length,
                      itemBuilder: (context, index) => _ProductListTile(product: filtered[index]),
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _CategoryChips extends StatelessWidget {
  const _CategoryChips({
    required this.categories,
    required this.selectedCategoryId,
    required this.onSelect,
  });

  final List<CategoryEntity> categories;
  final String? selectedCategoryId;
  final ValueChanged<String?> onSelect;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 48,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: ChoiceChip(
              label: const Text('Todos'),
              selected: selectedCategoryId == null,
              onSelected: (_) => onSelect(null),
            ),
          ),
          for (final category in categories)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: ChoiceChip(
                label: Text(category.name),
                selected: selectedCategoryId == category.id,
                onSelected: (_) => onSelect(category.id),
              ),
            ),
        ],
      ),
    );
  }
}

class _ProductListTile extends StatelessWidget {
  const _ProductListTile({required this.product});

  final ProductEntity product;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: product.photoUrl.isEmpty
          ? const CircleAvatar(child: Icon(Icons.fastfood))
          : CircleAvatar(backgroundImage: NetworkImage(product.photoUrl)),
      title: Text(product.name, style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text(product.description, maxLines: 1, overflow: TextOverflow.ellipsis),
      trailing: Text(
        'R\$ ${product.price.toStringAsFixed(2)}',
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => ProductDetailScreen(product: product)),
      ),
    );
  }
}
