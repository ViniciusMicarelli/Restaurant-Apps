import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getMyOpenCashRegister,
  listPayments,
  openCashRegister,
  processPayment,
  type OpenCashRegisterRequest,
  type PaymentStatus,
  type ProcessPaymentRequest,
} from '../../infrastructure/api/paymentApi';

export function useMyOpenCashRegister() {
  return useQuery({
    queryKey: ['cash-register', 'mine'],
    queryFn: getMyOpenCashRegister,
  });
}

export function useOpenCashRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: OpenCashRegisterRequest) => openCashRegister(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cash-register'] });
    },
  });
}

export function useProcessPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      payload,
      idempotencyKey,
    }: {
      payload: ProcessPaymentRequest;
      idempotencyKey: string;
    }) => processPayment(payload, idempotencyKey),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['payments'] });
      void queryClient.invalidateQueries({ queryKey: ['cash-register'] });
    },
  });
}

export function usePayments(status?: PaymentStatus) {
  return useQuery({
    queryKey: ['payments', status ?? 'all'],
    queryFn: () => listPayments(status),
  });
}
