import { apiRequest } from './client';
import type { GeneratePlansPayload, WeeklyPlan, Meal } from '../types';

type BackendMeal = string | Meal;
type BackendDay = {
  day?: string;
  date?: string;
  breakfast?: BackendMeal;
  lunch?: BackendMeal;
  dinner?: BackendMeal;
  snacks?: BackendMeal | BackendMeal[];
  totalCalories?: number;
  totalNutrition?: {
    calories?: number;
    protein?: number;
    carbs?: number;
    fat?: number;
    fiber?: number;
    sodium?: number;
  };
};

type BackendWeeklyPlan = WeeklyPlan & {
  meals?: WeeklyPlan['meals'];
  days?: BackendDay[];
};

const getDayLabel = (planStart: string, day: BackendDay, index: number) => {
  if (day?.day) return day.day;
  const explicitDate = day?.date ?? (() => {
    const base = new Date(planStart);
    if (Number.isNaN(base.getTime())) return undefined;
    base.setDate(base.getDate() + index);
    return base.toISOString();
  })();

  if (explicitDate) {
    const date = new Date(explicitDate);
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleDateString('en-US', { weekday: 'long' });
    }
  }
  return `Day ${index + 1}`;
};

const normalizePlan = (plan: BackendWeeklyPlan): WeeklyPlan => {
  if (Array.isArray(plan.meals)) {
    return plan;
  }

  const meals =
    plan.days?.map((day, index) => ({
      day: getDayLabel(plan.weekStart, day, index),
      date: day.date,
      breakfast: day.breakfast,
      lunch: day.lunch,
      dinner: day.dinner,
      snacks: day.snacks,
      totalCalories: day.totalCalories ?? day.totalNutrition?.calories,
      totalNutrition: day.totalNutrition,
    })) ?? [];

  return {
    id: plan.id,
    patientId: plan.patientId,
    patientName: plan.patientName,
    weekStart: plan.weekStart,
    meals,
  };
};

export const planApi = {
  list: async () => {
    const data = await apiRequest<BackendWeeklyPlan[]>('/plans');
    return data.map(normalizePlan);
  },
  generate: async (payload: GeneratePlansPayload) => {
    const data = await apiRequest<BackendWeeklyPlan[]>('/plans/generate', {
      method: 'POST',
      body: payload,
    });
    return data.map(normalizePlan);
  },
};


