"""Testes da entidade de domínio `Restaurant`/`RestaurantBranding`."""

import uuid

from src.domain.entities.restaurant import Restaurant, RestaurantBranding


def test_branding_css_variables_generation() -> None:
    branding = RestaurantBranding(
        primary_color="#EA1D2C",
        secondary_color="#1E293B",
        accent_color="#059669",
        font_family="Inter",
        border_radius="lg",
    )

    css_vars = branding.to_css_variables()

    assert css_vars["--primary-color"] == "#EA1D2C"
    assert css_vars["--font-family"] == "'Inter', sans-serif"
    assert css_vars["--border-radius"] == "16px"


def test_branding_border_radius_maps_small_to_8px() -> None:
    branding = RestaurantBranding(border_radius="sm")

    assert branding.to_css_variables()["--border-radius"] == "8px"


def test_restaurant_entity_uses_default_branding_when_not_provided() -> None:
    restaurant = Restaurant(
        id=uuid.uuid4(),
        slug="pizzaria-napoles",
        trade_name="Pizzaria Nápoles",
        legal_name="Pizzaria Nápoles Ltda",
        cnpj="11.222.333/0001-44",
        phone="(11) 98888-1111",
        service_fee_percent=12.5,
    )

    assert restaurant.is_active is True
    assert restaurant.currency == "BRL"
    assert restaurant.branding.primary_color == "#EA1D2C"
