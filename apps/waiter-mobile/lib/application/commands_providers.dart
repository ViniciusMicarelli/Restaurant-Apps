import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/dto/command_dto.dart';
import 'api_providers.dart';

/// Comandas abertas do tenant — usado para achar o `command_id` de uma mesa
/// já ocupada antes de montar um novo pedido (`BuildOrderScreen` precisa do
/// `command_id` para vincular o pedido à comanda, Fase C do plano de
/// faturamento). `autoDispose` + `ref.invalidate` no pull-to-refresh do mapa
/// de mesas, mesmo padrão de `tablesProvider`.
final openCommandsProvider = FutureProvider.autoDispose<List<CommandDto>>((ref) async {
  final dining = ref.watch(diningApiProvider);
  return dining.listOpenCommands();
});
