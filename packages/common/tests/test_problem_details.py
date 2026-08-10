"""Testes do handler global RFC 7807 (`register_exception_handlers`)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from restaurant_common.problem_details import register_exception_handlers
from restaurant_core.exceptions import ForbiddenException, ResourceNotFoundException


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom/not-found")
    async def _raise_not_found() -> None:
        raise ResourceNotFoundException("Order", "ord-123")

    @app.get("/boom/forbidden")
    async def _raise_forbidden() -> None:
        raise ForbiddenException()

    return app


def test_domain_exception_is_converted_to_rfc7807_problem_json() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/boom/not-found")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"

    body = response.json()
    assert body["status"] == 404
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "Order" in body["detail"]
    assert body["errors"] == {"resource_name": "Order", "resource_id": "ord-123"}


def test_forbidden_exception_maps_to_403_with_default_message() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/boom/forbidden")

    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "FORBIDDEN"
    assert body["title"] == "ForbiddenException"
