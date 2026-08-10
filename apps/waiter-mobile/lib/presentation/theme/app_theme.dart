import 'package:flutter/material.dart';

/// Tokens da direção visual aprovada (2026-08-10, ver docs/logs/2026-08-10.md
/// Sessão 8/9) — mesma paleta usada em `admin-web` (`tailwind.config.js`),
/// portada pra `ColorScheme`. `waiter-mobile` é ferramenta interna da
/// equipe, sem White-Label por tenant (mesmo raciocínio do `admin-web`:
/// não é essa a tela que o restaurante personaliza) — paleta fixa.
class AppTheme {
  const AppTheme._();

  static const Color ink = Color(0xFF1B1E27);
  static const Color inkSoft = Color(0xFF565C6B);
  static const Color paper = Color(0xFFF1F2F5);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color border = Color(0xFFDDE0E6);

  static const Color accent = Color(0xFFC1541F);
  static const Color good = Color(0xFF3F7D5C);
  static const Color warning = Color(0xFFA9781F);
  static const Color critical = Color(0xFFB23A3A);
  static const Color info = Color(0xFF3B5B8C);

  /// Números — dinheiro, contadores, cronômetro do KDS — com algarismos
  /// tabulares (equivalente Flutter do `font-variant-numeric: tabular-nums`
  /// já usado nos apps web), pra alinhar em coluna sem precisar de uma
  /// fonte monoespaçada embutida.
  static const List<FontFeature> tabularFigures = [FontFeature.tabularFigures()];

  static ThemeData light() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: accent,
      primary: accent,
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
      appBarTheme: const AppBarTheme(
        backgroundColor: surface,
        foregroundColor: ink,
        elevation: 0,
        titleTextStyle: TextStyle(
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
}
