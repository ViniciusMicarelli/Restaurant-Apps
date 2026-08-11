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

// Riverpod 3: `StateNotifier` saiu do pacote principal — `Notifier` é o
// substituto direto. Injeção de dependência muda de construtor (`this._storage`)
// pra `build()` lendo via `ref.watch` (é assim que o `Notifier` acessa
// `ref` — só existe depois que o provider é inicializado, não no
// construtor, que agora é sempre sem argumentos).
class SessionController extends Notifier<UserSession?> {
  late final SessionStorage _storage;

  @override
  UserSession? build() {
    _storage = ref.watch(sessionStorageProvider);
    return _storage.load();
  }

  Future<void> login(UserSession session) async {
    await _storage.save(session);
    state = session;
  }

  Future<void> logout() async {
    await _storage.clear();
    state = null;
  }
}

final sessionControllerProvider =
    NotifierProvider<SessionController, UserSession?>(SessionController.new);
