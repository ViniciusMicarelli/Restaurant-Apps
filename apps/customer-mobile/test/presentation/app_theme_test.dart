import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:customer_mobile/presentation/theme/app_theme.dart';

void main() {
  group('AppTheme.colorFromHex', () {
    test('parses a 6-digit hex color with a leading #', () {
      expect(AppTheme.colorFromHex('#DC2626'), const Color(0xFFDC2626));
    });

    test('parses a 6-digit hex color without a leading #', () {
      expect(AppTheme.colorFromHex('059669'), const Color(0xFF059669));
    });

    test('returns null for null input', () {
      expect(AppTheme.colorFromHex(null), isNull);
    });

    test('returns null for an empty string', () {
      expect(AppTheme.colorFromHex(''), isNull);
    });

    test('returns null for an invalid hex string', () {
      expect(AppTheme.colorFromHex('not-a-color'), isNull);
    });
  });
}
