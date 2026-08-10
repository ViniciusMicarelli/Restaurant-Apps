/// Espelha `OrderResponse` do `order-service` — só os campos que o app do
/// garçom usa para confirmar o envio à cozinha.
class OrderDto {
  const OrderDto({required this.id, required this.status, required this.totalAmount});

  factory OrderDto.fromJson(Map<String, dynamic> json) {
    return OrderDto(
      id: json['id'] as String,
      status: json['status'] as String,
      totalAmount: (json['total_amount'] as num).toDouble(),
    );
  }

  final String id;
  final String status;
  final double totalAmount;
}
