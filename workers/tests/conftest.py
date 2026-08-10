"""Fixtures/configuração compartilhada dos testes de `workers`.

Define as variáveis de ambiente exigidas por `WorkerSettings` antes de
qualquer import de `src.*` — os testes chamam os actors diretamente
(bypassando o broker Dramatiq), então um Redis real não é necessário.
"""

from __future__ import annotations

import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("REDIS__HOST", "127.0.0.1")
os.environ.setdefault("REDIS__PORT", "6379")
os.environ.setdefault("REDIS__DB", "12")
os.environ.setdefault("RABBITMQ__HOST", "127.0.0.1")
os.environ.setdefault("RABBITMQ__PORT", "1")
os.environ.setdefault("RABBITMQ__USER", "unused")
os.environ.setdefault("RABBITMQ__PASSWORD", "unused")
