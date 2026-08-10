import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/entities/table_entity.dart';
import 'api_providers.dart';

/// Mapa de mesas em tempo real — `autoDispose` + `ref.invalidate` no pull-to-refresh
/// da tela (não usa polling automático para manter o app simples e testável).
final tablesProvider = FutureProvider.autoDispose<List<TableEntity>>((ref) async {
  final dining = ref.watch(diningApiProvider);
  final tables = await dining.listTables();
  return tables.map((dto) => dto.toEntity()).toList();
});
