import 'package:flutter/material.dart';
import 'package:rive/rive.dart';

/// Indicador de carregamento animado (Rive) — substitui o
/// `CircularProgressIndicator` genérico nas telas que buscam dados. Cai de
/// volta pro spinner nativo enquanto carrega ou se o asset falhar, então a
/// animação nunca trava nem quebra uma tela real (ver
/// `assets/animations/README.md`).
class RiveLoadingIndicator extends StatefulWidget {
  const RiveLoadingIndicator({super.key, this.size = 120});

  final double size;

  @override
  State<RiveLoadingIndicator> createState() => _RiveLoadingIndicatorState();
}

class _RiveLoadingIndicatorState extends State<RiveLoadingIndicator> {
  late final FileLoader _fileLoader = FileLoader.fromAsset(
    'assets/animations/liquid_download.riv',
    riveFactory: Factory.flutter,
  );

  @override
  void dispose() {
    _fileLoader.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: RiveWidgetBuilder(
        fileLoader: _fileLoader,
        dataBind: DataBind.auto(),
        builder: (context, state) => switch (state) {
          RiveLoading() => const Center(child: CircularProgressIndicator()),
          RiveFailed() => const Center(child: CircularProgressIndicator()),
          RiveLoaded() => RiveWidget(controller: state.controller, fit: Fit.contain),
        },
      ),
    );
  }
}
