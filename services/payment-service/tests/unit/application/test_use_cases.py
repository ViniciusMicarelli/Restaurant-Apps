"""Testes unitários dos casos de uso do `payment-service` (repositórios fake, sem DB real)."""

from __future__ import annotations

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.payment_dtos import PaymentSplitRequest
from src.application.interfaces.repository_interface import OpenCommandInfo, PayableSummary
from src.application.use_cases.close_cash_register import CloseCashRegisterUseCase
from src.application.use_cases.customer_checkout import CustomerCheckoutUseCase
from src.application.use_cases.get_cash_register import (
    GetCashRegisterUseCase,
    ListCashMovementsUseCase,
)
from src.application.use_cases.get_payment import GetPaymentUseCase, ListPaymentsUseCase
from src.application.use_cases.open_cash_register import OpenCashRegisterUseCase
from src.application.use_cases.process_payment import ProcessPaymentUseCase
from src.application.use_cases.register_cash_movement import RegisterCashMovementUseCase
from src.application.use_cases.staff_checkout import StaffCheckoutUseCase
from src.domain.entities.cash_movement import CashMovementType
from src.domain.entities.cash_register import CashRegister
from src.domain.entities.payment_method import PaymentMethod
from src.domain.exceptions import (
    CashOperationException,
    InvalidTableSecretException,
    NoPayableOrdersError,
    OperatorAlreadyHasOpenCashRegisterException,
    PayableAmountUnavailableException,
    SplitAmountMismatchException,
    UnderpaidCommandException,
)
from tests.unit.fakes import (
    FakeCashMovementStore,
    FakeCashRegisterStore,
    FakeDiningServiceClient,
    FakeIdempotencyStore,
    FakeOrderServiceClient,
    FakePaymentStore,
    FakeRestaurantServiceClient,
)


@pytest.mark.asyncio
async def test_open_cash_register_creates_register_and_opening_movement() -> None:
    tenant_id, operator_id = uuid.uuid4(), uuid.uuid4()
    register_store = FakeCashRegisterStore()
    movement_store = FakeCashMovementStore()
    use_case = OpenCashRegisterUseCase(
        cash_register_repository=register_store, cash_movement_repository=movement_store
    )

    response = await use_case.execute(
        tenant_id=tenant_id, operator_id=operator_id, opening_amount=100.0
    )

    assert response.current_balance == 100.0
    assert len(movement_store.movements) == 1
    assert movement_store.movements[0].movement_type == CashMovementType.OPENING_FLOAT


@pytest.mark.asyncio
async def test_open_cash_register_rejects_second_open_register_for_same_operator() -> None:
    tenant_id, operator_id = uuid.uuid4(), uuid.uuid4()
    existing = CashRegister(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        operator_id=operator_id,
        opening_amount=50.0,
        current_balance=50.0,
    )
    use_case = OpenCashRegisterUseCase(
        cash_register_repository=FakeCashRegisterStore([existing]),
        cash_movement_repository=FakeCashMovementStore(),
    )

    with pytest.raises(OperatorAlreadyHasOpenCashRegisterException):
        await use_case.execute(tenant_id=tenant_id, operator_id=operator_id, opening_amount=100.0)


@pytest.mark.asyncio
async def test_register_cash_movement_supply_increases_balance() -> None:
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        operator_id=uuid.uuid4(),
        opening_amount=100.0,
        current_balance=100.0,
    )
    use_case = RegisterCashMovementUseCase(
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
    )

    response = await use_case.execute(
        cash_register_id=register.id,
        movement_type=CashMovementType.SUPPLY,
        amount=50.0,
        reason=None,
    )

    assert response.amount_delta == 50.0
    assert register.current_balance == 150.0


@pytest.mark.asyncio
async def test_register_cash_movement_sangria_requires_reason() -> None:
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        operator_id=uuid.uuid4(),
        opening_amount=100.0,
        current_balance=100.0,
    )
    use_case = RegisterCashMovementUseCase(
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
    )

    with pytest.raises(CashOperationException, match="motivo"):
        await use_case.execute(
            cash_register_id=register.id,
            movement_type=CashMovementType.SANGRIA,
            amount=20.0,
            reason=None,
        )


