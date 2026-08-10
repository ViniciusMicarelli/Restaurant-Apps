import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createTable,
  listTables,
  markTableCleaned,
  type CreateTableRequest,
} from '../../infrastructure/api/diningApi';

const TABLES_POLL_INTERVAL_MS = 10_000;
const TABLES_QUERY_KEY = ['tables'];

export function useTables() {
  return useQuery({
    queryKey: TABLES_QUERY_KEY,
    queryFn: listTables,
    refetchInterval: TABLES_POLL_INTERVAL_MS,
  });
}

export function useCreateTable() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateTableRequest) => createTable(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TABLES_QUERY_KEY });
    },
  });
}

export function useMarkTableCleaned() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tableId: string) => markTableCleaned(tableId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TABLES_QUERY_KEY });
    },
  });
}
