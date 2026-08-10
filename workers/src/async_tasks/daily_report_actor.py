"""Actor Dramatiq: geração do relatório diário de vendas (tarefa agendada).

Escopo Tier B (base sólida): um log estruturado representa a geração do
relatório. Agregação real de vendas (`DailySalesReport`, curva ABC, DRE
simplificado — docs/modules/module_breakdown.md §12) depende de uma API de
consulta agregada do `order-service` ainda não exposta nesta fase, e fica
para um trabalho futuro sem alterar o contrato deste actor.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import dramatiq

logger = logging.getLogger(__name__)


@dramatiq.actor(max_retries=1, queue_name="reports")
def generate_daily_sales_report() -> None:
    """Disparado periodicamente pelo agendador (`src/schedulers/daily_report_scheduler.py`)."""
    logger.info(
        "DAILY_SALES_REPORT_GENERATED (simulado) report_date=%s",
        datetime.now(UTC).date().isoformat(),
    )
