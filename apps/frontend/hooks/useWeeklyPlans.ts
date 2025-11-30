import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { planApi } from '../lib/api/plans';
import type { GeneratePlansPayload } from '../lib/types';

export function useWeeklyPlansQuery() {
  return useQuery({
    queryKey: ['weeklyPlans'],
    queryFn: planApi.list,
  });
}

export function useGeneratePlansMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: GeneratePlansPayload) => planApi.generate(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weeklyPlans'] });
    },
  });
}


