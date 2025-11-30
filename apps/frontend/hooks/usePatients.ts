import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { patientApi } from '../lib/api/patients';
import type { CreatePatientPayload } from '../lib/types';

export function usePatientsQuery() {
  return useQuery({
    queryKey: ['patients'],
    queryFn: patientApi.list,
  });
}

export function useCreatePatientMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreatePatientPayload) => patientApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    },
  });
}

export function useDeletePatientMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => patientApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      queryClient.invalidateQueries({ queryKey: ['weeklyPlans'] });
    },
  });
}


