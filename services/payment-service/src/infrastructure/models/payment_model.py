"""Modelo SQLAlchemy 2.0 da tabela `payments` (`payments_db`).

As parcelas (`PaymentSplit`) são armazenadas como JSON embutido — sempre
lidas e escritas junto com o pagamento como um todo (agregado único).
"""

from __future__ import annotations

import uuid
from typing import Any

from restaurant_database import GUID, TenantAwareModel
from sqlalchemy import JSON, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.payment import PaymentStatus


class PaymentModel(TenantAwareModel):
    __tablename__ = "payments"

    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    # Nulo para pagamentos de autoatendimento do cliente (US-05.4) — não há
    # operador/caixa físico nesse canal.
    cash_register_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    # Referência autoritativa da comanda paga, quando aplicável — "Payment
    # por Comanda" (nulo em pagamentos de pedido avulso e em registros
    # anteriores a esta coluna).
    command_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    splits: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), nullable=False, default=PaymentStatus.APPROVED
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    card_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    card_holder_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    signature_data: Mapped[str | None] = mapped_column(Text, nullable=True)
