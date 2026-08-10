import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/entities/cart.dart';
import '../domain/entities/menu_entities.dart';

class CartController extends StateNotifier<Cart> {
  CartController() : super(const Cart());

  void addProduct(ProductEntity product) => state = state.addProduct(product);

  void removeProduct(String productId) => state = state.removeProduct(productId);

  void clear() => state = state.clear();
}

/// Um carrinho por mesa/comanda em montagem — `family` mantém carrinhos de
/// mesas diferentes isolados caso o garçom navegue entre elas sem enviar.
final cartControllerProvider =
    StateNotifierProvider.family<CartController, Cart, String>((ref, tableId) {
      return CartController();
    });
