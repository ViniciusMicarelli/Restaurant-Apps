import '../dto/command_dto.dart';
import '../dto/table_dto.dart';
import 'api_client.dart';

class DiningApi {
  const DiningApi(this._client);

  final ApiClient _client;

  Future<List<TableDto>> listTables() async {
    final json = await _client.getList('/api/v1/dining/tables');
    return json.map((e) => TableDto.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<CommandDto> openCommand({
    required int tableNumber,
    required String customerName,
    String? customerCpf,
  }) async {
    final json = await _client.post(
      '/api/v1/dining/commands/open',
      body: {
        'table_number': tableNumber,
        'customer_name': customerName,
        'customer_cpf': ?customerCpf,
      },
    );
    return CommandDto.fromJson(json);
  }

  /// Comandas abertas do tenant — usado para achar o `command_id` de uma
  /// mesa já ocupada (o mapa de mesas só devolve o status, não a comanda).
  Future<List<CommandDto>> listOpenCommands() async {
    final json = await _client.getList('/api/v1/dining/commands?status=OPEN');
    return json.map((e) => CommandDto.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Libera uma mesa "Aguardando Limpeza" de volta pra disponível (US-03.5)
  /// — sem isso, toda comanda encerrada prende a mesa pra sempre.
  Future<TableDto> markTableCleaned(String tableId) async {
    final json = await _client.post('/api/v1/dining/tables/$tableId/mark-cleaned');
    return TableDto.fromJson(json);
  }
}
