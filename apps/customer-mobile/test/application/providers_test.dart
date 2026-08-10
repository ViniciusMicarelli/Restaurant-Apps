import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:customer_mobile/application/providers.dart';
import 'package:customer_mobile/data/api/menu_api.dart';
import 'package:customer_mobile/data/api/restaurant_api.dart';
import 'package:customer_mobile/data/dto/menu_dto.dart';
import 'package:customer_mobile/data/dto/restaurant_dto.dart';

class _FakeRestaurantApi implements RestaurantApi {
  @override
  Future<RestaurantDto> getBySlug(String slug) async {
    return RestaurantDto.fromJson({
      'id': 'tenant-1',
      'slug': slug,
      'trade_name': 'Burger House',
      'branding': {
        'primary_color': '#DC2626',
        'logo_url': '',
        'banner_url': '',
      },
    });
  }
}

class _FakeMenuApi implements MenuApi {
  @override
  Future<List<CategoryDto>> listCategories(String tenantId) async {
    return [
      CategoryDto.fromJson({
        'id': 'cat-2',
        'tenant_id': tenantId,
        'name': 'Sobremesas',
        'display_order': 2,
        'is_active': true,
      }),
      CategoryDto.fromJson({
        'id': 'cat-1',
        'tenant_id': tenantId,
        'name': 'Hambúrgueres',
        'display_order': 1,
        'is_active': true,
      }),
      CategoryDto.fromJson({
        'id': 'cat-3',
        'tenant_id': tenantId,
        'name': 'Descontinuada',
        'display_order': 3,
        'is_active': false,
      }),
    ];
  }

  @override
  Future<List<ProductDto>> listProducts(String tenantId) async {
    return [
      ProductDto.fromJson({
        'id': 'prod-1',
        'tenant_id': tenantId,
        'category_id': 'cat-1',
        'name': 'X-Burger',
        'description': '',
        'price': 25,
        'cost_price': 10,
        'tax_rate': 0.0,
        'photo_url': '',
        'display_order': 0,
        'is_active': true,
      }),
      ProductDto.fromJson({
        'id': 'prod-2',
        'tenant_id': tenantId,
        'category_id': 'cat-2',
        'name': 'Produto Inativo',
        'description': '',
        'price': 10,
        'cost_price': 5,
        'tax_rate': 0.0,
        'photo_url': '',
        'display_order': 0,
        'is_active': false,
      }),
    ];
  }
}

void main() {
  late ProviderContainer container;

  setUp(() {
    container = ProviderContainer(
      overrides: [
        restaurantApiProvider.overrideWithValue(_FakeRestaurantApi()),
        menuApiProvider.overrideWithValue(_FakeMenuApi()),
      ],
    );
  });

  tearDown(() => container.dispose());

  test('restaurantProvider is null until a slug is set', () async {
    final restaurant = await container.read(restaurantProvider.future);
    expect(restaurant, isNull);
  });

  test('restaurantProvider resolves the restaurant once a slug is set', () async {
    container.read(restaurantSlugProvider.notifier).state = 'burger-house';

    final restaurant = await container.read(restaurantProvider.future);

    expect(restaurant, isNotNull);
    expect(restaurant!.tradeName, 'Burger House');
  });

  test('categoriesProvider returns only active categories, sorted by display order', () async {
    container.read(restaurantSlugProvider.notifier).state = 'burger-house';

    final categories = await container.read(categoriesProvider.future);

    expect(categories.map((c) => c.name).toList(), ['Hambúrgueres', 'Sobremesas']);
  });

  test('productsProvider returns only active products', () async {
    container.read(restaurantSlugProvider.notifier).state = 'burger-house';

    final products = await container.read(productsProvider.future);

    expect(products, hasLength(1));
    expect(products.first.name, 'X-Burger');
  });
}
