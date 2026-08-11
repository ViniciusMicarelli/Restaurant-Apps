import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/entities/cart.dart';
import '../domain/entities/menu_entities.dart';

// Riverpod 3: `StateNotifier`/`StateNotifierProvider` saíram do pacote
// principal (`FamilyNotifier` também foi removido — não existe mais).
// Em uma family, `Notifier` continua sendo a base certa: o argumento da
// family chega pelo construtor (o `create` que `NotifierProvider.family`
// espera é `NotifierT Function(ArgT arg)`), não por `build()`, que
// permanece sem parâmetros.
class CartController extends Notifier<Cart> {
  CartController(this.tableId);

  final String tableId;

  @override
  Cart build() => const Cart();

  void addProduct(ProductEntity product) => state = state.addProduct(product);

  void removeProduct(String productId) => state = state.removeProduct(productId);

  void clear() => state = state.clear();
}

/// Um carrinho por mesa/comanda em montagem — `family` mantém carrinhos de
/// mesas diferentes isolados caso o garçom navegue entre elas sem enviar.
final cartControllerProvider =
    NotifierProvider.family<CartController, Cart, String>(CartController.new);
