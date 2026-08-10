"""Testes das entidades de domínio `Recipe`/`RecipeItem`."""

import uuid

import pytest
from src.domain.entities.recipe import Recipe, RecipeItem


def test_recipe_item_rejects_non_positive_quantity() -> None:
    with pytest.raises(ValueError, match="positiva"):
        RecipeItem(inventory_item_id=uuid.uuid4(), quantity_required=0)


def test_recipe_requires_at_least_one_item() -> None:
    with pytest.raises(ValueError, match="ao menos um insumo"):
        Recipe(id=uuid.uuid4(), tenant_id=uuid.uuid4(), product_id=uuid.uuid4(), items=[])


def test_replace_items_updates_the_recipe() -> None:
    recipe = Recipe(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        items=[RecipeItem(inventory_item_id=uuid.uuid4(), quantity_required=1.0)],
    )
    new_items = [
        RecipeItem(inventory_item_id=uuid.uuid4(), quantity_required=2.0),
        RecipeItem(inventory_item_id=uuid.uuid4(), quantity_required=3.0),
    ]

    recipe.replace_items(new_items)

    assert recipe.items == new_items


def test_replace_items_rejects_empty_list() -> None:
    recipe = Recipe(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        items=[RecipeItem(inventory_item_id=uuid.uuid4(), quantity_required=1.0)],
    )
    with pytest.raises(ValueError, match="ao menos um insumo"):
        recipe.replace_items([])
