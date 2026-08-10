import 'dart:async';

import 'package:flutter/material.dart';
import 'package:rive/rive.dart';

/// Celebração de sucesso (Rive, data-binding sobre `rewards.riv` — mesmo
/// arquivo/API do exemplo oficial `docs/runtimes/data-binding`) mostrada
/// depois de uma ação concluída (pedido enviado, comanda fechada). O valor é
/// só decorativo/gamificado, não é dinheiro de verdade nem afeta nada no
/// backend. Se o data-binding falhar por qualquer motivo (ex: nomes de
/// propriedade mudaram numa versão nova do arquivo), cai num ícone estático
/// — a celebração é um enfeite, nunca deve travar o fluxo real do garçom.
class RivePaymentReward extends StatefulWidget {
  const RivePaymentReward({super.key, this.rewardValue = 500, this.message});

  final int rewardValue;
  final String? message;

  @override
  State<RivePaymentReward> createState() => _RivePaymentRewardState();
}

class _RivePaymentRewardState extends State<RivePaymentReward> {
  File? _file;
  RiveWidgetController? _controller;
  ViewModelInstance? _viewModelInstance;
  ViewModelInstanceNumber? _coinProperty;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    try {
      final file = await File.asset(
        'assets/animations/rewards.riv',
        riveFactory: Factory.flutter,
      );
      if (file == null) return;

      final controller = RiveWidgetController(file);
      final viewModelInstance = controller.dataBind(DataBind.auto());

      // Sempre celebra com moedas (o arquivo original sorteia moeda/gema
      // aleatoriamente — aqui fixamos moeda, é sempre a mesma "recompensa").
      viewModelInstance.viewModel('Item_Selection')?.enumerator('Item_Selection')?.value = 'Coin';
      final coinProperty = viewModelInstance.viewModel('Coin')?.number('Item_Value');
      coinProperty?.value = widget.rewardValue.toDouble();

      if (!mounted) {
        coinProperty?.dispose();
        viewModelInstance.dispose();
        controller.dispose();
        file.dispose();
        return;
      }
      setState(() {
        _file = file;
        _controller = controller;
        _viewModelInstance = viewModelInstance;
        _coinProperty = coinProperty;
      });
    } catch (_) {
      // Sem fallback de estado aqui: `_controller` permanece null e o
      // `build()` já mostra o ícone estático nesse caso.
    }
  }

  @override
  void dispose() {
    _coinProperty?.dispose();
    _viewModelInstance?.dispose();
    _controller?.dispose();
    _file?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 180,
          height: 180,
          child: controller == null
              ? Icon(Icons.celebration, size: 96, color: Colors.amber.shade600)
              : RiveWidget(controller: controller, fit: Fit.contain),
        ),
        if (widget.message != null) ...[
          const SizedBox(height: 12),
          Text(
            widget.message!,
            style: Theme.of(context).textTheme.titleMedium,
            textAlign: TextAlign.center,
          ),
        ],
      ],
    );
  }
}

/// Mostra [RivePaymentReward] num diálogo transparente por [duration] e
/// fecha sozinho — uso: `await showRivePaymentReward(context, message: 'Pedido enviado!');`
Future<void> showRivePaymentReward(
  BuildContext context, {
  int rewardValue = 500,
  String? message,
  Duration duration = const Duration(milliseconds: 2200),
}) async {
  final navigator = Navigator.of(context);
  unawaited(
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black45,
      builder: (_) => Dialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: RivePaymentReward(rewardValue: rewardValue, message: message),
        ),
      ),
    ),
  );
  await Future.delayed(duration);
  if (navigator.canPop()) navigator.pop();
}
