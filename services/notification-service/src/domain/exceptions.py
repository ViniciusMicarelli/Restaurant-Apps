"""Exceções de domínio específicas do serviço de Notificações."""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class ChannelMismatchException(BaseDomainException):
    """Disparada ao enfileirar uma notificação num canal diferente do template referenciado."""

    def __init__(self, template_code: str) -> None:
        super().__init__(
            message=f"O canal informado não corresponde ao canal do template '{template_code}'.",
            code="CHANNEL_MISMATCH",
            status_code=422,
        )


class DuplicateTemplateCodeException(BaseDomainException):
    """Disparada ao tentar cadastrar um código de template já existente para o tenant."""

    def __init__(self, code: str) -> None:
        super().__init__(
            message=f"Já existe um template com o código '{code}' para este restaurante.",
            code="DUPLICATE_TEMPLATE_CODE",
            status_code=409,
        )


class TemplateContextError(BaseDomainException):
    """Disparada quando o contexto fornecido não preenche todos os placeholders do template."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="TEMPLATE_CONTEXT_ERROR", status_code=422)


class InvalidTemplateError(BaseDomainException):
    """Disparada quando os dados do template violam uma regra de domínio (ex: e-mail sem assunto)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="INVALID_TEMPLATE", status_code=422)
