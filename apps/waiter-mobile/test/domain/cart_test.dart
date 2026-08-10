import 'package:flutter_test/flutter_test.dart';
import 'package:waiter_mobile/domain/entities/cart.dart';
import 'package:waiter_mobile/domain/entities/menu_entities.dart';

const _burger = ProductEntity(
  id: 'prod-1',
  categoryId: 'cat-1',
  name: 'X-Burger',
  description: 'Hambúrguer artesanal',
  price: 25.5,
  photoUrl: '',
);

const _soda = ProductEntity(
  id: 'prod-2',
  categoryId: 'cat-2',
  name: 'Coca-Cola',
  description: 'Lata 350ml',
  price: 6.9,
  photoUrl: '',
);

void main() {
  group('Cart', () {
    test('starts empty', () {
      const cart = Cart();
      expect(cart.isEmpty, isTrue);
      expect(cart.totalAmount, 0.0);
    });

    test('addProduct adds a new item with quantity 1', () {
      final cart = const Cart().addProduct(_burger);

      expect(cart.items, hasLength(1));
      expect(cart.items.first.quantity, 1);
      expect(cart.totalAmount, 25.5);
    });

    test('addProduct increments quantity when the product is already in the cart', () {
      final cart = const Cart().addProduct(_burger).addProduct(_burger);

      expect(cart.items, hasLength(1));
      expect(cart.items.first.quantity, 2);
      expect(cart.totalAmount, 51.0);
    });

    test('totalAmount sums all distinct items', () {
      final cart = const Cart().addProduct(_burger).addProduct(_soda);

      expect(cart.totalAmount, 32.4);
      expect(cart.totalItemCount, 2);
    });

    test('removeProduct decrements quantity without removing the item', () {
      final cart = const Cart().addProduct(_burger).addProduct(_burger).removeProduct(_burger.id);

      expect(cart.items.first.quantity, 1);
    });

    test('removeProduct removes the item entirely when quantity reaches zero', () {
      final cart = const Cart().addProduct(_burger).removeProduct(_burger.id);

      expect(cart.isEmpty, isTrue);
    });

    test('removeProduct is a no-op for a product not in the cart', () {
      final cart = const Cart().addProduct(_burger).removeProduct('unknown-id');

      expect(cart.items, hasLength(1));
    });

    test('clear empties the cart', () {
      final cart = const Cart().addProduct(_burger).addProduct(_soda).clear();

      expect(cart.isEmpty, isTrue);
    });
  });
}
