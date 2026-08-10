import '../../domain/entities/user_session.dart';

/// Espelha `TokenResponse`/`UserProfileResponse` do `auth-service`.
class TokenResponseDto {
  const TokenResponseDto({
    required this.accessToken,
    required this.refreshToken,
    required this.userId,
    required this.tenantId,
    required this.name,
    required this.email,
    required this.role,
  });

  factory TokenResponseDto.fromJson(Map<String, dynamic> json) {
    final user = json['user'] as Map<String, dynamic>;
    return TokenResponseDto(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      userId: user['id'] as String,
      tenantId: user['tenant_id'] as String,
      name: user['name'] as String,
      email: user['email'] as String,
      role: user['role'] as String,
    );
  }

  final String accessToken;
  final String refreshToken;
  final String userId;
  final String tenantId;
  final String name;
  final String email;
  final String role;

  UserSession toSession() => UserSession(
    userId: userId,
    tenantId: tenantId,
    name: name,
    email: email,
    role: role,
    accessToken: accessToken,
    refreshToken: refreshToken,
  );
}
