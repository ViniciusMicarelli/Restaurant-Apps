"""Entidade de Domínio: Mesa do Salão."""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

_QR_SECRET_SAFETY_TTL_SECONDS_DEFAULT = 60 * 60 * 24  # 24h


class TableStatus(StrEnum):
    """Máquina de Estados válida da Mesa."""

    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    WAITING_CLEANING = "WAITING_CLEANING"


_VALID_TRANSITIONS: dict[TableStatus, tuple[TableStatus, ...]] = {
    TableStatus.AVAILABLE: (TableStatus.OCCUPIED, TableStatus.RESERVED),
    TableStatus.OCCUPIED: (TableStatus.WAITING_CLEANING,),
    TableStatus.RESERVED: (TableStatus.OCCUPIED, TableStatus.AVAILABLE),
    TableStatus.WAITING_CLEANING: (TableStatus.AVAILABLE,),
}


@dataclass
class Table:
    """Mesa do salão, identificada por um número único dentro do tenant."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    number: int
    capacity: int
    status: TableStatus = TableStatus.AVAILABLE
    qr_code_url: str = ""
    active_qr_secret: str | None = None
    qr_secret_expires_at: datetime | None = None

    def transition_to(self, new_status: TableStatus) -> None:
        """Aplica uma transição válida de status, ou lança `ValueError`."""
        allowed = _VALID_TRANSITIONS.get(self.status, ())
        if new_status not in allowed:
            raise ValueError(
                f"Transição inválida de mesa: não é permitido ir de '{self.status.value}' para '{new_status.value}'."
            )
        self.status = new_status

    def rotate_qr_secret(self, ttl_seconds: int = _QR_SECRET_SAFETY_TTL_SECONDS_DEFAULT) -> None:
        """Gera uma nova secret opaca para o QR Code da mesa, invalidando
        qualquer secret anterior.

        O limite real de validade é o **ciclo de ocupação da mesa**, não um
        TTL curto: `CloseCommandUseCase` chama este método sempre que a
        comanda é encerrada, então quem já saiu não consegue reaproveitar o
        link pra pedir em nome de outra pessoa que sente na mesma mesa depois.
        `ttl_seconds` é só uma rede de segurança (default 24h) para o caso de
        uma mesa ficar aberta indefinidamente sem ser encerrada — não é o
        mecanismo principal.

        `secrets.token_urlsafe` (não UUIDv7): precisamos de um valor
        imprevisível o bastante para não ser adivinhado/reaproveitado depois
        de expirar, diferente do UUIDv7 (ordenável por tempo, previsível).
        """
        self.active_qr_secret = secrets.token_urlsafe(16)
        self.qr_secret_expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)

    def is_qr_secret_valid(self, secret: str) -> bool:
        if not self.active_qr_secret or not self.qr_secret_expires_at:
            return False
        expires_at = self.qr_secret_expires_at
        if expires_at.tzinfo is None:
            # SQLite (usado nos testes de integração leves, ver
            # tests/integration/conftest.py) devolve datetime naive mesmo com
            # a coluna declarada `DateTime(timezone=True)` — normaliza pra UTC
            # em vez de quebrar a comparação. Postgres/asyncpg em produção já
            # devolve timezone-aware corretamente, então isso é só uma rede de
            # segurança, não muda o comportamento real.
            expires_at = expires_at.replace(tzinfo=UTC)
        if datetime.now(UTC) > expires_at:
            return False
        return secrets.compare_digest(self.active_qr_secret, secret)
