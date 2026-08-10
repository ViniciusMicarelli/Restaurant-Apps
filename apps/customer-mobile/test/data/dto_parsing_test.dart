import 'package:flutter_test/flutter_test.dart';
import 'package:customer_mobile/data/dto/menu_dto.dart';
import 'package:customer_mobile/data/dto/restaurant_dto.dart';

void main() {
  group('RestaurantDto.fromJson', () {
    test('parses nested branding fields', () {
      final dto = RestaurantDto.fromJson({
        'id': 'r1',
        'slug': 'burger-house',
        'trade_name': 'Burger House',
        'branding': {
          'primary_color': '#DC2626',
          'logo_url': 'https://x.com/logo.png',
          'banner_url': 'https://x.com/banner.png',
        },
      });

      expect(dto.tradeName, 'Burger House');
      expect(dto.primaryColor, '#DC2626');
      final entity = dto.toEntity();
      expect(entity.slug, 'burger-house');
    });
  });

  group('CategoryDto / ProductDto fromJson', () {
    test('parses a category response', () {
      final dto = CategoryDto.fromJson({
        'id': 'cat-1',
        'tenant_id': 't1',
        'name': 'Bebidas',
        'display_order': 2,
        'is_active': true,
      });

      expect(dto.name, 'Bebidas');
      expect(dto.displayOrder, 2);
    });

    test('parses a product response, converting price to double', () {
      final dto = ProductDto.fromJson({
        'id': 'prod-1',
        'tenant_id': 't1',
        'category_id': 'cat-1',
        'name': 'Coca-Cola',
        'description': 'Lata 350ml',
        'price': 7,
        'cost_price': 3,
        'tax_rate': 0.0,
        'photo_url': '',
        'display_order': 0,
        'is_active': true,
      });

      expect(dto.price, 7.0);
      expect(dto.price, isA<double>());
      expect(dto.toEntity().name, 'Coca-Cola');
    });
  });
}
