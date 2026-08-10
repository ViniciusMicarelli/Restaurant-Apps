import 'api_client.dart';

/// Resolve o `tenant_id` (UUID) a partir do slug do restaurante — digitar um
/// UUID de cabeça não é uma UX aceitável para o login do garçom, então o PIN
/// login pede o slug (ex: "restaurante-demo", já visível no QR Code/no
/// crachá do restaurante) e resolve o UUID por trás dos panos.
class RestaurantApi {
  const RestaurantApi(this._client);

  final ApiClient _client;

  Future<String> getTenantIdBySlug(String slug) async {
    final json = await _client.get('/api/v1/restaurants/by-slug/$slug');
    return json['id'] as String;
  }
}
