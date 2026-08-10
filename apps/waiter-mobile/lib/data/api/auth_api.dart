import '../dto/token_response_dto.dart';
import 'api_client.dart';

class AuthApi {
  const AuthApi(this._client);

  final ApiClient _client;

  Future<TokenResponseDto> loginWithPin({required String tenantId, required String pin}) async {
    final json = await _client.post(
      '/api/v1/auth/login-pin',
      body: {'tenant_id': tenantId, 'pin': pin},
    );
    return TokenResponseDto.fromJson(json);
  }
}
