"""Testes das dependencies FastAPI de autenticação/RBAC (`rbac.py`)."""

import uuid
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from restaurant_core.exceptions import BaseDomainException
from restaurant_security.jwt import create_access_token, create_refresh_token
from restaurant_security.rbac import CurrentUser, build_get_current_user, require_role

SECRET = "test-secret-key-32-chars-long-security"
USER_ID = str(uuid.uuid4())
TENANT_ID = str(uuid.uuid4())


def _build_test_app() -> FastAPI:
    app = FastAPI()
    get_current_user = build_get_current_user(SECRET)

    # `restaurant_security` não depende de `restaurant_common`, então o app de
    # teste registra localmente um handler mínimo (o real, RFC 7807 completo,
    # vive em `restaurant_common.problem_details` e é usado pelos serviços).
    @app.exception_handler(BaseDomainException)
    async def _handle_domain_exception(_request: Request, exc: BaseDomainException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code, content={"code": exc.code, "detail": exc.message}
        )

    @app.get("/whoami")
    async def _whoami(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> dict[str, str]:
        return {"user_id": str(current_user.user_id), "role": current_user.role}

    @app.get("/managers-only")
    async def _managers_only(
        current_user: Annotated[
            CurrentUser, Depends(require_role(get_current_user, "MANAGER", "RESTAURANT_OWNER"))
        ],
    ) -> dict[str, str]:
        return {"role": current_user.role}

    return app


def test_get_current_user_accepts_valid_access_token() -> None:
    client = TestClient(_build_test_app())
    token = create_access_token(USER_ID, TENANT_ID, "MANAGER", SECRET)

    response = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"user_id": USER_ID, "role": "MANAGER"}


def test_get_current_user_rejects_missing_authorization_header() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/whoami")

    assert response.status_code == 401


def test_get_current_user_rejects_malformed_authorization_header() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/whoami", headers={"Authorization": "NotBearer xyz"})

    assert response.status_code == 401


def test_get_current_user_rejects_invalid_token() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/whoami", headers={"Authorization": "Bearer garbage.token.value"})

    assert response.status_code == 401


def test_get_current_user_rejects_refresh_token_used_as_access_token() -> None:
    client = TestClient(_build_test_app())
    refresh_token = create_refresh_token(USER_ID, TENANT_ID, "MANAGER", SECRET)

    response = client.get("/whoami", headers={"Authorization": f"Bearer {refresh_token}"})

    assert response.status_code == 401


def test_require_role_allows_matching_role() -> None:
    client = TestClient(_build_test_app())
    token = create_access_token(USER_ID, TENANT_ID, "MANAGER", SECRET)

    response = client.get("/managers-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_require_role_rejects_non_matching_role() -> None:
    client = TestClient(_build_test_app())
    token = create_access_token(USER_ID, TENANT_ID, "WAITER", SECRET)

    response = client.get("/managers-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_current_user_carries_parsed_expiration() -> None:
    get_current_user = build_get_current_user(SECRET)
    token = create_access_token(USER_ID, TENANT_ID, "MANAGER", SECRET, expires_delta_minutes=15)

    current_user = await get_current_user(authorization=f"Bearer {token}")

    assert current_user.expires_at.timestamp() > 0
