import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  closeCommand,
  listCommands,
  setCommandServiceFee,
  type CommandStatus,
} from '../../infrastructure/api/diningApi';

const COMMANDS_POLL_INTERVAL_MS = 10_000;

export function useCommands(status?: CommandStatus) {
  return useQuery({
    queryKey: ['commands', status ?? 'all'],
    queryFn: () => listCommands(status),
    refetchInterval: COMMANDS_POLL_INTERVAL_MS,
  });
}

export function useSetCommandServiceFee() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ commandId, charged }: { commandId: string; charged: boolean }) =>
      setCommandServiceFee(commandId, charged),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['commands'] });
    },
  });
}

export function useCloseCommand() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (commandId: string) => closeCommand(commandId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['commands'] });
      void queryClient.invalidateQueries({ queryKey: ['tables'] });
    },
  });
}
