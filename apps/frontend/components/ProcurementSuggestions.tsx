import { useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { ShoppingCart, Download, Package, Sparkles } from 'lucide-react';
import type { AggregatedIngredient, Patient, WeeklyPlan } from '../lib/types';
import { useLlmInsightsMutation } from '../hooks/useLlmInsights';
import { useProcurementIngredients } from '../hooks/useProcurementIngredients';

interface ProcurementSuggestionsProps {
  patients: Patient[];
  weeklyPlans: WeeklyPlan[];
  isLoading?: boolean;
}

type IngredientCategory =
  | 'proteins'
  | 'grains'
  | 'vegetables'
  | 'fruits'
  | 'dairy'
  | 'nuts'
  | 'condiments'
  | 'others';

const CATEGORY_PATTERNS: Record<IngredientCategory, string[]> = {
  proteins: ['chicken', 'turkey', 'beef', 'pork', 'fish', 'salmon', 'cod', 'tuna', 'egg', 'tofu'],
  grains: ['rice', 'pasta', 'bread', 'toast', 'oatmeal', 'quinoa', 'wheat', 'cereal', 'pancake', 'noodle'],
  vegetables: [
    'broccoli',
    'spinach',
    'vegetable',
    'green beans',
    'asparagus',
    'carrot',
    'potato',
    'sweet potato',
    'zucchini',
    'cauliflower',
    'tomato',
    'celery',
    'lettuce',
    'pepper',
    'onion',
  ],
  fruits: ['berries', 'banana', 'apple', 'fruit', 'avocado', 'peach'],
  dairy: ['yogurt', 'cheese', 'milk', 'cottage cheese', 'mozzarella', 'butter'],
  nuts: ['nuts', 'almond', 'peanut', 'chia', 'granola'],
  condiments: ['honey', 'maple syrup', 'hummus', 'dressing', 'sauce', 'marinara', 'gravy'],
  others: [],
};

const CATEGORY_ORDER: IngredientCategory[] = [
  'proteins',
  'grains',
  'vegetables',
  'fruits',
  'dairy',
  'nuts',
  'condiments',
  'others',
];

function getIngredientCategory(name: string): IngredientCategory {
  const lower = name.toLowerCase();
  for (const category of CATEGORY_ORDER) {
    if (CATEGORY_PATTERNS[category].some(pattern => lower.includes(pattern))) {
      return category;
    }
  }
  return 'others';
}

function formatQuantity(value: number): string {
  if (!Number.isFinite(value)) {
    return '--';
  }
  return Math.abs(value - Math.round(value)) < 0.01 ? value.toFixed(0) : value.toFixed(2);
}

function formatUnit(unit?: string | null): string {
  if (!unit) return '';
  return unit;
}

function categorizeIngredients(ingredients: AggregatedIngredient[]) {
  const grouped: Record<IngredientCategory, AggregatedIngredient[]> = CATEGORY_ORDER.reduce(
    (acc, category) => {
      acc[category] = [];
      return acc;
    },
    {} as Record<IngredientCategory, AggregatedIngredient[]>,
  );

  ingredients.forEach(item => {
    const category = getIngredientCategory(item.name);
    grouped[category].push(item);
  });

  CATEGORY_ORDER.forEach(category => {
    grouped[category].sort((a, b) => b.quantity - a.quantity);
  });

  return grouped;
}

export function ProcurementSuggestions({ patients, weeklyPlans, isLoading }: ProcurementSuggestionsProps) {
  const [instructions, setInstructions] = useState('');
  const llmInsights = useLlmInsightsMutation();
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>(
    {},
  );
  const hasPlans = weeklyPlans.length > 0;
  const planIds = useMemo(
    () => weeklyPlans.map(plan => plan.id ?? plan.patientId).filter(Boolean) as string[],
    [weeklyPlans],
  );
  const ingredientQuery = useProcurementIngredients(planIds);
  const aggregatedIngredients = ingredientQuery.data ?? [];
  const categorizedIngredients = useMemo(
    () => categorizeIngredients(aggregatedIngredients),
    [aggregatedIngredients],
  );
  const totalItems = aggregatedIngredients.length;
  const showLoadingState = isLoading || (planIds.length > 0 && ingredientQuery.isLoading);

  if (showLoadingState) {
    return (
      <Card className="rounded-2xl border border-[#E7E1D5] bg-white shadow-lg shadow-emerald-50">
        <CardContent className="space-y-4 py-8">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-[#E5ECE2] animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-1/2 rounded bg-[#E5ECE2] animate-pulse" />
              <div className="h-3 w-1/3 rounded bg-[#F1EEE6] animate-pulse" />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="rounded-2xl border border-[#E7E1D5] p-4 space-y-2">
                <div className="h-4 w-1/2 rounded bg-[#E5ECE2] animate-pulse" />
                <div className="h-3 w-full rounded bg-[#F1EEE6] animate-pulse" />
                <div className="h-3 w-2/3 rounded bg-[#F1EEE6] animate-pulse" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!hasPlans) {
    return (
      <Card className="rounded-2xl border border-[#E7E1D5] bg-white shadow-lg shadow-emerald-50">
        <CardContent className="flex flex-col items-center justify-center py-16 text-center">
          <ShoppingCart className="size-16 text-[#C2CBC0] mb-4" />
          <p className="text-[#5B645C]">No weekly plans generated yet</p>
          <p className="text-[#8B9289] text-sm">Generate nutrition plans first to see procurement suggestions.</p>
        </CardContent>
      </Card>
    );
  }

  const exportProcurement = () => {
    if (!aggregatedIngredients.length) {
      return;
    }

    let text = `PROCUREMENT SUGGESTIONS\n`;
    text += `Week Starting: ${weeklyPlans[0]?.weekStart}\n`;
    text += `Number of Patients: ${patients.length}\n`;
    text += `${'='.repeat(60)}\n`;

    Object.entries(categorizedIngredients).forEach(([category, items]) => {
      if (!items.length) return;
        text += `\n${category.toUpperCase()}\n`;
        text += `${'-'.repeat(40)}\n`;
      items.forEach(item => {
        const unit = formatUnit(item.unit);
        text += `• ${item.name}: ${formatQuantity(item.quantity)}${unit ? ` ${unit}` : ''}\n`;
      });
    });

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `procurement-list-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const categoryIcons: { [key: string]: string } = {
    proteins: '🍗',
    grains: '🌾',
    vegetables: '🥬',
    fruits: '🍎',
    dairy: '🥛',
    nuts: '🥜',
    condiments: '🧂',
    others: '🧺',
  };

  const categoryColors: { [key: string]: string } = {
    proteins: 'border-l-4 border-l-red-300',
    grains: 'border-l-4 border-l-amber-300',
    vegetables: 'border-l-4 border-l-green-300',
    fruits: 'border-l-4 border-l-pink-300',
    dairy: 'border-l-4 border-l-blue-300',
    nuts: 'border-l-4 border-l-orange-300',
    condiments: 'border-l-4 border-l-purple-300',
    others: 'border-l-4 border-l-slate-200',
  };

  const handleAskAi = () => {
    if (planIds.length === 0) return;
    llmInsights.mutate({
      planIds,
      instructions: instructions.trim() || undefined,
    });
  };

  return (
    <div className="space-y-6">
      <Card className="rounded-2xl border border-[#E7E1D5] bg-white shadow-lg shadow-emerald-50">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-3xl font-serif font-bold text-gray-900 tracking-tight mb-4">
                Procurement Suggestions
              </CardTitle>
            </div>
            <Badge variant="secondary" className="rounded-full bg-[#E5ECE2] text-[#4A7C59] text-sm">
              {totalItems} ingredients
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4 mb-6">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2 text-[#5F635F]">
                <Package className="size-5 text-[#4A7C59]" />
                <span className="text-sm">
                  Week of {new Date(weeklyPlans[0]?.weekStart).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                </span>
              </div>
              <Button
                onClick={exportProcurement}
                variant="outline"
                size="sm"
                className="rounded-2xl border-[#c4d1c8] text-[#4A7C59] shadow-sm hover:bg-[#F3F1EB]"
              >
                <Download className="size-4 mr-2" />
                Export List
              </Button>
            </div>

            <div className="space-y-3">
              <label className="flex items-center gap-2 text-lg font-serif font-medium text-gray-800">
                <Sparkles className="size-4 text-[#4A7C59]" />
                Optional instructions for AI
              </label>
              <Textarea
                rows={4}
                value={instructions}
                onChange={(event) => setInstructions(event.target.value)}
                placeholder="e.g., Highlight diabetic substitutions, flag supply risks, or optimize for cost."
                className="min-h-[120px] rounded-2xl border border-[#D8D3C4] bg-gray-50 p-4 text-base text-gray-800 placeholder:text-gray-400 focus:bg-white focus:ring-2 focus:ring-green-500"
              />
              <div className="flex flex-wrap items-center justify-end gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  className="rounded-2xl bg-[#4A7C59] text-white hover:bg-[#3f6a4c]"
                  onClick={handleAskAi}
                  disabled={llmInsights.isPending}
                >
                  <Sparkles className="size-4 mr-2" />
                  {llmInsights.isPending ? 'Contacting AI...' : 'Ask AI for Insights'}
                </Button>
              </div>
            </div>
          </div>

          {llmInsights.isPending && (
            <Card className="rounded-2xl border border-[#cde0d4] bg-[#eff8f2]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-[#3F5645]">
                  <Sparkles className="size-4 animate-spin" />
                  Contacting AI...
                </CardTitle>
                <CardDescription className="text-[#5F635F]">Analyzing selected meal plans for procurement insights.</CardDescription>
              </CardHeader>
            </Card>
          )}

          {llmInsights.data && (
            <Card className="rounded-xl bg-white shadow-md border border-gray-100 border-l-4 border-gradient-left p-6" style={{ borderImage: 'linear-gradient(to bottom, #22c55e, #059669) 1' }}>
              <CardHeader className="flex items-center justify-between pb-3">
                <CardTitle className="flex items-center gap-2 font-serif text-xl font-bold text-green-800">
                  <Sparkles className="size-5 text-yellow-500" />
                  AI Procurement Insights
                </CardTitle>
                <span className="text-xs text-gray-400">
                  Generated {new Date(llmInsights.data.generatedAt).toLocaleString()}
                </span>
              </CardHeader>
              <CardContent className="space-y-4 text-[15px] leading-relaxed text-gray-700">
                <div className="prose prose-sm">
                  <p>{llmInsights.data.summary}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">Key Recommendations</h4>
                  <ul className="space-y-3">
                    {(llmInsights.data.procurementNotes ?? []).map((note, index) => (
                      <li key={`${note}-${index}`} className="flex items-start gap-2">
                        <span className="mt-1 inline-block h-2 w-2 rounded-full bg-green-500" />
                        <span>{note}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
              {llmInsights.data.tokenUsage && (
                <div className="border-t border-gray-100 pt-3 text-xs text-gray-500">
                  Tokens — Prompt: {llmInsights.data.tokenUsage.promptTokens}, Completion: {llmInsights.data.tokenUsage.completionTokens}
                </div>
              )}
            </Card>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(categorizedIngredients).map(([category, items]) => {
              const itemCount = items.length;
              if (itemCount === 0) return null;
              const isExpanded = expandedCategories[category] ?? false;
              const visibleItems = isExpanded ? items : items.slice(0, 10);

              return (
                <Card
                  key={category}
                  className={`rounded-2xl border border-gray-200 bg-white shadow-sm pl-3 ${categoryColors[category] ?? ''}`}
                >
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2 text-[#2F2F2F]">
                      <span className="text-2xl">{categoryIcons[category]}</span>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                      <Badge variant="secondary" className="ml-auto rounded-full bg-white/70 text-[#4A7C59]">
                        {itemCount}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-[#4A4A4A]">
                      {visibleItems.map(item => {
                        const unit = formatUnit(item.unit);
                        return (
                          <li key={item.name} className="flex items-center gap-3 text-sm">
                            <span className="text-[#3F3F3F]">{item.name}</span>
                            <span className="flex-1 border-b border-dotted border-[#d9d2c6]" />
                            <span className="shrink-0 rounded-full border border-[#d5cec0] bg-white px-3 py-1 text-xs font-semibold text-[#4A4A4A]">
                              {formatQuantity(item.quantity)}
                              {unit ? ` ${unit}` : ''}
                            </span>
                          </li>
                        );
                      })}
                    </ul>
                    {itemCount > 10 && (
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedCategories(prev => ({
                            ...prev,
                            [category]: !isExpanded,
                          }))
                        }
                        className="mt-3 text-xs font-medium text-[#4A7C59] underline-offset-2 hover:underline"
                      >
                        {isExpanded ? 'Hide extra items' : `Show ${itemCount - 10} more`}
                      </button>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl border border-[#E7E1D5] bg-gradient-to-br from-[#f6f3ec] to-[#eef6f1] shadow-lg shadow-emerald-50">
        <CardHeader>
          <CardTitle className="font-serif text-2xl text-[#2F2F2F]">Procurement Tips</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-[#4A4A4A]">
          <p>
            • Quantities are calculated from recipe ingredient proportions for {patients.length} patient
            {patients.length !== 1 ? 's' : ''} over 7 days
          </p>
          <p>• Consider patient-specific dietary restrictions when purchasing</p>
          <p>• Buy fresh produce multiple times per week for optimal freshness</p>
          <p>• Stock pantry items (grains, condiments) in larger quantities for convenience</p>
          <p>• Verify allergen information on all packaged foods</p>
        </CardContent>
      </Card>

    </div>
  );
}
