import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../application/api_providers.dart';
import '../../application/tables_providers.dart';
import '../../data/api/api_exception.dart';
import '../../domain/entities/table_entity.dart';
import 'build_order_screen.dart';

/// Abre a comanda de uma mesa livre (US-03.3), associando o nome/CPF do
/// cliente, e segue direto para a montagem do pedido.
class OpenCommandScreen extends ConsumerStatefulWidget {
  const OpenCommandScreen({super.key, required this.table});

  final TableEntity table;

  @override
  ConsumerState<OpenCommandScreen> createState() => _OpenCommandScreenState();
}

class _OpenCommandScreenState extends ConsumerState<OpenCommandScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _cpfController = TextEditingController();
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _nameController.dispose();
    _cpfController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      final diningApi = ref.read(diningApiProvider);
      final command = await diningApi.openCommand(
        tableNumber: widget.table.number,
        customerName: _nameController.text.trim(),
        customerCpf: _cpfController.text.trim().isEmpty ? null : _cpfController.text.trim(),
      );
      ref.invalidate(tablesProvider);

      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => BuildOrderScreen(table: widget.table, commandId: command.id),
        ),
      );
    } on ApiException catch (e) {
      setState(() => _errorMessage = e.message);
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Abrir Comanda — Mesa ${widget.table.number}')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(labelText: 'Nome do cliente', border: OutlineInputBorder()),
                validator: (value) =>
                    (value == null || value.trim().isEmpty) ? 'Informe o nome do cliente.' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _cpfController,
                decoration: const InputDecoration(labelText: 'CPF (opcional)', border: OutlineInputBorder()),
              ),
              if (_errorMessage != null) ...[
                const SizedBox(height: 12),
                Text(_errorMessage!, style: const TextStyle(color: Colors.red)),
              ],
              const SizedBox(height: 24),
              FilledButton(
                onPressed: _isSubmitting ? null : _submit,
                child: _isSubmitting
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Abrir Comanda'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
