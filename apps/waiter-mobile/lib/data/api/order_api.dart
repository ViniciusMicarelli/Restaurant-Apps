import '../../domain/entities/cart.dart';
import '../dto/order_dto.dart';
import 'api_client.dart';

class OrderApi {
  const OrderApi(this._client);

  final ApiClient _client;

  /// Envia o carrinho montado para a cozinha — cria o pedido no
  /// `order-service`, que publica `order.created` (Saga por coreografia,
  /// ADR-001) para o `kitchen-service` popular o KDS automaticamente.
  Future<OrderDto> submitOrder({
    required int tableNumber,
    required Cart cart,
    String? commandId,
  }) async {
    final json = await _client.post(
      '/api/v1/orders',
      body: {
        'order_type': 'TABLE',
        'table_number': tableNumber,
        'command_id': ?commandId,
        'items': cart.items
            .map(
              (item) => {
                'product_id': item.product.id,
                'product_name': item.product.name,
                'unit_price': item.product.price,
                'quantity': item.quantity,
                if (item.notes != null) 'notes': item.notes,
              },
            )
            .toList(),
      },
    );
    return OrderDto.fromJson(json);
  }
}
