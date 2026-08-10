"""Helper interno: monta o DTO de resposta de um `Restaurant` (com CSS vars calculadas)."""

from __future__ import annotations

from src.application.dtos.restaurant_dtos import BrandingResponse, RestaurantResponse
from src.domain.entities.restaurant import Restaurant


def to_restaurant_response(restaurant: Restaurant) -> RestaurantResponse:
    branding = restaurant.branding
    return RestaurantResponse(
        id=restaurant.id,
        slug=restaurant.slug,
        trade_name=restaurant.trade_name,
        legal_name=restaurant.legal_name,
        cnpj=restaurant.cnpj,
        phone=restaurant.phone,
        currency=restaurant.currency,
        service_fee_percent=restaurant.service_fee_percent,
        is_active=restaurant.is_active,
        branding=BrandingResponse(
            primary_color=branding.primary_color,
            secondary_color=branding.secondary_color,
            accent_color=branding.accent_color,
            background_color=branding.background_color,
            surface_color=branding.surface_color,
            theme_mode=branding.theme_mode,
            logo_url=branding.logo_url,
            favicon_url=branding.favicon_url,
            banner_url=branding.banner_url,
            font_family=branding.font_family,
            border_radius=branding.border_radius,
            css_variables=branding.to_css_variables(),
        ),
    )
