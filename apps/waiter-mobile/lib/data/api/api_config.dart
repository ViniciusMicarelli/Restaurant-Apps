/// URLs-base dos microsserviços consumidos pelo app do garçom.
///
/// Nenhuma URL é hardcoded para produção: os valores abaixo são apenas o
/// padrão de desenvolvimento (`docker-compose.dev.yml`), sobrescrevível em
/// tempo de build via `--dart-define`, ex:
/// `flutter build apk --dart-define=AUTH_SERVICE_URL=https://auth.meurestaurante.com`.
class ApiConfig {
  const ApiConfig._();

  static const String authServiceUrl = String.fromEnvironment(
    'AUTH_SERVICE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const String restaurantServiceUrl = String.fromEnvironment(
    'RESTAURANT_SERVICE_URL',
    defaultValue: 'http://10.0.2.2:8001',
  );

  static const String diningServiceUrl = String.fromEnvironment(
    'DINING_SERVICE_URL',
    defaultValue: 'http://10.0.2.2:8003',
  );

  static const String menuServiceUrl = String.fromEnvironment(
    'MENU_SERVICE_URL',
    defaultValue: 'http://10.0.2.2:8002',
  );

  static const String orderServiceUrl = String.fromEnvironment(
    'ORDER_SERVICE_URL',
    defaultValue: 'http://10.0.2.2:8005',
  );
}
