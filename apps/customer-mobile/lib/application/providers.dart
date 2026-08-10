import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/api/api_client.dart';
import '../data/api/api_config.dart';
import '../data/api/menu_api.dart';
import '../data/api/restaurant_api.dart';
import '../domain/entities/menu_entities.dart';
import '../domain/entities/restaurant_entity.dart';

final restaurantApiProvider = Provider<RestaurantApi>((ref) {
  return RestaurantApi(ApiClient(baseUrl: ApiConfig.restaurantServiceUrl));
});

final menuApiProvider = Provider<MenuApi>((ref) {
  return MenuApi(ApiClient(baseUrl: ApiConfig.menuServiceUrl));
});

/// Slug do restaurante informado pelo cliente na tela inicial — `null`
/// enquanto nenhum restaurante foi selecionado ainda.
final restaurantSlugProvider = StateProvider<String?>((ref) => null);

final restaurantProvider = FutureProvider.autoDispose<RestaurantEntity?>((ref) async {
  final slug = ref.watch(restaurantSlugProvider);
  if (slug == null || slug.trim().isEmpty) return null;

  final api = ref.watch(restaurantApiProvider);
  final dto = await api.getBySlug(slug.trim());
  return dto.toEntity();
});

final categoriesProvider = FutureProvider.autoDispose<List<CategoryEntity>>((ref) async {
  final restaurant = await ref.watch(restaurantProvider.future);
  if (restaurant == null) return [];

  final api = ref.watch(menuApiProvider);
  final categories = await api.listCategories(restaurant.id);
  final active = categories.where((c) => c.isActive).toList()
    ..sort((a, b) => a.displayOrder.compareTo(b.displayOrder));
  return active.map((dto) => dto.toEntity()).toList();
});

final productsProvider = FutureProvider.autoDispose<List<ProductEntity>>((ref) async {
  final restaurant = await ref.watch(restaurantProvider.future);
  if (restaurant == null) return [];

  final api = ref.watch(menuApiProvider);
  final products = await api.listProducts(restaurant.id);
  return products.where((p) => p.isActive).map((dto) => dto.toEntity()).toList();
});
