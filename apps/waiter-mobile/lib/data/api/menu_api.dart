import '../dto/menu_dto.dart';
import 'api_client.dart';

class MenuApi {
  const MenuApi(this._client);

  final ApiClient _client;

  Future<List<CategoryDto>> listCategories() async {
    final json = await _client.getList('/api/v1/menu/categories');
    return json.map((e) => CategoryDto.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<ProductDto>> listProducts() async {
    final json = await _client.getList('/api/v1/menu/products');
    return json.map((e) => ProductDto.fromJson(e as Map<String, dynamic>)).toList();
  }
}
