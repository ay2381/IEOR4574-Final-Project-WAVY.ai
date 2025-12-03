import { useEffect, useMemo, useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Download, Loader2, Sparkles } from 'lucide-react';
import type { Patient, PlanGenerationMode, WeeklyPlan } from '../lib/types';

const MEAL_META = [
  { key: 'breakfast', label: 'Breakfast', emoji: '🌅' },
  { key: 'lunch', label: 'Lunch', emoji: '☀️' },
  { key: 'dinner', label: 'Dinner', emoji: '🌙' },
] as const;

const normalizeNutrition = (day: WeeklyPlan['meals'][number]) => {
  if (!day.totalNutrition) {
    return {
      calories: undefined,
      protein: undefined,
      carbs: undefined,
      fat: undefined,
    };
  }

  return {
    calories: day.totalCalories ?? day.totalNutrition.calories,
    protein: day.totalNutrition.protein,
    carbs: day.totalNutrition.carbs,
    fat: day.totalNutrition.fat,
  };
};

const tagStyles: Record<string, string> = {
  texture: 'bg-[#F4E7D3] text-[#5F5238]',
  nutrient: 'bg-[#E1F2E3] text-[#37724F]',
  default: 'bg-[#E9E6E1] text-[#4A4A4A]',
};

const classifyTag = (tag: string) => {
  const textureKeywords = ['crisp', 'soft_texture', 'easy_to_chew', 'pureed'];
  const nutrientKeywords = ['protein', 'carb', 'fiber', 'sodium', 'potassium', 'fat'];
  if (textureKeywords.some(keyword => tag.includes(keyword))) return 'texture';
  if (nutrientKeywords.some(keyword => tag.includes(keyword))) return 'nutrient';
  return 'default';
};

type MealDetails = { title: string; highlights: string[] };

const getMealDetails = (meal?: unknown): MealDetails => {
  if (!meal) {
    return { title: 'Not specified', highlights: [] };
  }

  if (typeof meal === 'string') {
    const [title, ...rest] = meal.split(' — ');
    const highlightString = rest.join(' — ').trim();
    const highlightArray = highlightString
      ? highlightString.split(',').map(tag => tag.trim()).filter(Boolean)
      : [];
    return {
      title: title?.trim() || 'Chef-crafted meal',
      highlights: highlightArray,
    };
  }

  if (typeof meal === 'object') {
    const maybeMeal = meal as {
      name?: string;
      description?: string;
      tags?: string[];
      ingredients?: string[];
      highlights?: string[] | string;
    };
    const title = maybeMeal.name || maybeMeal.description || maybeMeal.ingredients?.[0] || 'Chef-crafted meal';
    const highlightSource: string[] = [];
    if (Array.isArray(maybeMeal.highlights) && maybeMeal.highlights.length > 0) {
      highlightSource.push(...maybeMeal.highlights);
    } else if (typeof maybeMeal.highlights === 'string' && maybeMeal.highlights.length > 0) {
      highlightSource.push(maybeMeal.highlights);
    } else if (maybeMeal.tags && maybeMeal.tags.length > 0) {
      highlightSource.push(...maybeMeal.tags);
    } else if (maybeMeal.description) {
      highlightSource.push(maybeMeal.description);
    }
    return { title, highlights: highlightSource };
  }

  return { title: String(meal), highlights: [] };
};

