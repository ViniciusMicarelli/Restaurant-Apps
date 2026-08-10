"""Entidade de Domínio: Categoria do Cardápio."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class Category:
    """Agrupamento de produtos no cardápio, com ordenação customizada pelo restaurante."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    display_order: int = 0
    is_active: bool = True
