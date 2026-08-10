"""DTOs (Pydantic v2) de Request/Response do serviço de Restaurantes.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5) — proteção
contra Mass Assignment.
"""

from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CreateRestaurantRequest(BaseModel):
    """Payload público de criação de um novo restaurante (bootstrap de um tenant novo)."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(..., min_length=3, max_length=80)
    trade_name: str = Field(..., min_length=2, max_length=150)
    legal_name: str = Field(..., min_length=2, max_length=150)
    cnpj: str = Field(..., min_length=14, max_length=18)
    phone: str = Field(..., min_length=8, max_length=20)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    service_fee_percent: float = Field(default=10.0, ge=0, le=100)

    @field_validator("slug")
    @classmethod
    def _slug_must_be_url_safe(cls, slug: str) -> str:
        if not _SLUG_PATTERN.match(slug):
            raise ValueError("O slug deve conter apenas letras minúsculas, números e hífens.")
        return slug


class UpdateRestaurantRequest(BaseModel):
    """Payload de atualização de dados operacionais — apenas o Owner/Manager do próprio tenant."""

    model_config = ConfigDict(extra="forbid")

    trade_name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., min_length=8, max_length=20)
    currency: str = Field(..., min_length=3, max_length=3)
    service_fee_percent: float = Field(..., ge=0, le=100)


class UpdateBrandingRequest(BaseModel):
    """Payload de atualização de tema/branding White-Label."""

    model_config = ConfigDict(extra="forbid")

    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str = "#F7F7F7"
    surface_color: str = "#FFFFFF"
    theme_mode: str = Field(default="light", pattern="^(light|dark|auto)$")
    logo_url: str = ""
    favicon_url: str = ""
    banner_url: str = ""
    font_family: str = "Inter"
    border_radius: str = Field(default="lg", pattern="^(sm|md|lg)$")


class BrandingResponse(BaseModel):
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    surface_color: str
    theme_mode: str
    logo_url: str
    favicon_url: str
    banner_url: str
    font_family: str
    border_radius: str
    css_variables: dict[str, str]


class RestaurantResponse(BaseModel):
    """Resposta pública com os dados de um restaurante."""

    id: uuid.UUID
    slug: str
    trade_name: str
    legal_name: str
    cnpj: str
    phone: str
    currency: str
    service_fee_percent: float
    is_active: bool
    branding: BrandingResponse
