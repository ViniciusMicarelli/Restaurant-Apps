import 'package:flutter_test/flutter_test.dart';
import 'package:waiter_mobile/data/dto/command_dto.dart';
import 'package:waiter_mobile/data/dto/menu_dto.dart';
import 'package:waiter_mobile/data/dto/order_dto.dart';
import 'package:waiter_mobile/data/dto/table_dto.dart';
import 'package:waiter_mobile/data/dto/token_response_dto.dart';
import 'package:waiter_mobile/domain/entities/table_entity.dart';

void main() {
  group('TokenResponseDto.fromJson', () {
    test('parses the nested user profile from TokenResponse', () {
      final dto = TokenResponseDto.fromJson({
        'access_token': 'access-1',
        'refresh_token': 'refresh-1',
        'token_type': 'Bearer',
        'expires_in_seconds': 900,
        'user': {
          'id': 'u1',
          'tenant_id': 't1',
          'email': 'ana@x.com',
          'name': 'Ana',
          'role': 'WAITER',
        },
      });

      expect(dto.accessToken, 'access-1');
      expect(dto.tenantId, 't1');
      expect(dto.role, 'WAITER');
    });
  });

  group('TableDto.fromJson', () {
    test('parses and converts status to the domain enum', () {
      final dto = TableDto.fromJson({
        'id': 'table-1',
        'tenant_id': 't1',
        'number': 5,
        'capacity': 4,
        'status': 'OCCUPIED',
        'qr_code_url': 'https://x.com/qr',
      });

      final entity = dto.toEntity();
      expect(entity.number, 5);
      expect(entity.status, TableStatus.occupied);
    });
  });

  group('CommandDto.fromJson', () {
    test('parses a command response', () {
      final dto = CommandDto.fromJson({
        'id': 'cmd-1',
        'tenant_id': 't1',
        'table_id': 'table-1',
        'customer_name': 'João',
        'customer_cpf': null,
        'waiter_id': 'u1',
        'status': 'OPEN',
      });

      expect(dto.customerName, 'João');
      expect(dto.status, 'OPEN');
    });
  });

  group('CategoryDto / ProductDto fromJson', () {
    test('parses a category response', () {
      final dto = CategoryDto.fromJson({
        'id': 'cat-1',
        'tenant_id': 't1',
        'name': 'Hambúrgueres',
        'display_order': 1,
        'is_active': true,
      });

      expect(dto.name, 'Hambúrgueres');
      expect(dto.isActive, isTrue);
    });

    test('parses a product response, converting price to double', () {
      final dto = ProductDto.fromJson({
        'id': 'prod-1',
        'tenant_id': 't1',
        'category_id': 'cat-1',
        'name': 'X-Burger',
        'description': 'Delicioso',
        'price': 25,
        'cost_price': 10,
        'tax_rate': 0.0,
        'photo_url': '',
        'display_order': 0,
        'is_active': true,
      });

      expect(dto.price, 25.0);
      expect(dto.price, isA<double>());
    });
  });

  group('OrderDto.fromJson', () {
    test('parses an order response', () {
      final dto = OrderDto.fromJson({
        'id': 'order-1',
        'status': 'PENDING',
        'total_amount': 51.0,
      });

      expect(dto.id, 'order-1');
      expect(dto.totalAmount, 51.0);
    });
  });
}
