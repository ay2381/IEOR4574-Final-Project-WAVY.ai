export interface Patient {
  id: string;
  name: string;
  age: number;
  weight: number;
  height: number;
  dietaryRestrictions: string[];
  allergies: string[];
  medicalConditions: string[];
  calorieTarget: number;
  notes: string;
}

export type CreatePatientPayload = Omit<Patient, 'id'>;

export interface WeeklyPlan {
  id?: string;
  patientId: string;
  patientName: string;
  weekStart: string;
  meals: DailyMeals[];
}

export interface DailyMeals {
  day: string;
  breakfast: string;
  lunch: string;
  dinner: string;
  snacks: string;
}

export type PlanGenerationMode = 'rule_based' | 'llm';

export interface GeneratePlansPayload {
  patientIds: string[];
  weekStart?: string;
  strategy?: PlanGenerationMode;
}

export interface LlmInsightsPayload {
  planIds: string[];
  instructions?: string;
}

export interface LlmInsightsResponse {
  summary: string;
  procurementNotes: string[];
  generatedAt: string;
  tokenUsage?: {
    promptTokens: number;
    completionTokens: number;
  };
}

