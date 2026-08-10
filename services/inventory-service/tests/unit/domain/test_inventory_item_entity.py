"""Testes da entidade de domínio `InventoryItem`."""

import uuid
from typing import Any

import pytest
from src.domain.entities.inventory_item import InventoryItem, InventoryUnit
from src.domain.exceptions import InsufficientStockException


def _make_item(**overrides: Any) -> InventoryItem:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "name": "Pão de Hambúrguer",
        "unit": InventoryUnit.UN,
        "current_quantity": 10.0,
        "minimum_quantity": 5.0,
    }
    defaults.update(overrides)
    return InventoryItem(**defaults)


def test_item_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="nome"):
        _make_item(name="   ")


def test_item_rejects_negative_initial_quantity() -> None:
    with pytest.raises(ValueError, match="negativa"):
        _make_item(current_quantity=-1.0)


def test_is_below_minimum_when_quantity_under_threshold() -> None:
    item = _make_item(current_quantity=2.0, minimum_quantity=5.0)
    assert item.is_below_minimum is True


def test_is_not_below_minimum_when_quantity_meets_threshold() -> None:
    item = _make_item(current_quantity=5.0, minimum_quantity=5.0)
    assert item.is_below_minimum is False


def test_increase_adds_to_current_quantity() -> None:
    item = _make_item(current_quantity=10.0)
    item.increase(5.0)
    assert item.current_quantity == 15.0


def test_increase_rejects_non_positive_quantity() -> None:
    item = _make_item()
    with pytest.raises(ValueError, match="positiva"):
        item.increase(0)


def test_decrease_subtracts_from_current_quantity() -> None:
    item = _make_item(current_quantity=10.0)
    item.decrease(4.0)
    assert item.current_quantity == 6.0


def test_decrease_raises_when_insufficient_stock() -> None:
    item = _make_item(current_quantity=3.0)
    with pytest.raises(InsufficientStockException):
        item.decrease(5.0)


def test_decrease_allows_negative_when_flag_set() -> None:
    item = _make_item(current_quantity=3.0)
    item.decrease(5.0, allow_negative=True)
    assert item.current_quantity == -2.0


def test_adjust_to_counted_quantity_returns_positive_delta() -> None:
    item = _make_item(current_quantity=10.0)
    delta = item.adjust_to_counted_quantity(15.0)
    assert delta == 5.0
    assert item.current_quantity == 15.0


def test_adjust_to_counted_quantity_returns_negative_delta() -> None:
    item = _make_item(current_quantity=10.0)
    delta = item.adjust_to_counted_quantity(6.0)
    assert delta == -4.0
    assert item.current_quantity == 6.0
