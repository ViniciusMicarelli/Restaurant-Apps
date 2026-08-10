"""DTOs (Pydantic v2) de Request/Response do serviço de Cardápio.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5).
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class CreateCategoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100)
    display_order: int = Field(default=0, ge=0)


class CategoryResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    display_order: int
    is_active: bool


class CreateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=150)
    description: str = Field(default="", max_length=1000)
    price: float = Field(..., ge=0)
    cost_price: float = Field(default=0.0, ge=0)
    tax_rate: float = Field(default=0.0, ge=0, le=100)
    photo_url: str = ""
    display_order: int = Field(default=0, ge=0)


class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=150)
    description: str = Field(default="", max_length=1000)
    price: float = Field(..., ge=0)
    is_active: bool = True


class ProductResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    category_id: uuid.UUID
    name: str
    description: str
    price: float
    cost_price: float
    tax_rate: float
    photo_url: str
    display_order: int
    is_active: bool


class AddonOptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100)
    price_delta: float = 0.0


class CreateAddonGroupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=100)
    min_selections: int = Field(default=0, ge=0)
    max_selections: int = Field(default=1, ge=1)
    options: list[AddonOptionRequest] = Field(default_factory=list, min_length=1)


class AddonOptionResponse(BaseModel):
    name: str
    price_delta: float


class AddonGroupResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    product_id: uuid.UUID
    name: str
    min_selections: int
    max_selections: int
    options: list[AddonOptionResponse]


class ProductSearchResultResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    category_id: uuid.UUID
    price: float
    photo_url: str
