import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:customer_mobile/app.dart';
import 'package:customer_mobile/application/providers.dart';
import 'package:customer_mobile/data/api/menu_api.dart';
import 'package:customer_mobile/data/api/restaurant_api.dart';
import 'package:customer_mobile/data/dto/menu_dto.dart';
import 'package:customer_mobile/data/dto/restaurant_dto.dart';
import 'package:customer_mobile/presentation/theme/app_theme.dart';

class _FakeRestaurantApi implements RestaurantApi {
  @override
  Future<RestaurantDto> getBySlug(String slug) async {
    return RestaurantDto.fromJson({
      'id': 'tenant-1',
      'slug': slug,
      'trade_name': 'Burger House',
      'branding': {'primary_color': '#059669', 'logo_url': '', 'banner_url': ''},
    });
  }
}

class _EmptyMenuApi implements MenuApi {
  @override
  Future<List<CategoryDto>> listCategories(String tenantId) async => [];

  @override
  Future<List<ProductDto>> listProducts(String tenantId) async => [];
}

MaterialApp _materialAppFrom(WidgetTester tester) =>
    tester.widget<MaterialApp>(find.byType(MaterialApp));

void main() {
  testWidgets('uses the default accent before a restaurant is selected', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          restaurantApiProvider.overrideWithValue(_FakeRestaurantApi()),
          menuApiProvider.overrideWithValue(_EmptyMenuApi()),
        ],
        child: const CustomerApp(),
      ),
    );
    await tester.pump();

    final theme = _materialAppFrom(tester).theme!;
    expect(theme.colorScheme.primary, AppTheme.defaultPrimary);
  });

  testWidgets('applies the tenant brand color once the restaurant loads', (tester) async {
    late ProviderContainer container;

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          restaurantApiProvider.overrideWithValue(_FakeRestaurantApi()),
          menuApiProvider.overrideWithValue(_EmptyMenuApi()),
        ],
        child: Consumer(
          builder: (context, ref, _) {
            container = ProviderScope.containerOf(context);
            return const CustomerApp();
          },
        ),
      ),
    );
    await tester.pump();

    container.read(restaurantSlugProvider.notifier).state = 'burger-house';
    await tester.pumpAndSettle();

    final theme = _materialAppFrom(tester).theme!;
    expect(theme.colorScheme.primary, const Color(0xFF059669));
  });
}
