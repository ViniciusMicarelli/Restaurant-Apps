"""Testes unitários de `RegisterUserUseCase` (repositório fake, sem DB)."""

import uuid

import pytest
from restaurant_security.hash import verify_password, verify_pin
from src.application.use_cases.register_user import RegisterUserUseCase
from src.domain.entities.user import UserRole
from src.domain.exceptions import DuplicateEmailError
from tests.unit.fakes import FakeUserStore


@pytest.mark.asyncio
async def test_register_user_persists_hashed_password_and_pin() -> None:
    store = FakeUserStore()
    tenant_id = uuid.uuid4()
    use_case = RegisterUserUseCase(user_repository=store.scoped_to(tenant_id), user_lookup=store)

    response = await use_case.execute(
        tenant_id=tenant_id,
        email="joao@burgerhouse.com.br",
        password="SenhaForte@123",
        name="Garçom João",
        role=UserRole.WAITER,
        pin="1234",
    )

    assert response.tenant_id == tenant_id
    assert response.role == UserRole.WAITER

    stored_user = await store.find_by_email("joao@burgerhouse.com.br")
    assert stored_user is not None
    assert stored_user.hashed_password != "SenhaForte@123"
    assert verify_password("SenhaForte@123", stored_user.hashed_password)
    assert stored_user.pin_hash is not None
    assert verify_pin("1234", stored_user.pin_hash)


@pytest.mark.asyncio
async def test_register_user_without_pin_leaves_pin_hash_none() -> None:
    store = FakeUserStore()
    tenant_id = uuid.uuid4()
    use_case = RegisterUserUseCase(user_repository=store.scoped_to(tenant_id), user_lookup=store)

    await use_case.execute(
        tenant_id=tenant_id,
        email="gerente@burgerhouse.com.br",
        password="SenhaForte@123",
        name="Gerente",
        role=UserRole.MANAGER,
    )

    stored_user = await store.find_by_email("gerente@burgerhouse.com.br")
    assert stored_user is not None
    assert stored_user.pin_hash is None


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate_email_globally() -> None:
    store = FakeUserStore()
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    use_case_a = RegisterUserUseCase(user_repository=store.scoped_to(tenant_a), user_lookup=store)
    use_case_b = RegisterUserUseCase(user_repository=store.scoped_to(tenant_b), user_lookup=store)

    await use_case_a.execute(
        tenant_id=tenant_a,
        email="dono@burgerhouse.com.br",
        password="SenhaForte@123",
        name="Dono",
        role=UserRole.RESTAURANT_OWNER,
    )

    with pytest.raises(DuplicateEmailError):
        await use_case_b.execute(
            tenant_id=tenant_b,
            email="dono@burgerhouse.com.br",
            password="OutraSenha@123",
            name="Outro Dono",
            role=UserRole.RESTAURANT_OWNER,
        )
