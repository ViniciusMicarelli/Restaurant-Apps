/// Máquina de Estados da mesa — espelha `TableStatus` do `dining-service`.
enum TableStatus { available, occupied, reserved, waitingCleaning;

  static TableStatus fromWire(String value) {
    switch (value) {
      case 'AVAILABLE':
        return TableStatus.available;
      case 'OCCUPIED':
        return TableStatus.occupied;
      case 'RESERVED':
        return TableStatus.reserved;
      case 'WAITING_CLEANING':
        return TableStatus.waitingCleaning;
      default:
        throw ArgumentError('Status de mesa desconhecido: $value');
    }
  }

  String get label {
    switch (this) {
      case TableStatus.available:
        return 'Livre';
      case TableStatus.occupied:
        return 'Ocupada';
      case TableStatus.reserved:
        return 'Reservada';
      case TableStatus.waitingCleaning:
        return 'Aguardando Limpeza';
    }
  }
}

/// Mesa do salão (Aggregate reduzido no cliente — só o necessário para o app do garçom).
class TableEntity {
  const TableEntity({
    required this.id,
    required this.number,
    required this.capacity,
    required this.status,
  });

  final String id;
  final int number;
  final int capacity;
  final TableStatus status;
}
