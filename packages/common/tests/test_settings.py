"""Testes dos blocos de configuração reutilizáveis."""

from restaurant_common.settings import DatabaseSettings, RabbitMQSettings, RedisSettings


def test_database_settings_builds_correct_asyncpg_dsn() -> None:
    db_settings = DatabaseSettings(
        host="postgres-db", port=5432, user="app", password="s3cr3t", name="menu_db"
    )

    assert db_settings.async_dsn == "postgresql+asyncpg://app:s3cr3t@postgres-db:5432/menu_db"


def test_database_settings_never_exposes_plaintext_password_via_repr() -> None:
    db_settings = DatabaseSettings(
        host="postgres-db", port=5432, user="app", password="s3cr3t", name="menu_db"
    )

    assert "s3cr3t" not in repr(db_settings)
    assert "s3cr3t" not in str(db_settings)


def test_redis_settings_builds_correct_url_with_default_db() -> None:
    redis_settings = RedisSettings(host="redis-cache", port=6379)

    assert redis_settings.url == "redis://redis-cache:6379/0"


def test_redis_settings_builds_correct_url_with_explicit_db() -> None:
    redis_settings = RedisSettings(host="redis-cache", port=6379, db=4)

    assert redis_settings.url == "redis://redis-cache:6379/4"


def test_rabbitmq_settings_builds_correct_amqp_url() -> None:
    rabbit_settings = RabbitMQSettings(host="rabbitmq", port=5672, user="app", password="s3cr3t")

    assert rabbit_settings.url == "amqp://app:s3cr3t@rabbitmq:5672/"