@pytest.mark.asyncio
async def test_register_cash_movement_rejects_opening_float_type() -> None:
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        operator_id=uuid.uuid4(),
        opening_amount=100.0,
        current_balance=100.0,
    )
    use_case = RegisterCashMovementUseCase(
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
    )

    with pytest.raises(CashOperationException):
        await use_case.execute(
            cash_register_id=register.id,
            movement_type=CashMovementType.OPENING_FLOAT,
            amount=20.0,
            reason=None,
        )


@pytest.mark.asyncio
async def test_register_cash_movement_not_found_raises() -> None:
    use_case = RegisterCashMovementUseCase(
        cash_register_repository=FakeCashRegisterStore(),
        cash_movement_repository=FakeCashMovementStore(),
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(
            cash_register_id=uuid.uuid4(),
            movement_type=CashMovementType.SUPPLY,
            amount=10.0,
            reason=None,
        )


@pytest.mark.asyncio
async def test_close_cash_register_computes_divergence() -> None:
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        operator_id=uuid.uuid4(),
        opening_amount=100.0,
        current_balance=180.0,
    )
    use_case = CloseCashRegisterUseCase(cash_register_repository=FakeCashRegisterStore([register]))

    response = await use_case.execute(cash_register_id=register.id, counted_amount=175.0)

    assert response.closing_divergence == -5.0
    assert response.status.value == "CLOSED"


@pytest.mark.asyncio
async def test_get_cash_register_not_found_raises() -> None:
    use_case = GetCashRegisterUseCase(cash_register_repository=FakeCashRegisterStore())
    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(cash_register_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_list_cash_movements_filters_by_register() -> None:
    register_id = uuid.uuid4()
    store = FakeCashMovementStore()
    use_case = RegisterCashMovementUseCase(
        cash_register_repository=FakeCashRegisterStore(
            [
                CashRegister(
                    id=register_id,
                    tenant_id=uuid.uuid4(),
                    operator_id=uuid.uuid4(),
                    opening_amount=100.0,
                    current_balance=100.0,
                )
            ]
        ),
        cash_movement_repository=store,
    )
    await use_case.execute(
        cash_register_id=register_id,
        movement_type=CashMovementType.SUPPLY,
        amount=10.0,
        reason=None,
    )

    list_use_case = ListCashMovementsUseCase(cash_movement_repository=store)
    result = await list_use_case.execute(cash_register_id=register_id)

    assert len(result) == 1


@pytest.mark.asyncio
async def test_process_payment_creates_payment_and_moves_cash_balance() -> None:
    tenant_id, order_id = uuid.uuid4(), uuid.uuid4()
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        operator_id=uuid.uuid4(),
        opening_amount=100.0,
        current_balance=100.0,
    )
    use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )

    response = await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        cash_register_id=register.id,
        expected_total=50.0,
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.CASH, amount=50.0)],
    )

    assert response.total_amount == 50.0
    assert register.current_balance == 150.0


@pytest.mark.asyncio
async def test_process_payment_non_cash_split_does_not_move_cash_balance() -> None:
    tenant_id, order_id = uuid.uuid4(), uuid.uuid4()
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        operator_id=uuid.uuid4(),
        opening_amount=100.0,
        current_balance=100.0,
    )
    use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )

    await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        cash_register_id=register.id,
        expected_total=50.0,
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=50.0)],
    )

    assert register.current_balance == 100.0


@pytest.mark.asyncio
async def test_process_payment_rejects_split_mismatch() -> None:
    tenant_id, order_id = uuid.uuid4(), uuid.uuid4()
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        operator_id=uuid.uuid4(),
        opening_amount=100.0,
        current_balance=100.0,
    )
    use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )

    with pytest.raises(SplitAmountMismatchException):
        await use_case.execute(
            tenant_id=tenant_id,
            order_id=order_id,
            cash_register_id=register.id,
            expected_total=50.0,
            splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=40.0)],
        )


@pytest.mark.asyncio
async def test_process_payment_with_same_idempotency_key_returns_same_payment() -> None:
    tenant_id, order_id = uuid.uuid4(), uuid.uuid4()
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        operator_id=uuid.uuid4(),
        opening_amount=100.0,
        current_balance=100.0,
    )
    use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )
    splits = [PaymentSplitRequest(payment_method=PaymentMethod.CASH, amount=50.0)]

    first = await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        cash_register_id=register.id,
        expected_total=50.0,
        splits=splits,
        idempotency_key="key-1",
    )
    second = await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        cash_register_id=register.id,
        expected_total=50.0,
        splits=splits,
        idempotency_key="key-1",
    )

    assert first.id == second.id
    assert register.current_balance == 150.0  # não duplicou a movimentação de caixa