const escapeCsv = (value: string | number | undefined) => {
  const str = value === undefined || value === null ? '' : String(value);
  const escaped = str.replace(/"/g, '""');
  return `"${escaped}"`;
};

interface WeeklyPlanGeneratorProps {
  patients: Patient[];
  weeklyPlans: WeeklyPlan[];
  onGeneratePlans: (strategy: PlanGenerationMode) => Promise<void> | void;
  isGenerating?: boolean;
  isLoading?: boolean;
}

export function WeeklyPlanGenerator({
  patients,
  weeklyPlans,
  onGeneratePlans,
  isGenerating,
  isLoading,
}: WeeklyPlanGeneratorProps) {
  const strategy: PlanGenerationMode = 'llm';
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);
  const [isGeneratingState, setIsGeneratingState] = useState(false);
  const [progress, setProgress] = useState(0);
  const [loadingStage, setLoadingStage] = useState('');

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | undefined;

    if (isGenerating) {
      setIsGeneratingState(true);
      setProgress(0);
      setLoadingStage('Analyzing patient profiles and restrictions...');
      timer = setInterval(() => {
        setProgress(prev => Math.min(prev + 1.5, 95));
      }, 600);
    } else {
      setIsGeneratingState(false);
      setProgress(0);
      setLoadingStage('');
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isGenerating]);

  useEffect(() => {
    if (!isGeneratingState) return;
    if (progress < 25) {
      setLoadingStage('Analyzing patient profiles and restrictions...');
    } else if (progress < 50) {
      setLoadingStage('Retrieving nutritional data constraints...');
    } else if (progress < 75) {
      setLoadingStage('Optimizing weekly meal distribution...');
    } else if (progress < 90) {
      setLoadingStage('Finalizing ingredients list...');
    } else {
      setLoadingStage('Wrapping up personalized plans...');
    }
  }, [progress, isGeneratingState]);

  const handleGenerate = () => {
    void onGeneratePlans(strategy);
  };

  const exportPlans = () => {
    const rows: string[][] = [
      ['Patient', 'Week Start', 'Day', 'Meal Type', 'Dish', 'Highlights', 'Calories'],
    ];

    weeklyPlans.forEach(plan => {
      plan.meals.forEach((day, index) => {
        const dayRecord = day as unknown as Record<string, unknown>;
        MEAL_META.forEach(({ key, label }) => {
          const mealData = dayRecord[key];
          const { title, highlights } = getMealDetails(mealData);
          rows.push([
            plan.patientName,
            plan.weekStart,
            day.day || `Day ${index + 1}`,
            label,
            title,
            highlights.join(' | '),
            day.totalCalories ? day.totalCalories.toString() : '',
          ]);
        });
      });
    });

    const csvContent = rows.map(row => row.map(escapeCsv).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nutrition-plans-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getDateLabel = (weekStart: string, index: number, options: Intl.DateTimeFormatOptions) => {
    const date = new Date(weekStart);
    date.setDate(date.getDate() + index);
    return date.toLocaleDateString('en-US', options);
  };

  const sharedWeekStart = weeklyPlans[0]?.weekStart;
  const sharedCalendar = useMemo(() => {
    if (!sharedWeekStart) return [];
    return Array.from({ length: 7 }).map((_, index) => {
      const weekday = getDateLabel(sharedWeekStart, index, { weekday: 'long' });
      const date = getDateLabel(sharedWeekStart, index, { month: 'short', day: 'numeric' });
      const iso = new Date(sharedWeekStart);
      iso.setDate(iso.getDate() + index);
      const isoString = iso.toISOString().split('T')[0];
      return { weekday, date, iso: isoString };
    });
  }, [sharedWeekStart]);

  return (
    <section aria-label="Weekly nutrition planning" className="space-y-6">
      <Card className="rounded-3xl border border-[#E7E1D5] bg-white shadow-md shadow-emerald-50">
        <CardHeader>
          <CardTitle className="text-3xl font-serif font-bold text-gray-900 tracking-tight mb-4">
            Generate Weekly Nutrition Plans
          </CardTitle>
          <CardDescription className="text-sm text-[#5F635F]">
            Run the AI planner for every patient and export structured reports for sharing.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-stretch">
            <Button
              aria-label="Generate AI plans for all patients"
              onClick={handleGenerate}
              disabled={isGeneratingState || patients.length === 0}
              className={`group relative w-full rounded-2xl bg-[#4A7C59] text-white shadow-lg shadow-emerald-100 transition-transform duration-200 md:w-auto md:px-8 min-h-[52px] ${
                isGeneratingState ? 'cursor-not-allowed opacity-70' : 'hover:-translate-y-0.5 hover:bg-[#3f6a4c]'
              }`}
              size="lg"
            >
              <span className="pointer-events-none absolute inset-[-3px] rounded-[30px] bg-gradient-to-r from-[#f7efe4] via-[#d2f1dc] to-[#fdfbf7] opacity-0 transition-opacity duration-200 group-hover:opacity-80" aria-hidden="true" />
              <span className="relative flex items-center justify-center gap-2">
                {isGeneratingState ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Sparkles className="size-4" aria-hidden="true" />
                )}
                {isGeneratingState ? 'Generating Plans…' : 'Generate AI Plans for All Patients'}
              </span>
            </Button>

            {weeklyPlans.length > 0 && (
              <Button
                aria-label="Export all plans as CSV"
                onClick={exportPlans}
                variant="outline"
                className="w-full rounded-2xl border-[#c4d1c8] text-[#4A7C59] shadow-lg shadow-emerald-100 transition-transform duration-200 hover:-translate-y-0.5 hover:bg-[#F3F1EB] focus-visible:ring-[#c4d1c8] active:translate-y-[1px] md:w-auto whitespace-nowrap px-6 min-h-[52px]"
              >
                <Download className="size-4 mr-2" aria-hidden="true" />
                Export All Plans
              </Button>
            )}
          </div>
          {isGeneratingState && (
            <div className="mt-3 w-full max-w-2xl space-y-1">
              <div className="h-1.5 w-full rounded-full bg-gray-200 overflow-hidden">
                <div
                  className="h-full rounded-full bg-[#4A7C59] transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-sm text-gray-500">{loadingStage}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {weeklyPlans.length > 0 && sharedCalendar.length > 0 && (
        <div className="rounded-2xl bg-stone-100 p-1 shadow-inner">
          <nav aria-label="Week selector" className="flex justify-between gap-1">
            {sharedCalendar.map((entry, index) => {
              const isActive = selectedDayIndex === index;
              return (
                <button
                  key={`${entry.weekday}-${index}`}
                  type="button"
                  onClick={() => setSelectedDayIndex(index)}
                  className={`flex-1 rounded-lg px-3 py-2 text-center transition-all ${
                    isActive
                      ? 'bg-white shadow-sm text-green-800 font-semibold'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <span className="block text-sm">{entry.weekday}</span>
                  <span className="block text-xs opacity-80">{entry.date}</span>
                </button>
              );
            })}
          </nav>
        </div>
      )}

      {isLoading && (
        <section aria-live="polite">
          <Card className="rounded-3xl border border-[#E7E1D5] bg-white shadow-md shadow-emerald-50">
            <CardContent className="space-y-4 py-8">
              <div className="h-4 w-1/3 rounded bg-[#E5ECE2] animate-pulse" />
              <div className="h-4 w-1/2 rounded bg-[#E5ECE2] animate-pulse" />
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="rounded-2xl border border-[#E7E1D5] p-4 space-y-2 shadow-sm">
                    <div className="h-4 w-1/2 rounded bg-[#E5ECE2] animate-pulse" />
                    <div className="h-3 w-full rounded bg-[#F1EEE6] animate-pulse" />
                    <div className="h-3 w-2/3 rounded bg-[#F1EEE6] animate-pulse" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </section>
      )}

      {!isLoading && weeklyPlans.length > 0 && (
        <section className="space-y-6">
          {weeklyPlans.map(plan => {
            const planKey = plan.id ?? plan.patientId;
            const targetMeta = sharedCalendar[selectedDayIndex];
            const selectedDay =
              (targetMeta && plan.meals.find(day => day.date === targetMeta.iso)) ||
              plan.meals[Math.min(selectedDayIndex, plan.meals.length - 1)] ||
              plan.meals[0];
            const nutrition = selectedDay ? normalizeNutrition(selectedDay) : undefined;
            const displayedDayLabel =
              targetMeta?.weekday || selectedDay?.day || `Day ${selectedDayIndex + 1}`;

            return (
              <article key={planKey} aria-label={`${plan.patientName} weekly plan`}>
                <Card className="rounded-3xl border border-[#E7E1D5] bg-white shadow-md shadow-emerald-50">
                  <CardContent className="p-6 space-y-5">
                    <div className="flex flex-col gap-1 border-b border-[#E7E1D5] pb-4">
                      <CardTitle className="text-2xl font-serif font-semibold text-[#2F2F2F]">{plan.patientName}</CardTitle>
                      <CardDescription className="text-sm text-[#5F635F]">
                        Week of{' '}
                        {new Date(plan.weekStart).toLocaleDateString('en-US', {
                          month: 'long',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </CardDescription>
                    </div>
                    {selectedDay ? (
                      <div className="grid gap-4 lg:grid-cols-[3fr_2fr]">
                        <section
                          aria-label={`${displayedDayLabel} meals`}
                          className="rounded-2xl border border-[#E7E1D5] bg-[#FDFBF7] shadow-lg shadow-emerald-50"
                        >
                          <div className="border-b border-[#E7E1D5] px-5 py-4">
                            <p className="text-sm font-serif text-[#3F3F3F]">
                              {displayedDayLabel}
                              <span className="ml-2 font-sans text-[#6B6B6B]">
                                · Total calories:{' '}
                                {nutrition?.calories !== undefined
                                  ? Number(nutrition.calories).toLocaleString()
                                  : '—'}{' '}
                                kcal
                              </span>
                            </p>
                          </div>

                          <div className="overflow-x-auto">
                            <table className="min-w-[600px] w-full border-collapse text-sm" role="table">
                              <thead className="bg-[#EAE4D6] text-[#4A4A4A] text-left text-xs uppercase tracking-wide">
                                <tr>
                                  <th scope="col" className="px-4 py-3 font-semibold">
                                    Meal
                                  </th>
                                  <th scope="col" className="px-4 py-3 font-semibold">
                                    Dish
                                  </th>
                                  <th scope="col" className="px-4 py-3 font-semibold">
                                    Highlights
                                  </th>
                                </tr>
                              </thead>
                              <tbody>
                                {MEAL_META.map(({ key, label, emoji }) => {
                                  const mealData = (selectedDay as unknown as Record<string, unknown>)[key];
                                  const { title, highlights } = getMealDetails(mealData);
                                  const tags = highlights;
                                  return (
                                    <tr key={`${planKey}-${label}`} className="even:bg-[#F3F1EB]">
                                      <th
                                        scope="row"
                                        className="px-4 py-3 font-medium text-[#2F2F2F]"
                                      >
                                        <span className="inline-flex items-center gap-2 font-serif text-lg">
                                          <span aria-hidden="true">{emoji}</span>
                                          {label}
                                        </span>
                                      </th>
                                      <td className="px-4 py-3 text-base text-[#3F3F3F] font-sans">{title}</td>
                                      <td className="px-4 py-3 text-base text-[#6B6B6B] font-sans">
                                        <div className="flex flex-wrap gap-1.5">
                                          {tags.map(tag => {
                                            const bucket = classifyTag(tag.toLowerCase());
                                            return (
                                              <span
                                                key={`${tag}-${planKey}-${label}`}
                                                className={`rounded-full px-2 py-0.5 text-xs font-medium ${tagStyles[bucket]}`}
                                              >
                                                {tag.replace(/_/g, ' ')}
                                              </span>
                                            );
                                          })}
                                        </div>
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        </section>

                        <aside
                          aria-label="Nutrition snapshot"
                          className="rounded-2xl border border-[#d1dfd6] bg-[#F2F7F0] p-5 shadow-lg shadow-emerald-50"
                        >
                          <h4 className="text-base font-semibold text-[#3F5645]">
                            Nutrition Snapshot
                          </h4>
                          <dl className="mt-4 space-y-4 text-sm text-[#2F2F2F]">
                            {[
                              { label: 'Protein', value: nutrition?.protein, color: 'from-[#82B29A] to-[#4A7C59]' },
                              { label: 'Carbs', value: nutrition?.carbs, color: 'from-[#E0C18E] to-[#C89B5A]' },
                              { label: 'Fat', value: nutrition?.fat, color: 'from-[#F2B9A0] to-[#E28A64]' },
                            ].map((macro) => (
                              <div key={macro.label}>
                                <div className="flex items-center justify-between mb-1">
                                  <dt className="font-medium">{macro.label}</dt>
                                  <dd>
                                    {macro.value !== undefined ? `${Number(macro.value).toFixed(1)} g` : '—'}
                                  </dd>
                                </div>
                                <div className="h-2 rounded-full bg-white/60 shadow-inner">
                                  <div
                                    className={`h-full rounded-full bg-gradient-to-r ${macro.color} transition-all duration-300`}
                                    style={{ width: macro.value ? `${Math.min((Number(macro.value) / 150) * 100, 100)}%` : '8%' }}
                                  />
                                </div>
                              </div>
                            ))}
                          </dl>
                        </aside>
                      </div>
                    ) : (
                      <p className="text-sm text-[#6B6B6B]">No meals found for this plan.</p>
                    )}
                  </CardContent>
                </Card>
              </article>
            );
          })}
        </section>
      )}
    </section>
  );
}