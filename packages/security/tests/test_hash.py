"""Testes do módulo de hashing Argon2id (senhas e PINs)."""

from restaurant_security.hash import hash_password, hash_pin, verify_password, verify_pin


def test_hash_password_never_stores_plaintext() -> None:
    password = "SenhaSegura@2026"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2id$")


def test_verify_password_accepts_correct_and_rejects_incorrect() -> None:
    password = "SenhaSegura@2026"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("SenhaIncorreta", hashed) is False


def test_verify_password_rejects_malformed_hash_without_raising() -> None:
    assert verify_password("qualquer-senha", "hash-corrompido-invalido") is False


def test_hash_pin_and_verify_pin_round_trip() -> None:
    pin = "1234"
    hashed_pin = hash_pin(pin)

    assert verify_pin("1234", hashed_pin) is True
    assert verify_pin("9999", hashed_pin) is False
