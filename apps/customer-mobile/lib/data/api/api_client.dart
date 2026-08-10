import 'package:dio/dio.dart';

import 'api_exception.dart';

/// Cliente HTTP fino sobre `Dio`, comum aos módulos de API — app público,
/// sem autenticação (o escopo de tenant vai no header `X-Tenant-Id`).
class ApiClient {
  ApiClient({required String baseUrl}) {
    _dio = Dio(BaseOptions(baseUrl: baseUrl, connectTimeout: const Duration(seconds: 10)));
  }

  late final Dio _dio;

  Future<Map<String, dynamic>> get(String path, {String? tenantId}) async {
    try {
      final response = await _dio.get<dynamic>(
        path,
        options: Options(headers: tenantId != null ? {'X-Tenant-Id': tenantId} : null),
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }

  Future<List<dynamic>> getList(String path, {String? tenantId}) async {
    try {
      final response = await _dio.get<dynamic>(
        path,
        options: Options(headers: tenantId != null ? {'X-Tenant-Id': tenantId} : null),
      );
      return response.data as List<dynamic>;
    } on DioException catch (e) {
      throw ApiException.fromDioException(e);
    }
  }
}
