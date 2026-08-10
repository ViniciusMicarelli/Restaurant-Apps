import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../data/session_storage.dart';
import '../domain/entities/user_session.dart';

/// Sobrescrito em `main()` com a instância real (`SharedPreferences.getInstance()`
/// é assíncrono — não dá para resolver de forma síncrona no grafo de providers).
final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError('sharedPreferencesProvider deve ser sobrescrito em main()');
});

final sessionStorageProvider = Provider<SessionStorage>((ref) {
  return SessionStorage(ref.watch(sharedPreferencesProvider));
});

class SessionController extends StateNotifier<UserSession?> {
  SessionController(this._storage) : super(_storage.load());

  final SessionStorage _storage;

  Future<void> login(UserSession session) async {
    await _storage.save(session);
    state = session;
  }

  Future<void> logout() async {
    await _storage.clear();
    state = null;
  }
}

final sessionControllerProvider = StateNotifierProvider<SessionController, UserSession?>((ref) {
  return SessionController(ref.watch(sessionStorageProvider));
});
