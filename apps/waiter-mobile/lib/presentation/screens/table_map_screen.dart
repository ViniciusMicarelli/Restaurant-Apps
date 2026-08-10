import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../application/api_providers.dart';
import '../../application/commands_providers.dart';
import '../../application/session_providers.dart';
import '../../application/tables_providers.dart';
import '../../domain/entities/table_entity.dart';
import '../widgets/rive/rive_loading_indicator.dart';
import 'build_order_screen.dart';
import 'open_command_screen.dart';

class TableMapScreen extends ConsumerWidget {
  const TableMapScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tablesAsync = ref.watch(tablesProvider);
    final session = ref.watch(sessionControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mapa de Mesas'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sair',
            onPressed: () => ref.read(sessionControllerProvider.notifier).logout(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(tablesProvider),
        child: tablesAsync.when(
          loading: () => const Center(child: RiveLoadingIndicator()),
          error: (error, _) => _ErrorState(message: error.toString()),
          data: (tables) => _TableGrid(tables: tables),
        ),
      ),
      floatingActionButton: session != null
          ? FloatingActionButton.extended(
              onPressed: () {}, // reservado para futura tela de fila de espera
              label: Text(session.name),
              icon: const Icon(Icons.person),
            )
          : null,
    );
  }
}

class _TableGrid extends StatelessWidget {
  const _TableGrid({required this.tables});

  final List<TableEntity> tables;

  @override
  Widget build(BuildContext context) {
    if (tables.isEmpty) {
      return const Center(child: Text('Nenhuma mesa cadastrada.'));
    }
    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        mainAxisSpacing: 12,
        crossAxisSpacing: 12,
        childAspectRatio: 1,
      ),
      itemCount: tables.length,
      itemBuilder: (context, index) => _TableCard(table: tables[index]),
    );
  }
}

class _TableCard extends ConsumerWidget {
  const _TableCard({required this.table});

  final TableEntity table;

  Color get _color {
    switch (table.status) {
      case TableStatus.available:
        return Colors.green.shade50;
      case TableStatus.occupied:
        return Colors.red.shade50;
      case TableStatus.reserved:
        return Colors.amber.shade50;
      case TableStatus.waitingCleaning:
        return Colors.purple.shade50;
    }
  }

  Color get _borderColor {
    switch (table.status) {
      case TableStatus.available:
        return Colors.green;
      case TableStatus.occupied:
        return Colors.red;
      case TableStatus.reserved:
        return Colors.amber;
      case TableStatus.waitingCleaning:
        return Colors.purple;
    }
  }

  Future<void> _onTap(BuildContext context, WidgetRef ref) async {
    if (table.status == TableStatus.available) {
      Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => OpenCommandScreen(table: table)),
      );
    } else if (table.status == TableStatus.occupied) {
      // A mesa só guarda o status — a comanda aberta precisa ser encontrada
      // à parte para vincular o próximo pedido a ela (Fase C: faturamento).
      String? commandId;
      try {
        final openCommands = await ref.read(openCommandsProvider.future);
        final matches = openCommands.where((c) => c.tableId == table.id);
        commandId = matches.isEmpty ? null : matches.first.id;
      } catch (_) {
        // Sem a lista de comandas o pedido ainda pode ser enviado, só fica
        // sem vínculo com a comanda — não bloqueia o garçom por isso.
      }
      if (!context.mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => BuildOrderScreen(table: table, commandId: commandId)),
      );
    } else if (table.status == TableStatus.waitingCleaning) {
      try {
        await ref.read(diningApiProvider).markTableCleaned(table.id);
        ref.invalidate(tablesProvider);
        if (!context.mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Mesa ${table.number} liberada!')),
        );
      } catch (_) {
        if (!context.mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Falha ao liberar a mesa. Tente de novo.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return InkWell(
      onTap: () => _onTap(context, ref),
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          color: _color,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: _borderColor, width: 1.5),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Mesa ${table.number}', style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(table.status.label, style: const TextStyle(fontSize: 11)),
            Text('${table.capacity} lugares', style: const TextStyle(fontSize: 10, color: Colors.grey)),
            if (table.status == TableStatus.waitingCleaning) ...[
              const SizedBox(height: 4),
              const Text(
                'Toque para liberar',
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Colors.purple),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text('Falha ao carregar mesas: $message', textAlign: TextAlign.center),
      ),
    );
  }
}
