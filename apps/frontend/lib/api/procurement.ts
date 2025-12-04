import { apiRequest } from './client';
import type {
  AggregatedIngredient,
  ProcurementIngredientsPayload,
} from '../types';

export const procurementApi = {
  getAggregatedIngredients: (payload: ProcurementIngredientsPayload) =>
    apiRequest<AggregatedIngredient[]>('/llm/procurement-ingredients', {
      method: 'POST',
      body: payload,
    }),
};