@pytest.mark.asyncio
async def test_process_payment_cash_register_not_found_raises() -> None:
    use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore(),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(
            tenant_id=uuid.uuid4(),
            order_id=uuid.uuid4(),
            cash_register_id=uuid.uuid4(),
            expected_total=50.0,
            splits=[PaymentSplitRequest(payment_method=PaymentMethod.CASH, amount=50.0)],
        )


@pytest.mark.asyncio
async def test_process_payment_without_cash_register_id_approves_card_payment() -> None:
    """Autoatendimento do cliente (US-05.4): sem caixa, cartão/Pix aprovam
    normalmente — não há operador/caixa físico nesse canal."""
    tenant_id, order_id = uuid.uuid4(), uuid.uuid4()
    use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore(),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )

    response = await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        cash_register_id=None,
        expected_total=50.0,
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.CREDIT_CARD, amount=50.0)],
    )

    assert response.total_amount == 50.0
    assert response.cash_register_id is None


@pytest.mark.asyncio
async def test_process_payment_without_cash_register_id_rejects_cash_split() -> None:
    """Dinheiro sem caixa não faz sentido — nunca deveria chegar do canal
    remoto, mas o use case rejeita mesmo assim (defesa em profundidade)."""
    use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore(),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )

    with pytest.raises(CashOperationException):
        await use_case.execute(
            tenant_id=uuid.uuid4(),
            order_id=uuid.uuid4(),
            cash_register_id=None,
            expected_total=50.0,
            splits=[PaymentSplitRequest(payment_method=PaymentMethod.CASH, amount=50.0)],
        )


@pytest.mark.asyncio
async def test_process_payment_persists_command_id_when_paying_a_command() -> None:
    """ "Payment por Comanda": quando o pagamento fecha uma comanda inteira
    (não um pedido avulso), o `command_id` fica gravado como referência
    autoritativa — não depende de qual pedido foi usado como `order_id`."""
    tenant_id, order_id, command_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        operator_id=uuid.uuid4(),
        opening_amount=0.0,
        current_balance=0.0,
    )
    use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )

    response = await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        cash_register_id=register.id,
        command_id=command_id,
        expected_total=50.0,
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=50.0)],
    )

    assert response.command_id == command_id
    assert (
        response.order_id == order_id
    )  # mantido por compatibilidade, não é mais a referência principal


@pytest.mark.asyncio
async def test_process_payment_without_command_id_leaves_it_none() -> None:
    """Pagamento de pedido avulso (sem comanda) continua funcionando como
    antes — `command_id` fica `None`, não é obrigatório."""
    tenant_id, order_id = uuid.uuid4(), uuid.uuid4()
    use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore(),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )

    response = await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        cash_register_id=None,
        expected_total=50.0,
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=50.0)],
    )

    assert response.command_id is None


@pytest.mark.asyncio
async def test_list_payments_filters_by_command_id() -> None:
    tenant_id = uuid.uuid4()
    command_a, command_b = uuid.uuid4(), uuid.uuid4()
    use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore(),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )
    store = use_case.payment_repository
    await use_case.execute(
        tenant_id=tenant_id,
        order_id=uuid.uuid4(),
        cash_register_id=None,
        command_id=command_a,
        expected_total=10.0,
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=10.0)],
    )
    await use_case.execute(
        tenant_id=tenant_id,
        order_id=uuid.uuid4(),
        cash_register_id=None,
        command_id=command_b,
        expected_total=20.0,
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=20.0)],
    )

    result = await ListPaymentsUseCase(payment_repository=store).execute(command_id=command_a)

    assert len(result) == 1
    assert result[0].command_id == command_a


@pytest.mark.asyncio
async def test_get_payment_not_found_raises() -> None:
    use_case = GetPaymentUseCase(payment_repository=FakePaymentStore())
    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(payment_id=uuid.uuid4())


def _customer_checkout_use_case(
    *,
    open_command: OpenCommandInfo | None,
    summary: PayableSummary | None,
    fee_percent: float | None = None,
) -> tuple[CustomerCheckoutUseCase, FakeDiningServiceClient, FakeOrderServiceClient]:
    process_payment_use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore(),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )
    dining_client = FakeDiningServiceClient(open_command=open_command)
    order_client = FakeOrderServiceClient(summary=summary)
    use_case = CustomerCheckoutUseCase(
        process_payment_use_case=process_payment_use_case,
        dining_service_client=dining_client,
        order_service_client=order_client,
        restaurant_service_client=FakeRestaurantServiceClient(fee_percent=fee_percent),
    )
    return use_case, dining_client, order_client


