"""Testes unitários da extração de IP do rate limiter (docs/SECURITY.md
§2.7) — confirma que `X-Forwarded-For` só é confiado quando
`trust_proxy_headers=True` (produção, atrás do Nginx), e que só o ÚLTIMO
valor da cadeia é usado (o único que o Nginx garante não ter sido forjado
pelo cliente)."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from src.config import settings
from src.presentation.api.v1.dependencies import _extract_client_ip
from starlette.requests import Request


def _build_request(*, client_host: str | None, forwarded_for: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if forwarded_for is not None:
        headers.append((b"x-forwarded-for", forwarded_for.encode()))
    scope = {
        "type": "http",
        "headers": headers,
        "client": (client_host, 12345) if client_host is not None else None,
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def _restore_trust_proxy_headers() -> Generator[None, None, None]:
    original = settings.trust_proxy_headers
    yield
    settings.trust_proxy_headers = original


def test_uses_request_client_host_when_not_trusting_proxy_headers() -> None:
    settings.trust_proxy_headers = False
    request = _build_request(client_host="10.0.0.5", forwarded_for="1.2.3.4")

    assert _extract_client_ip(request) == "10.0.0.5"  # header ignorado mesmo presente


def test_uses_last_forwarded_for_value_when_trusting_proxy_headers() -> None:
    """O Nginx só garante o ÚLTIMO valor — os anteriores podem ter sido
    forjados pelo próprio cliente na requisição original."""
    settings.trust_proxy_headers = True
    request = _build_request(client_host="172.19.0.5", forwarded_for="1.2.3.4, 172.19.0.5")

    assert _extract_client_ip(request) == "172.19.0.5"


def test_falls_back_to_client_host_when_trusting_but_header_absent() -> None:
    settings.trust_proxy_headers = True
    request = _build_request(client_host="10.0.0.9")

    assert _extract_client_ip(request) == "10.0.0.9"


def test_returns_unknown_when_no_client_and_no_header() -> None:
    settings.trust_proxy_headers = False
    request = _build_request(client_host=None)

    assert _extract_client_ip(request) == "unknown"
