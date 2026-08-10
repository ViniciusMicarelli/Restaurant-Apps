"""Agendador do relatório diário de vendas (APScheduler → actor Dramatiq).

Processo separado (`python -m src.schedulers.daily_report_scheduler`) que
apenas AGENDA: a execução de fato acontece no worker Dramatiq que consome a
fila `reports` (`dramatiq src.async_tasks`), preservando a separação entre
"quem decide quando rodar" (agendador) e "quem processa" (worker) — permite
escalar os dois independentemente.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.async_tasks.daily_report_actor import generate_daily_sales_report

logger = logging.getLogger(__name__)

DAILY_REPORT_JOB_ID = "daily_sales_report"


def trigger_daily_report() -> None:
    """Enfileira a geração do relatório diário (chamado pelo job agendado)."""
    logger.info("Agendador disparou a geração do relatório diário de vendas.")
    generate_daily_sales_report.send()


def build_scheduler() -> BlockingScheduler:
    """Monta o `BlockingScheduler` com o job diário configurado (00:05 UTC)."""
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        trigger_daily_report,
        trigger=CronTrigger(hour=0, minute=5),
        id=DAILY_REPORT_JOB_ID,
        replace_existing=True,
    )
    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_scheduler().start()