@pytest.mark.asyncio
async def test_customer_checkout_computes_total_from_order_service_not_the_client() -> None:
    """Núcleo da correção de segurança (2026-08-10): o total cobrado vem do
    `order-service`, nunca de um `expected_total` que o cliente mandaria."""
    tenant_id, command_id, order_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    use_case, dining_client, _ = _customer_checkout_use_case(
        open_command=OpenCommandInfo(command_id=command_id, service_fee_charged=False),
        summary=PayableSummary(total_amount=50.0, reference_order_id=order_id),
    )

    response = await use_case.execute(
        tenant_id=tenant_id,
        table_number=5,
        secret="secret-valida",
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=50.0)],
        idempotency_key=None,
        card_last4=None,
        card_holder_name=None,
    )

    assert response.total_amount == 50.0
    assert response.command_id == command_id
    assert response.order_id == order_id
    assert response.cash_register_id is None
    assert dining_client.calls == [(tenant_id, 5, "secret-valida")]


@pytest.mark.asyncio
async def test_customer_checkout_applies_service_fee_from_restaurant_service() -> None:
    tenant_id, command_id, order_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    use_case, _, _ = _customer_checkout_use_case(
        open_command=OpenCommandInfo(command_id=command_id, service_fee_charged=True),
        summary=PayableSummary(total_amount=100.0, reference_order_id=order_id),
        fee_percent=10.0,
    )

    response = await use_case.execute(
        tenant_id=tenant_id,
        table_number=5,
        secret="secret-valida",
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=110.0)],
        idempotency_key=None,
        card_last4=None,
        card_holder_name=None,
    )

    assert response.total_amount == 110.0


@pytest.mark.asyncio
async def test_customer_checkout_rejects_a_split_that_does_not_match_the_real_total() -> None:
    """Um cliente tentando forjar `amount` menor que o total real (o próprio
    ataque que motivou a correção) é rejeitado — não é mais possível nem
    mandar `expected_total` (campo removido do DTO), e o `amount` do split
    precisa bater com o valor computado no servidor."""
    use_case, _, _ = _customer_checkout_use_case(
        open_command=OpenCommandInfo(command_id=uuid.uuid4(), service_fee_charged=False),
        summary=PayableSummary(total_amount=500.0, reference_order_id=uuid.uuid4()),
    )

    with pytest.raises(SplitAmountMismatchException):
        await use_case.execute(
            tenant_id=uuid.uuid4(),
            table_number=5,
            secret="secret-valida",
            splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=0.01)],
            idempotency_key=None,
            card_last4=None,
            card_holder_name=None,
        )


@pytest.mark.asyncio
async def test_customer_checkout_rejects_invalid_table_secret_without_charging() -> None:
    use_case, _, order_client = _customer_checkout_use_case(open_command=None, summary=None)

    with pytest.raises(InvalidTableSecretException):
        await use_case.execute(
            tenant_id=uuid.uuid4(),
            table_number=5,
            secret="secret-errada",
            splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=50.0)],
            idempotency_key=None,
            card_last4=None,
            card_holder_name=None,
        )
    assert order_client.calls == []  # nunca chega a consultar o total sem secret válida


@pytest.mark.asyncio
async def test_customer_checkout_raises_no_payable_orders_for_empty_command() -> None:
    use_case, _, _ = _customer_checkout_use_case(
        open_command=OpenCommandInfo(command_id=uuid.uuid4(), service_fee_charged=False),
        summary=PayableSummary(total_amount=0.0, reference_order_id=None),
    )

    with pytest.raises(NoPayableOrdersError):
        await use_case.execute(
            tenant_id=uuid.uuid4(),
            table_number=5,
            secret="secret-valida",
            splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=50.0)],
            idempotency_key=None,
            card_last4=None,
            card_holder_name=None,
        )


@pytest.mark.asyncio
async def test_customer_checkout_fails_closed_when_order_service_is_unavailable() -> None:
    use_case, _, _ = _customer_checkout_use_case(
        open_command=OpenCommandInfo(command_id=uuid.uuid4(), service_fee_charged=False),
        summary=None,
    )

    with pytest.raises(PayableAmountUnavailableException):
        await use_case.execute(
            tenant_id=uuid.uuid4(),
            table_number=5,
            secret="secret-valida",
            splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=50.0)],
            idempotency_key=None,
            card_last4=None,
            card_holder_name=None,
        )


