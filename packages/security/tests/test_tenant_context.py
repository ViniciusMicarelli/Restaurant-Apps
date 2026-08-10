"""Testes do `TenantContextMiddleware` e do `ContextVar` de tenant corrente."""

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token
from restaurant_security.tenant_context import (
    TenantContextMiddleware,
    get_current_tenant_id_or_none,
)

SECRET = "test-secret-key-32-chars-long-security"


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(TenantContextMiddleware, jwt_secret_key=SECRET)

    @app.get("/tenant")
    async def _tenant() -> dict[str, str | None]:
        tenant_id = get_current_tenant_id_or_none()
        return {"tenant_id": str(tenant_id) if tenant_id else None}

    return app


def test_middleware_resolves_tenant_id_from_valid_bearer_jwt() -> None:
    client = TestClient(_build_test_app())
    tenant_id = str(uuid.uuid4())
    token = create_access_token(str(uuid.uuid4()), tenant_id, "MANAGER", SECRET)

    response = client.get("/tenant", headers={"Authorization": f"Bearer {token}"})

    assert response.json() == {"tenant_id": tenant_id}


def test_middleware_falls_back_to_x_tenant_id_header_without_jwt() -> None:
    client = TestClient(_build_test_app())
    tenant_id = str(uuid.uuid4())

    response = client.get("/tenant", headers={"X-Tenant-Id": tenant_id})

    assert response.json() == {"tenant_id": tenant_id}


def test_middleware_prefers_jwt_tenant_over_header_when_both_present() -> None:
    client = TestClient(_build_test_app())
    jwt_tenant_id = str(uuid.uuid4())
    header_tenant_id = str(uuid.uuid4())
    token = create_access_token(str(uuid.uuid4()), jwt_tenant_id, "MANAGER", SECRET)

    response = client.get(
        "/tenant",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-Id": header_tenant_id},
    )

    assert response.json() == {"tenant_id": jwt_tenant_id}


def test_middleware_leaves_tenant_none_when_nothing_is_present() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/tenant")

    assert response.json() == {"tenant_id": None}


def test_middleware_ignores_malformed_x_tenant_id_header() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/tenant", headers={"X-Tenant-Id": "not-a-uuid"})

    assert response.json() == {"tenant_id": None}


def test_context_var_does_not_leak_between_requests() -> None:
    client = TestClient(_build_test_app())
    tenant_id = str(uuid.uuid4())
    token = create_access_token(str(uuid.uuid4()), tenant_id, "MANAGER", SECRET)

    first = client.get("/tenant", headers={"Authorization": f"Bearer {token}"})
    second = client.get("/tenant")

    assert first.json() == {"tenant_id": tenant_id}
    assert second.json() == {"tenant_id": None}
