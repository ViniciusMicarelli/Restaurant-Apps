/// URLs-base dos microsserviços consumidos pelo app do cliente.
///
/// Nenhuma URL é hardcoded para produção: os valores abaixo são apenas o
/// padrão de desenvolvimento (`docker-compose.dev.yml`), sobrescrevível em
/// tempo de build via `--dart-define`.
class ApiConfig {
  const ApiConfig._();

  static const String restaurantServiceUrl = String.fromEnvironment(
    'RESTAURANT_SERVICE_URL',
    defaultValue: 'http://10.0.2.2:8001',
  );

  static const String menuServiceUrl = String.fromEnvironment(
    'MENU_SERVICE_URL',
    defaultValue: 'http://10.0.2.2:8002',
  );
}
