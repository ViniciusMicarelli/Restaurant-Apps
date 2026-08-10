"""Testes do envelope genérico `PaginatedResponse`."""

from restaurant_common.pagination import PaginatedResponse


def test_has_more_is_true_when_items_do_not_cover_the_full_total() -> None:
    response = PaginatedResponse[int](items=[1, 2, 3], total=10, limit=3, offset=0)

    assert response.has_more is True


def test_has_more_is_false_on_the_last_page() -> None:
    response = PaginatedResponse[int](items=[8, 9, 10], total=10, limit=3, offset=7)

    assert response.has_more is False


def test_has_more_is_false_when_all_items_fit_in_one_page() -> None:
    response = PaginatedResponse[str](items=["a", "b"], total=2, limit=50, offset=0)

    assert response.has_more is False
