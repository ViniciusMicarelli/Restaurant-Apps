"""DTOs (Pydantic v2) de Request/Response do serviço de Salão.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from src.domain.entities.command import CommandStatus
from src.domain.entities.queue_entry import QueueStatus
from src.domain.entities.table import TableStatus


class CreateTableRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(..., ge=1)
    capacity: int = Field(..., ge=1, le=50)
    qr_code_url: str = ""


class TableResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    number: int
    capacity: int
    status: TableStatus
    qr_code_url: str


class TableQrSecretResponse(BaseModel):
    secret: str
    expires_at: datetime


class ValidateQrSecretResponse(BaseModel):
    valid: bool
    table_id: uuid.UUID


class OpenCommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_number: int = Field(..., ge=1)
    customer_name: str = Field(..., min_length=1, max_length=150)
    customer_cpf: str | None = Field(default=None, max_length=14)


class UpdateServiceFeeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    charged: bool


class CommandResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    table_id: uuid.UUID
    customer_name: str
    customer_cpf: str | None
    waiter_id: uuid.UUID
    status: CommandStatus
    service_fee_charged: bool
    # Expostos para o dashboard do dono (tempo médio de atendimento por mesa,
    # mesas atendidas no dia) — existiam na entidade desde sempre, só nunca
    # tinham sido colocados no contrato da API.
    opened_at: datetime
    closed_at: datetime | None


class AddQueueEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_name: str = Field(..., min_length=1, max_length=150)
    phone: str = Field(..., min_length=8, max_length=20)
    party_size: int = Field(..., ge=1, le=50)


class QueueEntryResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_name: str
    phone: str
    party_size: int
    status: QueueStatus
    position: int = Field(..., description="Posição na fila (1 = próximo a ser chamado)")
