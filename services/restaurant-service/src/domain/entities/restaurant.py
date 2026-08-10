"""Entidades do Domínio de Restaurantes e Branding White-Label.

Cada `Restaurant` é, ele mesmo, o limite de tenant do resto da plataforma:
`Restaurant.id` é o `tenant_id` usado por todos os outros microsserviços
(`auth-service`, `menu-service`, etc.) — não existe um "tenant_id" separado
aqui, e por isso `RestaurantModel` NÃO herda de `TenantAwareModel`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class RestaurantBranding:
    """Objeto de Valor representando a identidade visual e tema White-Label do Restaurante."""

    primary_color: str = "#EA1D2C"
    secondary_color: str = "#1F2937"
    accent_color: str = "#00B469"
    background_color: str = "#F7F7F7"
    surface_color: str = "#FFFFFF"
    theme_mode: str = "light"
    logo_url: str = ""
    favicon_url: str = ""
    banner_url: str = ""
    font_family: str = "Inter"
    border_radius: str = "lg"

    def to_css_variables(self) -> dict[str, str]:
        """Converte o objeto de branding em variáveis CSS utilizáveis pelo frontend."""
        return {
            "--primary-color": self.primary_color,
            "--secondary-color": self.secondary_color,
            "--accent-color": self.accent_color,
            "--bg-color": self.background_color,
            "--surface-color": self.surface_color,
            "--font-family": f"'{self.font_family}', sans-serif",
            "--border-radius": "16px" if self.border_radius == "lg" else "8px",
        }


@dataclass
class Restaurant:
    """Entidade Raiz do Agregado de Restaurante — também o limite de tenant da plataforma.

    Attributes:
        id: UUIDv7 do restaurante, reutilizado como `tenant_id` em todos os
            demais microsserviços.
        slug: Identificador amigável de URL (subdomínio/cardápio digital).
        trade_name: Nome Fantasia.
        legal_name: Razão Social.
        cnpj: Registro CNPJ.
        phone: Telefone/WhatsApp de contato.
        currency: Moeda operacional (ISO 4217, ex: "BRL").
        service_fee_percent: Taxa de serviço padrão.
        is_active: Indica se a conta está ativa no SaaS.
        branding: Configurações visuais White-Label.
    """

    id: uuid.UUID
    slug: str
    trade_name: str
    legal_name: str
    cnpj: str
    phone: str
    currency: str = "BRL"
    service_fee_percent: float = 10.0
    is_active: bool = True
    branding: RestaurantBranding = field(default_factory=RestaurantBranding)
