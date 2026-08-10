"""Testes do actor Dramatiq `generate_daily_sales_report`."""

from __future__ import annotations

import logging

import pytest
from src.async_tasks.daily_report_actor import generate_daily_sales_report


def test_generate_daily_sales_report_logs_structured_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        generate_daily_sales_report()

    assert len(caplog.records) == 1
    assert "DAILY_SALES_REPORT_GENERATED" in caplog.records[0].getMessage()
