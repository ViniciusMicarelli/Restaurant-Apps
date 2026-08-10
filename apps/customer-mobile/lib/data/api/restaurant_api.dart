import '../dto/restaurant_dto.dart';
import 'api_client.dart';

class RestaurantApi {
  const RestaurantApi(this._client);

  final ApiClient _client;

  Future<RestaurantDto> getBySlug(String slug) async {
    final json = await _client.get('/api/v1/restaurants/by-slug/$slug');
    return RestaurantDto.fromJson(json);
  }
}
