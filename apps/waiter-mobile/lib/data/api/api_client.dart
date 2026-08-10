import 'package:dio/dio.dart';

import 'api_exception.dart';

/// Cliente HTTP fino sobre `Dio`, comum aos módulos de API de cada
/// microsserviço. Anexa o `Bearer` token da sessão (quando houver) e traduz
/// erros em `ApiException`.
class ApiClient {
  ApiClient({required String baseUrl, String? Function()? tokenProvider}) {
    _dio = Dio(BaseOptions(baseUrl: baseUrl, connectTimeout: const Duration(seconds: 10)));
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final token = tokenProvider?.call();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
      ),
    );
  }

  late final Dio _dio;

  Future<Map<String, dynamic>> get(String path, {Map<String, dynamic>? queryParameters}) async {
    try {
      final response = await _dio.get<dynamic>(path, queryParameters: queryParameters);
      return _asMap(response.data);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<List<dynamic>> getList(String path) async {
    try {
      final response = await _dio.get<dynamic>(path);
      return response.data as List<dynamic>;
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<Map<String, dynamic>> post(String path, {Map<String, dynamic>? body}) async {
    try {
      final response = await _dio.post<dynamic>(path, data: body);
      return _asMap(response.data);
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Map<String, dynamic> _asMap(dynamic data) => data as Map<String, dynamic>;
}
