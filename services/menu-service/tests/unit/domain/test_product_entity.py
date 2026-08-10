"""Testes das entidades de domínio `Product`/`AddonGroup`."""

import uuid

import pytest
from src.domain.entities.addon import AddonGroup, AddonOption
from src.domain.entities.product import Product


def test_product_margin_is_price_minus_cost() -> None:
    product = Product(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        category_id=uuid.uuid4(),
        name="X-Burger",
        price=25.0,
        cost_price=10.0,
    )

    assert product.margin == 15.0


def test_product_rejects_negative_price() -> None:
    with pytest.raises(ValueError, match="preço"):
        Product(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            name="X-Burger",
            price=-1.0,
        )


def test_product_rejects_negative_cost_price() -> None:
    with pytest.raises(ValueError, match="custo"):
        Product(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            name="X-Burger",
            price=10.0,
            cost_price=-1.0,
        )


def test_addon_group_accepts_valid_min_max() -> None:
    group = AddonGroup(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        name="Ponto da carne",
        min_selections=1,
        max_selections=1,
        options=[AddonOption(name="Mal passado"), AddonOption(name="Bem passado")],
    )

    assert len(group.options) == 2


def test_addon_group_rejects_negative_min_selections() -> None:
    with pytest.raises(ValueError, match="min_selections"):
        AddonGroup(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            name="X",
            min_selections=-1,
            max_selections=1,
        )


def test_addon_group_rejects_max_lower_than_min() -> None:
    with pytest.raises(ValueError, match="max_selections"):
        AddonGroup(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            name="X",
            min_selections=2,
            max_selections=1,
        )
