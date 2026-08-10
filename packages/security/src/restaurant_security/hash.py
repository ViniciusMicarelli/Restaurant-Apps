"""Módulo de Hashing Seguro de Senhas e PINs com Argon2id.

Fornece funções de criptografia de alto desempenho e segurança contra ataques
de força bruta e rainbow tables.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Instância única do Argon2id recomendada pela OWASP
_ph = PasswordHasher(
    time_cost=3,  # 3 iterações
    memory_cost=65536,  # 64 MB de memória
    parallelism=4,  # 4 threads
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Gera o hash Argon2id seguro para a senha do usuário.

    Args:
        password: Senha em texto claro.

    Returns:
        String formatada do hash Argon2id incluindo salt e parâmetros.
    """
    return _ph.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto claro bate com o hash Argon2id gravado.

    Args:
        password: Senha em texto claro.
        hashed_password: Hash Argon2id previamente gerado.

    Returns:
        True se a senha for válida; False caso contrário.
    """
    try:
        return _ph.verify(hashed_password, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def hash_pin(pin: str) -> str:
    """Gera o hash seguro para o PIN de 4 dígitos do garçom/caixa."""
    return hash_password(pin)


def verify_pin(pin: str, hashed_pin: str) -> bool:
    """Verifica o PIN de 4 dígitos informado pelo funcionário no POS/App Garçom."""
    return verify_password(pin, hashed_pin)
