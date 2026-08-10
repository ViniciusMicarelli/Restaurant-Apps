import 'package:shared_preferences/shared_preferences.dart';

import '../domain/entities/user_session.dart';

/// Persistência local da sessão (tokens JWT) — sobrevive ao fechamento do
/// app, para o garçom não precisar digitar o PIN a cada abertura.
class SessionStorage {
  const SessionStorage(this._preferences);

  static const _keyAccessToken = 'session.access_token';
  static const _keyRefreshToken = 'session.refresh_token';
  static const _keyUserId = 'session.user_id';
  static const _keyTenantId = 'session.tenant_id';
  static const _keyName = 'session.name';
  static const _keyEmail = 'session.email';
  static const _keyRole = 'session.role';

  final SharedPreferences _preferences;

  Future<void> save(UserSession session) async {
    await _preferences.setString(_keyAccessToken, session.accessToken);
    await _preferences.setString(_keyRefreshToken, session.refreshToken);
    await _preferences.setString(_keyUserId, session.userId);
    await _preferences.setString(_keyTenantId, session.tenantId);
    await _preferences.setString(_keyName, session.name);
    await _preferences.setString(_keyEmail, session.email);
    await _preferences.setString(_keyRole, session.role);
  }

  UserSession? load() {
    final accessToken = _preferences.getString(_keyAccessToken);
    final refreshToken = _preferences.getString(_keyRefreshToken);
    final userId = _preferences.getString(_keyUserId);
    final tenantId = _preferences.getString(_keyTenantId);
    final name = _preferences.getString(_keyName);
    final email = _preferences.getString(_keyEmail);
    final role = _preferences.getString(_keyRole);

    if (accessToken == null ||
        refreshToken == null ||
        userId == null ||
        tenantId == null ||
        name == null ||
        email == null ||
        role == null) {
      return null;
    }

    return UserSession(
      userId: userId,
      tenantId: tenantId,
      name: name,
      email: email,
      role: role,
      accessToken: accessToken,
      refreshToken: refreshToken,
    );
  }

  Future<void> clear() async {
    await _preferences.remove(_keyAccessToken);
    await _preferences.remove(_keyRefreshToken);
    await _preferences.remove(_keyUserId);
    await _preferences.remove(_keyTenantId);
    await _preferences.remove(_keyName);
    await _preferences.remove(_keyEmail);
    await _preferences.remove(_keyRole);
  }
}
