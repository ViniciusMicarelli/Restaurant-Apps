"""Testes do agendador do relatório diário (`APScheduler` → actor Dramatiq)."""

from __future__ import annotations

from unittest.mock import patch

from apscheduler.triggers.cron import CronTrigger
from src.schedulers.daily_report_scheduler import (
    DAILY_REPORT_JOB_ID,
    build_scheduler,
    trigger_daily_report,
)


def test_build_scheduler_registers_the_daily_job() -> None:
    scheduler = build_scheduler()

    job = scheduler.get_job(DAILY_REPORT_JOB_ID)

    assert job is not None
    assert isinstance(job.trigger, CronTrigger)


def test_trigger_daily_report_enqueues_the_actor() -> None:
    with patch("src.schedulers.daily_report_scheduler.generate_daily_sales_report") as mock_actor:
        trigger_daily_report()

    mock_actor.send.assert_called_once_with()
