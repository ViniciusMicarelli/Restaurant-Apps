import '../../domain/entities/table_entity.dart';

/// Espelha `TableResponse` do `dining-service`.
class TableDto {
  const TableDto({
    required this.id,
    required this.number,
    required this.capacity,
    required this.status,
  });

  factory TableDto.fromJson(Map<String, dynamic> json) {
    return TableDto(
      id: json['id'] as String,
      number: json['number'] as int,
      capacity: json['capacity'] as int,
      status: json['status'] as String,
    );
  }

  final String id;
  final int number;
  final int capacity;
  final String status;

  TableEntity toEntity() => TableEntity(
    id: id,
    number: number,
    capacity: capacity,
    status: TableStatus.fromWire(status),
  );
}
