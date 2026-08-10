import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:waiter_mobile/application/cart_providers.dart';
import 'package:waiter_mobile/domain/entities/menu_entities.dart';

const _burger = ProductEntity(
  id: 'prod-1',
  categoryId: 'cat-1',
  name: 'X-Burger',
  description: '',
  price: 25.5,
  photoUrl: '',
);

void main() {
  test('cartControllerProvider keeps separate carts per table (family)', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    container.read(cartControllerProvider('table-1').notifier).addProduct(_burger);

    final cartForTable1 = container.read(cartControllerProvider('table-1'));
    final cartForTable2 = container.read(cartControllerProvider('table-2'));

    expect(cartForTable1.totalItemCount, 1);
    expect(cartForTable2.isEmpty, isTrue);
  });

  test('addProduct and removeProduct update the watched state', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    final controller = container.read(cartControllerProvider('table-1').notifier);

    controller.addProduct(_burger);
    expect(container.read(cartControllerProvider('table-1')).totalItemCount, 1);

    controller.removeProduct(_burger.id);
    expect(container.read(cartControllerProvider('table-1')).isEmpty, isTrue);
  });
}
