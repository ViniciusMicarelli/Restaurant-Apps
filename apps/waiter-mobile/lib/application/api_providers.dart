import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/api/api_client.dart';
import '../data/api/api_config.dart';
import '../data/api/auth_api.dart';
import '../data/api/dining_api.dart';
import '../data/api/menu_api.dart';
import '../data/api/order_api.dart';
import '../data/api/restaurant_api.dart';
import 'session_providers.dart';

/// `AuthApi` nunca anexa token (login ainda não aconteceu).
final authApiProvider = Provider<AuthApi>((ref) {
  return AuthApi(ApiClient(baseUrl: ApiConfig.authServiceUrl));
});

/// `RestaurantApi` também nunca anexa token — resolve o slug do restaurante
/// (público) antes mesmo do login por PIN acontecer.
final restaurantApiProvider = Provider<RestaurantApi>((ref) {
  return RestaurantApi(ApiClient(baseUrl: ApiConfig.restaurantServiceUrl));
});

final diningApiProvider = Provider<DiningApi>((ref) {
  final session = ref.watch(sessionControllerProvider);
  return DiningApi(
    ApiClient(baseUrl: ApiConfig.diningServiceUrl, tokenProvider: () => session?.accessToken),
  );
});

final menuApiProvider = Provider<MenuApi>((ref) {
  final session = ref.watch(sessionControllerProvider);
  return MenuApi(
    ApiClient(baseUrl: ApiConfig.menuServiceUrl, tokenProvider: () => session?.accessToken),
  );
});

final orderApiProvider = Provider<OrderApi>((ref) {
  final session = ref.watch(sessionControllerProvider);
  return OrderApi(
    ApiClient(baseUrl: ApiConfig.orderServiceUrl, tokenProvider: () => session?.accessToken),
  );
});
