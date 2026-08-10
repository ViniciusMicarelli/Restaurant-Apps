"""Actors Dramatiq registrados no broker Redis (ADR-002).

Importa `src.broker` por efeito colateral: garante que `dramatiq.set_broker`
já foi chamado antes de qualquer `@dramatiq.actor` deste pacote ser avaliado.

Também importa cada módulo de actor por efeito colateral — o processo
worker é iniciado via `dramatiq src.async_tasks` (CLI oficial do Dramatiq),
que importa apenas este pacote; sem os imports abaixo, os actors nunca
seriam registrados no broker e o worker não processaria nenhuma mensagem.
"""

from __future__ import annotations

from src import broker  # noqa: F401
from src.async_tasks import daily_report_actor, notification_actor  # noqa: F401
