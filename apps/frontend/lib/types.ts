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

export interface Meal {
  name?: string;
  description?: string;
  highlights?: string[] | string;
  tags?: string[];
  ingredients?: string[];
  nutrition?: {
    calories?: number;
    protein?: number;
    carbs?: number;
    fat?: number;
    fiber?: number;
    sodium?: number;
  };
  difficulty?: string;
  preparationTime?: number;
  portion?: number;
  recipeId?: string;
  [key: string]: unknown;
}

export interface WeeklyPlan {
  id?: string;
  patientId: string;
  patientName: string;
  weekStart: string;
  meals: DailyMeals[];
}

export interface DailyMeals {
  day: string;
  date?: string;
  breakfast?: Meal | string;
  lunch?: Meal | string;
  dinner?: Meal | string;
  snacks?: Meal | string | Array<Meal | string>;
  totalCalories?: number;
  totalNutrition?: {
    calories?: number;
    protein?: number;
    carbs?: number;
    fat?: number;
    fiber?: number;
    sodium?: number;
  };
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

export interface ProcurementIngredientsPayload {
  planIds: string[];
}

export interface AggregatedIngredient {
  name: string;
  quantity: number;
  unit?: string | null;
}

