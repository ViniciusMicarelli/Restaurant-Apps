"""Entidade `Supplier` — fornecedor de insumos (docs/modules/module_breakdown.md §7)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class Supplier:
    """Fornecedor associado a um ou mais insumos do estoque."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    contact_phone: str | None = None
    contact_email: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("O nome do fornecedor não pode ser vazio.")
