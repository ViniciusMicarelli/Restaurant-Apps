import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../application/api_providers.dart';
import '../../application/cart_providers.dart';
import '../../application/menu_providers.dart';
import '../../data/api/api_exception.dart';
import '../../domain/entities/cart.dart';
import '../../domain/entities/menu_entities.dart';
import '../../domain/entities/table_entity.dart';
import '../widgets/rive/rive_loading_indicator.dart';
import '../widgets/rive/rive_payment_reward.dart';

/// Monta o pedido de uma mesa a partir do cardápio e envia à cozinha
/// (US-04.1) — cria o pedido no `order-service`, que dispara a Saga
/// (`order.created`) para o `kitchen-service` popular o KDS automaticamente.
class BuildOrderScreen extends ConsumerStatefulWidget {
  const BuildOrderScreen({super.key, required this.table, this.commandId});

  final TableEntity table;

  /// Comanda aberta desta mesa — vincula o pedido a ela (Fase C: faturamento
  /// soma pedidos por comanda). `null` só deveria acontecer se a comanda não
  /// foi encontrada (estado inconsistente entre mesa `OCCUPIED` e a lista de
  /// comandas abertas) — o pedido ainda é aceito, só fica sem vínculo.
  final String? commandId;

  @override
  ConsumerState<BuildOrderScreen> createState() => _BuildOrderScreenState();
}

class _BuildOrderScreenState extends ConsumerState<BuildOrderScreen> {
  String? _selectedCategoryId;
  bool _isSubmitting = false;

  @override
  Widget build(BuildContext context) {
    final categoriesAsync = ref.watch(categoriesProvider);
    final productsAsync = ref.watch(productsProvider);
    final cart = ref.watch(cartControllerProvider(widget.table.id));
    final cartController = ref.read(cartControllerProvider(widget.table.id).notifier);

    return Scaffold(
      appBar: AppBar(title: Text('Mesa ${widget.table.number} — Novo Pedido')),
      body: Column(
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
                  return const Center(child: Text('Nenhum produto nesta categoria.'));
                }
                return ListView.builder(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: filtered.length,
                  itemBuilder: (context, index) {
                    final product = filtered[index];
                    final quantityInCart = cart.items
                        .where((item) => item.product.id == product.id)
                        .fold<int>(0, (sum, item) => sum + item.quantity);
                    return _ProductTile(
                      product: product,
                      quantityInCart: quantityInCart,
                      onAdd: () => cartController.addProduct(product),
                      onRemove: () => cartController.removeProduct(product.id),
                    );
                  },
                );
              },
            ),
          ),
          if (!cart.isEmpty)
            _CartSummaryBar(
              itemCount: cart.totalItemCount,
              totalAmount: cart.totalAmount,
              isSubmitting: _isSubmitting,
              onSubmit: () => _submitOrder(cart, cartController),
            ),
        ],
      ),
    );
  }

  Future<void> _submitOrder(Cart cart, CartController cartController) async {
    setState(() => _isSubmitting = true);
    try {
      final orderApi = ref.read(orderApiProvider);
      final order = await orderApi.submitOrder(
        tableNumber: widget.table.number,
        cart: cart,
        commandId: widget.commandId,
      );
      cartController.clear();

      if (!mounted) return;
      await showRivePaymentReward(
        context,
        rewardValue: order.totalAmount.round(),
        message: 'Pedido enviado à cozinha!\nTotal: R\$ ${order.totalAmount.toStringAsFixed(2)}',
      );
      if (!mounted) return;
      Navigator.of(context).pop();
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Falha ao enviar pedido: ${e.message}')),
      );
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
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

class _ProductTile extends StatelessWidget {
  const _ProductTile({
    required this.product,
    required this.quantityInCart,
    required this.onAdd,
    required this.onRemove,
  });

  final ProductEntity product;
  final int quantityInCart;
  final VoidCallback onAdd;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(product.name, style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text('R\$ ${product.price.toStringAsFixed(2)}'),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (quantityInCart > 0) ...[
            IconButton(icon: const Icon(Icons.remove_circle_outline), onPressed: onRemove),
            Text('$quantityInCart', style: const TextStyle(fontWeight: FontWeight.bold)),
          ],
          IconButton(icon: const Icon(Icons.add_circle, color: Color(0xFFDC2626)), onPressed: onAdd),
        ],
      ),
    );
  }
}

class _CartSummaryBar extends StatelessWidget {
  const _CartSummaryBar({
    required this.itemCount,
    required this.totalAmount,
    required this.isSubmitting,
    required this.onSubmit,
  });

  final int itemCount;
  final double totalAmount;
  final bool isSubmitting;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.grey.shade900,
      child: Row(
        children: [
          Expanded(
            child: Text(
              '$itemCount itens — R\$ ${totalAmount.toStringAsFixed(2)}',
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ),
          FilledButton.icon(
            onPressed: isSubmitting ? null : onSubmit,
            icon: const Icon(Icons.send),
            label: const Text('Enviar à Cozinha'),
          ),
        ],
      ),
    );
  }
}
