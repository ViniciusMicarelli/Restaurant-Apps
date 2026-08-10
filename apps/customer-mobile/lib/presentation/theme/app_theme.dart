import 'package:flutter/material.dart';

/// Tokens da direção visual aprovada (2026-08-10, ver docs/logs/2026-08-10.md
/// Sessão 8/9) — mesma paleta usada em `customer-web` (`tailwind.config.js`).
/// `defaultPrimary`/`good`/`warning`/`critical` ficam fixos (estado
/// semântico não é White-Label); só `primary` é substituível por tenant —
/// mesmo raciocínio de `customer-web`, onde só o `accent` referencia a
/// variável CSS de branding.
class AppTheme {
  const AppTheme._();

  static const Color defaultPrimary = Color(0xFFC1541F);

  static const Color ink = Color(0xFF1B1E27);
  static const Color inkSoft = Color(0xFF565C6B);
  static const Color paper = Color(0xFFF1F2F5);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color border = Color(0xFFDDE0E6);

  static const Color good = Color(0xFF3F7D5C);
  static const Color warning = Color(0xFFA9781F);
  static const Color critical = Color(0xFFB23A3A);

  /// Números — preço, contadores — com algarismos tabulares (equivalente
  /// Flutter do `font-variant-numeric: tabular-nums` já usado nos web apps).
  static const List<FontFeature> tabularFigures = [FontFeature.tabularFigures()];

  static ThemeData light({Color? primary}) {
    final seed = primary ?? defaultPrimary;
    final colorScheme = ColorScheme.fromSeed(
      seedColor: seed,
      primary: seed,
      onPrimary: Colors.white,
      error: critical,
      onError: Colors.white,
      tertiary: good,
      surface: surface,
      onSurface: ink,
      outline: border,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: paper,
      cardColor: surface,
      dividerColor: border,
      appBarTheme: AppBarTheme(
        backgroundColor: surface,
        foregroundColor: ink,
        elevation: 0,
        titleTextStyle: const TextStyle(
          color: ink,
          fontSize: 18,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.2,
        ),
      ),
      textTheme: const TextTheme(
        bodyMedium: TextStyle(color: ink),
        bodySmall: TextStyle(color: inkSoft),
      ),
    );
  }

  /// Converte um HEX (`#RRGGBB`) vindo do `restaurant-service` em `Color` —
  /// o branding é dado dinâmico do backend, nunca fixo no app.
  static Color? colorFromHex(String? hex) {
    if (hex == null || hex.isEmpty) return null;
    final normalized = hex.replaceFirst('#', '');
    final value = int.tryParse(normalized, radix: 16);
    if (value == null) return null;
    return Color(0xFF000000 | value);
  }
}
