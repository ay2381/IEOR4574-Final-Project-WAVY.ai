import { apiRequest } from './client';
import type { GeneratePlansPayload, WeeklyPlan } from '../types';

export const planApi = {
  list: () => apiRequest<WeeklyPlan[]>('/plans'),
  generate: (payload: GeneratePlansPayload) =>
    apiRequest<WeeklyPlan[]>('/plans/generate', { method: 'POST', body: payload }),
};


