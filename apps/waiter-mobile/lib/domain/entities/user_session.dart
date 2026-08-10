/// Sessão do usuário autenticado (garçom/caixa/cozinha) — espelha
/// `TokenResponse`/`UserProfileResponse` do `auth-service`.
class UserSession {
  const UserSession({
    required this.userId,
    required this.tenantId,
    required this.name,
    required this.email,
    required this.role,
    required this.accessToken,
    required this.refreshToken,
  });

  final String userId;
  final String tenantId;
  final String name;
  final String email;
  final String role;
  final String accessToken;
  final String refreshToken;
}
