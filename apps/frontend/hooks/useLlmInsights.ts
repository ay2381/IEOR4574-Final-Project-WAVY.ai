import { useMutation } from '@tanstack/react-query';
import { llmApi } from '../lib/api/llm';
import type { LlmInsightsPayload } from '../lib/types';

export function useLlmInsightsMutation() {
  return useMutation({
    mutationFn: (payload: LlmInsightsPayload) => llmApi.getProcurementInsights(payload),
  });
}


