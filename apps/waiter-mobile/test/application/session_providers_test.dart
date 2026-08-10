import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:waiter_mobile/application/session_providers.dart';
import 'package:waiter_mobile/domain/entities/user_session.dart';

const _session = UserSession(
  userId: 'u1',
  tenantId: 't1',
  name: 'Ana',
  email: 'ana@x.com',
  role: 'WAITER',
  accessToken: 'access-1',
  refreshToken: 'refresh-1',
);

void main() {
  late ProviderContainer container;

  setUp(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    container = ProviderContainer(
      overrides: [sharedPreferencesProvider.overrideWithValue(prefs)],
    );
  });

  tearDown(() => container.dispose());

  test('starts with no session when nothing was persisted', () {
    expect(container.read(sessionControllerProvider), isNull);
  });

  test('login persists the session and updates the state', () async {
    await container.read(sessionControllerProvider.notifier).login(_session);

    final state = container.read(sessionControllerProvider);
    expect(state, isNotNull);
    expect(state!.name, 'Ana');
    expect(state.accessToken, 'access-1');
  });

  test('logout clears the persisted session', () async {
    final controller = container.read(sessionControllerProvider.notifier);
    await controller.login(_session);

    await controller.logout();

    expect(container.read(sessionControllerProvider), isNull);
  });

  test('a session persisted in a previous app run is restored on start', () async {
    SharedPreferences.setMockInitialValues({
      'session.access_token': 'access-2',
      'session.refresh_token': 'refresh-2',
      'session.user_id': 'u2',
      'session.tenant_id': 't2',
      'session.name': 'Carlos',
      'session.email': 'carlos@x.com',
      'session.role': 'CASHIER',
    });
    final prefs = await SharedPreferences.getInstance();
    final freshContainer = ProviderContainer(
      overrides: [sharedPreferencesProvider.overrideWithValue(prefs)],
    );
    addTearDown(freshContainer.dispose);

    final restored = freshContainer.read(sessionControllerProvider);

    expect(restored, isNotNull);
    expect(restored!.name, 'Carlos');
    expect(restored.role, 'CASHIER');
  });
}
