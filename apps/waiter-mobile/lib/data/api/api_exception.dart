import 'package:dio/dio.dart';

/// Erro de API traduzido do formato RFC 7807 Problem Details devolvido pelo
/// backend (`restaurant_common.problem_details`), para que a UI exiba a
/// mensagem real em vez de um erro HTTP genérico.
class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode, this.code});

  factory ApiException.fromDioException(DioException error) {
    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final detail = data['detail'] as String?;
      final title = data['title'] as String?;
      final code = data['code'] as String?;
      return ApiException(
        detail ?? title ?? 'Falha na requisição.',
        statusCode: error.response?.statusCode,
        code: code,
      );
    }
    return ApiException(
      error.message ?? 'Falha de conexão com o servidor.',
      statusCode: error.response?.statusCode,
    );
  }

  final String message;
  final int? statusCode;
  final String? code;

  @override
  String toString() => message;
}
