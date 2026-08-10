import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../application/api_providers.dart';
import '../../application/session_providers.dart';
import '../../data/api/api_exception.dart';
import '../widgets/rive/rive_loading_indicator.dart';

/// Login rápido do garçom/caixa/cozinha via PIN de 4 dígitos (US-01.4).
///
/// O PIN só é único *dentro* de um tenant, não globalmente — então o app
/// precisa saber de qual restaurante é o PIN. Pedir o `tenant_id` (UUID) de
/// cabeça é péssima UX; em vez disso pedimos o *slug* do restaurante (ex:
/// "restaurante-demo", o mesmo que aparece na URL do cardápio digital) e
/// resolvemos o UUID por trás via `GET /restaurants/by-slug/{slug}` (público)
/// antes de chamar o login por PIN.
class PinLoginScreen extends ConsumerStatefulWidget {
  const PinLoginScreen({super.key});

  @override
  ConsumerState<PinLoginScreen> createState() => _PinLoginScreenState();
}

class _PinLoginScreenState extends ConsumerState<PinLoginScreen> {
  final _slugController = TextEditingController();
  String _pin = '';
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _slugController.dispose();
    super.dispose();
  }

  void _onDigitPressed(String digit) {
    if (_pin.length >= 4) return;
    setState(() => _pin += digit);
    if (_pin.length == 4) {
      _submit();
    }
  }

  void _onBackspacePressed() {
    if (_pin.isEmpty) return;
    setState(() => _pin = _pin.substring(0, _pin.length - 1));
  }

  Future<void> _submit() async {
    final slug = _slugController.text.trim();
    if (slug.isEmpty) {
      setState(() => _errorMessage = 'Informe o código do restaurante.');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      final restaurantApi = ref.read(restaurantApiProvider);
      final String tenantId;
      try {
        tenantId = await restaurantApi.getTenantIdBySlug(slug);
      } on ApiException catch (e) {
        if (e.statusCode == 404) {
          // Erro comum: usuário digita o tenant_id (UUID técnico) em vez do
          // slug — devolve uma mensagem que aponta a causa provável em vez
          // do "recurso não encontrado" genérico do backend.
          throw const ApiException(
            'Restaurante não encontrado. Digite o código/slug do restaurante '
            '(ex: restaurante-demo) — não o ID técnico (UUID).',
          );
        }
        rethrow;
      }

      final authApi = ref.read(authApiProvider);
      final token = await authApi.loginWithPin(tenantId: tenantId, pin: _pin);
      await ref.read(sessionControllerProvider.notifier).login(token.toSession());
    } on ApiException catch (e) {
      setState(() {
        _errorMessage = e.message;
        _pin = '';
      });
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.storefront, size: 48, color: Color(0xFFDC2626)),
              const SizedBox(height: 12),
              const Text(
                'Entrar com PIN',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              const Text(
                'Garçom, Caixa ou Cozinha',
                style: TextStyle(fontSize: 13, color: Colors.grey),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: _slugController,
                textCapitalization: TextCapitalization.none,
                decoration: const InputDecoration(
                  labelText: 'Código do restaurante',
                  hintText: 'ex: restaurante-demo',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 24),
              _PinDots(filledCount: _pin.length),
              if (_errorMessage != null) ...[
                const SizedBox(height: 12),
                Text(
                  _errorMessage!,
                  style: const TextStyle(color: Colors.red, fontSize: 12, fontWeight: FontWeight.w600),
                  textAlign: TextAlign.center,
                ),
              ],
              const SizedBox(height: 24),
              if (_isSubmitting)
                const RiveLoadingIndicator(size: 72)
              else
                _PinKeypad(onDigit: _onDigitPressed, onBackspace: _onBackspacePressed),
            ],
          ),
        ),
      ),
    );
  }
}

class _PinDots extends StatelessWidget {
  const _PinDots({required this.filledCount});

  final int filledCount;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(4, (index) {
        final filled = index < filledCount;
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 6),
          width: 16,
          height: 16,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: filled ? const Color(0xFFDC2626) : Colors.transparent,
            border: Border.all(color: const Color(0xFFDC2626), width: 1.5),
          ),
        );
      }),
    );
  }
}

class _PinKeypad extends StatelessWidget {
  const _PinKeypad({required this.onDigit, required this.onBackspace});

  final ValueChanged<String> onDigit;
  final VoidCallback onBackspace;

  @override
  Widget build(BuildContext context) {
    const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '', '0', '⌫'];
    return SizedBox(
      width: 260,
      child: GridView.count(
        crossAxisCount: 3,
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        children: keys.map((key) {
          if (key.isEmpty) return const SizedBox.shrink();
          return InkWell(
            onTap: key == '⌫' ? onBackspace : () => onDigit(key),
            child: Center(
              child: Text(key, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
            ),
          );
        }).toList(),
      ),
    );
  }
}
