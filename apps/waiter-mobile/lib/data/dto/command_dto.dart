import '../../domain/entities/command_entity.dart';

/// Espelha `CommandResponse` do `dining-service`.
class CommandDto {
  const CommandDto({
    required this.id,
    required this.tableId,
    required this.customerName,
    required this.status,
  });

  factory CommandDto.fromJson(Map<String, dynamic> json) {
    return CommandDto(
      id: json['id'] as String,
      tableId: json['table_id'] as String,
      customerName: json['customer_name'] as String,
      status: json['status'] as String,
    );
  }

  final String id;
  final String tableId;
  final String customerName;
  final String status;

  CommandEntity toEntity() =>
      CommandEntity(id: id, tableId: tableId, customerName: customerName, status: status);
}
