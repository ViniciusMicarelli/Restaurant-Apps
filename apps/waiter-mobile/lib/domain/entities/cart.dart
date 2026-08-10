import 'menu_entities.dart';

/// Um item do carrinho: um produto + quantidade + observação, antes de virar
/// `OrderItem` no `order-service` (docs/ai/patterns.md — o carrinho é estado
/// local do app; o pedido só existe de fato após "Enviar à Cozinha").
class CartItem {
  const CartItem({required this.product, required this.quantity, this.notes});

  final ProductEntity product;
  final int quantity;
  final String? notes;

  double get totalPrice => double.parse((product.price * quantity).toStringAsFixed(2));

  CartItem copyWith({int? quantity, String? notes}) {
    return CartItem(
      product: product,
      quantity: quantity ?? this.quantity,
      notes: notes ?? this.notes,
    );
  }
}

/// Carrinho de um pedido em montagem para uma mesa (imutável — cada
/// mutação retorna um novo `Cart`, seguindo o padrão de estado do Riverpod).
class Cart {
  const Cart({this.items = const []});

  final List<CartItem> items;

  bool get isEmpty => items.isEmpty;

  int get totalItemCount => items.fold(0, (sum, item) => sum + item.quantity);

  double get totalAmount =>
      double.parse(items.fold(0.0, (sum, item) => sum + item.totalPrice).toStringAsFixed(2));

  Cart addProduct(ProductEntity product) {
    final existingIndex = items.indexWhere((item) => item.product.id == product.id);
    if (existingIndex == -1) {
      return Cart(items: [...items, CartItem(product: product, quantity: 1)]);
    }
    final updated = [...items];
    updated[existingIndex] = updated[existingIndex].copyWith(
      quantity: updated[existingIndex].quantity + 1,
    );
    return Cart(items: updated);
  }

  Cart removeProduct(String productId) {
    final existingIndex = items.indexWhere((item) => item.product.id == productId);
    if (existingIndex == -1) return this;

    final current = items[existingIndex];
    if (current.quantity <= 1) {
      final updated = [...items]..removeAt(existingIndex);
      return Cart(items: updated);
    }
    final updated = [...items];
    updated[existingIndex] = current.copyWith(quantity: current.quantity - 1);
    return Cart(items: updated);
  }

  Cart clear() => const Cart();
}
