"""Testes unitários de `GetUserProfileUseCase`."""

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.domain.entities.user import User, UserRole
from tests.unit.fakes import FakeUserStore


@pytest.mark.asyncio
async def test_get_profile_returns_public_fields_for_existing_user() -> None:
    tenant_id = uuid.uuid4()
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="gerente@burgerhouse.com.br",
        hashed_password="hashed",
        name="Gerente",
        role=UserRole.MANAGER,
    )
    store = FakeUserStore([user])
    use_case = GetUserProfileUseCase(user_repository=store.scoped_to(tenant_id))

    profile = await use_case.execute(user_id=user.id)

    assert profile.email == "gerente@burgerhouse.com.br"
    assert profile.role == UserRole.MANAGER
    assert not hasattr(profile, "hashed_password")


@pytest.mark.asyncio
async def test_get_profile_raises_not_found_for_unknown_user() -> None:
    tenant_id = uuid.uuid4()
    use_case = GetUserProfileUseCase(user_repository=FakeUserStore().scoped_to(tenant_id))

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(user_id=uuid.uuid4())