@pytest.mark.asyncio
async def test_customer_checkout_fails_closed_when_restaurant_service_is_unavailable() -> None:
    use_case, _, _ = _customer_checkout_use_case(
        open_command=OpenCommandInfo(command_id=uuid.uuid4(), service_fee_charged=True),
        summary=PayableSummary(total_amount=50.0, reference_order_id=uuid.uuid4()),
        fee_percent=None,
    )

    with pytest.raises(PayableAmountUnavailableException):
        await use_case.execute(
            tenant_id=uuid.uuid4(),
            table_number=5,
            secret="secret-valida",
            splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=55.0)],
            idempotency_key=None,
            card_last4=None,
            card_holder_name=None,
        )


@pytest.mark.asyncio
async def test_staff_checkout_rejects_underpaid_command() -> None:
    tenant_id, command_id = uuid.uuid4(), uuid.uuid4()
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        operator_id=uuid.uuid4(),
        opening_amount=0.0,
        current_balance=0.0,
    )
    process_payment_use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )
    order_client = FakeOrderServiceClient(
        summary=PayableSummary(total_amount=500.0, reference_order_id=uuid.uuid4())
    )
    use_case = StaffCheckoutUseCase(
        process_payment_use_case=process_payment_use_case, order_service_client=order_client
    )

    with pytest.raises(UnderpaidCommandException):
        await use_case.execute(
            tenant_id=tenant_id,
            order_id=uuid.uuid4(),
            cash_register_id=register.id,
            command_id=command_id,
            expected_total=0.01,
            splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=0.01)],
            idempotency_key=None,
            card_last4=None,
            card_holder_name=None,
            signature_data=None,
        )


@pytest.mark.asyncio
async def test_staff_checkout_accepts_total_at_or_above_the_real_minimum() -> None:
    """A equipe continua livre pra cobrar mais que o piso (ex: gorjeta)."""
    tenant_id, command_id = uuid.uuid4(), uuid.uuid4()
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        operator_id=uuid.uuid4(),
        opening_amount=0.0,
        current_balance=0.0,
    )
    process_payment_use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )
    order_client = FakeOrderServiceClient(
        summary=PayableSummary(total_amount=50.0, reference_order_id=uuid.uuid4())
    )
    use_case = StaffCheckoutUseCase(
        process_payment_use_case=process_payment_use_case, order_service_client=order_client
    )

    response = await use_case.execute(
        tenant_id=tenant_id,
        order_id=uuid.uuid4(),
        cash_register_id=register.id,
        command_id=command_id,
        expected_total=60.0,  # 50 + 10 de gorjeta
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=60.0)],
        idempotency_key=None,
        card_last4=None,
        card_holder_name=None,
        signature_data=None,
    )

    assert response.total_amount == 60.0


@pytest.mark.asyncio
async def test_staff_checkout_skips_verification_without_a_command_id() -> None:
    """Sem `command_id` (pedido avulso, sem comanda) não há fonte
    server-side pra cruzar — comportamento antigo mantido de propósito."""
    tenant_id = uuid.uuid4()
    register = CashRegister(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        operator_id=uuid.uuid4(),
        opening_amount=0.0,
        current_balance=0.0,
    )
    process_payment_use_case = ProcessPaymentUseCase(
        payment_repository=FakePaymentStore(),
        cash_register_repository=FakeCashRegisterStore([register]),
        cash_movement_repository=FakeCashMovementStore(),
        idempotency_store=FakeIdempotencyStore(),
    )
    order_client = FakeOrderServiceClient(summary=None)  # nunca deveria ser chamado
    use_case = StaffCheckoutUseCase(
        process_payment_use_case=process_payment_use_case, order_service_client=order_client
    )

    response = await use_case.execute(
        tenant_id=tenant_id,
        order_id=uuid.uuid4(),
        cash_register_id=register.id,
        command_id=None,
        expected_total=10.0,
        splits=[PaymentSplitRequest(payment_method=PaymentMethod.PIX, amount=10.0)],
        idempotency_key=None,
        card_last4=None,
        card_holder_name=None,
        signature_data=None,
    )

    assert response.total_amount == 10.0
    assert order_client.calls == []
