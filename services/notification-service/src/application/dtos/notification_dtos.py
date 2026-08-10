"""DTOs (Pydantic v2) de Request/Response do serviço de Notificações.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from src.domain.entities.notification import NotificationStatus
from src.domain.entities.notification_template import NotificationChannel


class CreateNotificationTemplateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, max_length=50)
    channel: NotificationChannel
    body: str = Field(..., min_length=1, max_length=2000)
    subject: str | None = Field(default=None, max_length=200)


class NotificationTemplateResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    code: str
    channel: NotificationChannel
    body: str
    subject: str | None


class QueueNotificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: NotificationChannel
    recipient: str = Field(..., min_length=1, max_length=255)
    template_code: str = Field(..., min_length=1, max_length=50)
    context: dict[str, str] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    channel: NotificationChannel
    recipient: str
    template_code: str
    rendered_body: str
    context: dict[str, str]
    status: NotificationStatus
    error_message: str | None
    created_at: datetime
