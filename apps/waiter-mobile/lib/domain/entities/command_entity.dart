/// Comanda aberta em uma mesa — espelha `CommandResponse` do `dining-service`.
class CommandEntity {
  const CommandEntity({
    required this.id,
    required this.tableId,
    required this.customerName,
    required this.status,
  });

  final String id;
  final String tableId;
  final String customerName;
  final String status;
}
