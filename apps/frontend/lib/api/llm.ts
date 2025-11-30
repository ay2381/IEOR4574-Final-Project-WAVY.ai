import { apiRequest } from './client';
import type { LlmInsightsPayload, LlmInsightsResponse } from '../types';

export const llmApi = {
  getProcurementInsights: (payload: LlmInsightsPayload) =>
    apiRequest<LlmInsightsResponse>('/llm/procurement-insights', {
      method: 'POST',
      body: payload,
    }),
};


