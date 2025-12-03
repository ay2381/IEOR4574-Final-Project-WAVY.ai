import { useQuery } from '@tanstack/react-query';
import { procurementApi } from '../lib/api/procurement';

export function useProcurementIngredients(planIds: string[]) {
  const sortedKey = [...planIds].sort().join(',');

  return useQuery({
    queryKey: ['procurement-ingredients', sortedKey],
    queryFn: () =>
      procurementApi.getAggregatedIngredients({
        planIds,
      }),
    enabled: planIds.length > 0,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}


