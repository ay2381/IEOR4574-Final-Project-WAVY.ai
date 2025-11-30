import { useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { ShoppingCart, Download, Package, Sparkles } from 'lucide-react';
import type { Patient, WeeklyPlan } from '../lib/types';
import { useLlmInsightsMutation } from '../hooks/useLlmInsights';

interface ProcurementSuggestionsProps {
  patients: Patient[];
  weeklyPlans: WeeklyPlan[];
  isLoading?: boolean;
}

interface IngredientCount {
  [key: string]: number;
}

// Ingredient extraction patterns from meal descriptions
const INGREDIENT_PATTERNS = {
  proteins: ['chicken', 'turkey', 'beef', 'pork', 'fish', 'salmon', 'cod', 'tuna', 'egg'],
  grains: ['rice', 'pasta', 'bread', 'toast', 'oatmeal', 'quinoa', 'wheat', 'cereal', 'pancake'],
  vegetables: ['broccoli', 'spinach', 'vegetable', 'green beans', 'asparagus', 'carrot', 'potato', 'sweet potato', 'zucchini', 'cauliflower', 'tomato', 'celery', 'lettuce'],
  fruits: ['berries', 'banana', 'apple', 'fruit', 'avocado'],
  dairy: ['yogurt', 'cheese', 'milk', 'cottage cheese', 'mozzarella'],
  nuts: ['nuts', 'almond', 'peanut butter', 'chia seeds', 'granola'],
  condiments: ['honey', 'maple syrup', 'hummus', 'dressing', 'sauce', 'marinara'],
};

function extractIngredients(weeklyPlans: WeeklyPlan[]): { [category: string]: IngredientCount } {
  const ingredients: { [category: string]: IngredientCount } = {
    proteins: {},
    grains: {},
    vegetables: {},
    fruits: {},
    dairy: {},
    nuts: {},
    condiments: {},
  };

  weeklyPlans.forEach(plan => {
    plan.meals.forEach(day => {
      const allMeals = `${day.breakfast} ${day.lunch} ${day.dinner} ${day.snacks}`.toLowerCase();

      Object.entries(INGREDIENT_PATTERNS).forEach(([category, patterns]) => {
        patterns.forEach(pattern => {
          if (allMeals.includes(pattern)) {
            if (!ingredients[category][pattern]) {
              ingredients[category][pattern] = 0;
            }
            ingredients[category][pattern]++;
          }
        });
      });
    });
  });

  return ingredients;
}

function calculateQuantity(ingredient: string, count: number, patientCount: number): string {
  // Simplified quantity estimation
  const baseQuantities: { [key: string]: string } = {
    // Proteins (kg)
    'chicken': `${(count * 0.15).toFixed(1)} kg`,
    'turkey': `${(count * 0.15).toFixed(1)} kg`,
    'beef': `${(count * 0.15).toFixed(1)} kg`,
    'pork': `${(count * 0.15).toFixed(1)} kg`,
    'fish': `${(count * 0.15).toFixed(1)} kg`,
    'salmon': `${(count * 0.15).toFixed(1)} kg`,
    'cod': `${(count * 0.15).toFixed(1)} kg`,
    'tuna': `${Math.ceil(count / 2)} cans`,
    'egg': `${count * 2} eggs`,
    
    // Grains
    'rice': `${(count * 0.08).toFixed(1)} kg`,
    'pasta': `${(count * 0.08).toFixed(1)} kg`,
    'bread': `${Math.ceil(count / 4)} loaves`,
    'toast': `${Math.ceil(count / 4)} loaves`,
    'oatmeal': `${(count * 0.05).toFixed(1)} kg`,
    'quinoa': `${(count * 0.06).toFixed(1)} kg`,
    'wheat': `${(count * 0.05).toFixed(1)} kg`,
    'cereal': `${Math.ceil(count / 5)} boxes`,
    'pancake': `${Math.ceil(count / 3)} mixes`,
    
    // Vegetables
    'broccoli': `${(count * 0.1).toFixed(1)} kg`,
    'spinach': `${(count * 0.08).toFixed(1)} kg`,
    'vegetable': `${(count * 0.15).toFixed(1)} kg (mixed)`,
    'green beans': `${(count * 0.1).toFixed(1)} kg`,
    'asparagus': `${(count * 0.1).toFixed(1)} kg`,
    'carrot': `${(count * 0.1).toFixed(1)} kg`,
    'potato': `${(count * 0.15).toFixed(1)} kg`,
    'sweet potato': `${(count * 0.15).toFixed(1)} kg`,
    'zucchini': `${(count * 0.1).toFixed(1)} kg`,
    'cauliflower': `${(count * 0.15).toFixed(1)} kg`,
    'tomato': `${(count * 0.1).toFixed(1)} kg`,
    'celery': `${Math.ceil(count / 3)} bunches`,
    'lettuce': `${Math.ceil(count / 2)} heads`,
    
    // Fruits
    'berries': `${(count * 0.15).toFixed(1)} kg`,
    'banana': `${count} bananas`,
    'apple': `${count} apples`,
    'fruit': `${(count * 0.2).toFixed(1)} kg (mixed)`,
    'avocado': `${count} avocados`,
    
    // Dairy
    'yogurt': `${Math.ceil(count / 2)} containers`,
    'cheese': `${(count * 0.05).toFixed(1)} kg`,
    'milk': `${Math.ceil(count / 4)} L`,
    'cottage cheese': `${Math.ceil(count / 3)} containers`,
    'mozzarella': `${(count * 0.05).toFixed(1)} kg`,
    
    // Nuts & Seeds
    'nuts': `${(count * 0.03).toFixed(1)} kg`,
    'almond': `${(count * 0.03).toFixed(1)} kg`,
    'peanut butter': `${Math.ceil(count / 5)} jars`,
    'chia seeds': `${(count * 0.02).toFixed(1)} kg`,
    'granola': `${Math.ceil(count / 4)} bags`,
    
    // Condiments
    'honey': `${Math.ceil(count / 8)} bottles`,
    'maple syrup': `${Math.ceil(count / 6)} bottles`,
    'hummus': `${Math.ceil(count / 3)} containers`,
    'dressing': `${Math.ceil(count / 4)} bottles`,
    'sauce': `${Math.ceil(count / 3)} bottles/jars`,
    'marinara': `${Math.ceil(count / 3)} jars`,
  };

  return baseQuantities[ingredient] || `${count} servings`;
}

export function ProcurementSuggestions({ patients, weeklyPlans, isLoading }: ProcurementSuggestionsProps) {
  const [instructions, setInstructions] = useState('');
  const llmInsights = useLlmInsightsMutation();
  const hasPlans = weeklyPlans.length > 0;

  if (isLoading) {
    return (
      <Card>
        <CardContent className="space-y-4 py-8">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-gray-200 animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-1/2 rounded bg-gray-200 animate-pulse" />
              <div className="h-3 w-1/3 rounded bg-gray-100 animate-pulse" />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="rounded-xl border p-4 space-y-2">
                <div className="h-4 w-1/2 rounded bg-gray-200 animate-pulse" />
                <div className="h-3 w-full rounded bg-gray-100 animate-pulse" />
                <div className="h-3 w-2/3 rounded bg-gray-100 animate-pulse" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!hasPlans) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16">
          <ShoppingCart className="size-16 text-gray-300 mb-4" />
          <p className="text-gray-500">No weekly plans generated yet</p>
          <p className="text-gray-400 text-sm">Generate nutrition plans first to see procurement suggestions</p>
        </CardContent>
      </Card>
    );
  }

  const ingredients = useMemo(() => extractIngredients(weeklyPlans), [weeklyPlans]);
  const totalItems = Object.values(ingredients).reduce(
    (sum, category) => sum + Object.keys(category).length,
    0
  );
  const planIds = weeklyPlans.map(plan => plan.id ?? plan.patientId);

  const exportProcurement = () => {
    let text = `PROCUREMENT SUGGESTIONS\n`;
    text += `Week Starting: ${weeklyPlans[0]?.weekStart}\n`;
    text += `Number of Patients: ${patients.length}\n`;
    text += `${'='.repeat(60)}\n\n`;

    Object.entries(ingredients).forEach(([category, items]) => {
      if (Object.keys(items).length > 0) {
        text += `\n${category.toUpperCase()}\n`;
        text += `${'-'.repeat(40)}\n`;
        Object.entries(items)
          .sort(([, a], [, b]) => b - a)
          .forEach(([ingredient, count]) => {
            text += `• ${ingredient.charAt(0).toUpperCase() + ingredient.slice(1)}: ${calculateQuantity(ingredient, count, patients.length)}\n`;
          });
      }
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
  };

  const categoryColors: { [key: string]: string } = {
    proteins: 'bg-red-50 border-red-200',
    grains: 'bg-amber-50 border-amber-200',
    vegetables: 'bg-green-50 border-green-200',
    fruits: 'bg-pink-50 border-pink-200',
    dairy: 'bg-blue-50 border-blue-200',
    nuts: 'bg-orange-50 border-orange-200',
    condiments: 'bg-purple-50 border-purple-200',
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
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle>Procurement Suggestions</CardTitle>
              <CardDescription>
                Shopping list based on {weeklyPlans.length} patient meal plan{weeklyPlans.length !== 1 ? 's' : ''} for the week
              </CardDescription>
            </div>
            <Badge variant="secondary" className="text-sm">
              {totalItems} ingredients
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4 mb-6">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Package className="size-5 text-gray-500" />
                <span className="text-sm text-gray-600">
                  Week of {new Date(weeklyPlans[0]?.weekStart).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                </span>
              </div>
              <Button onClick={exportProcurement} variant="outline" size="sm">
                <Download className="size-4 mr-2" />
                Export List
              </Button>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Optional instructions for AI (processed by your backend before calling the LLM)
              </label>
              <Textarea
                rows={3}
                value={instructions}
                onChange={(event) => setInstructions(event.target.value)}
                placeholder="e.g., Highlight diabetic substitutions, flag supply risks, or optimize for cost."
              />
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-xs text-gray-500">
                  AI insights use `/llm/procurement-insights` with the selected plans as context.
                </p>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={handleAskAi}
                  disabled={llmInsights.isPending}
                >
                  <Sparkles className="size-4 mr-2" />
                  {llmInsights.isPending ? 'Contacting AI...' : 'Ask AI for Insights'}
                </Button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(ingredients).map(([category, items]) => {
              const itemCount = Object.keys(items).length;
              if (itemCount === 0) return null;

              return (
                <Card key={category} className={`border-2 ${categoryColors[category]}`}>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <span className="text-2xl">{categoryIcons[category]}</span>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                      <Badge variant="secondary" className="ml-auto">
                        {itemCount}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {Object.entries(items)
                        .sort(([, a], [, b]) => b - a)
                        .map(([ingredient, count]) => (
                          <li key={ingredient} className="flex items-start justify-between text-sm">
                            <span className="capitalize">{ingredient}</span>
                            <Badge variant="outline" className="ml-2 shrink-0 text-xs">
                              {calculateQuantity(ingredient, count, patients.length)}
                            </Badge>
                          </li>
                        ))}
                    </ul>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200">
        <CardHeader>
          <CardTitle className="text-indigo-900">Procurement Tips</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-gray-700">
          <p>• Quantities are estimated based on standard serving sizes for {patients.length} patient{patients.length !== 1 ? 's' : ''} over 7 days</p>
          <p>• Consider patient-specific dietary restrictions when purchasing</p>
          <p>• Buy fresh produce multiple times per week for optimal freshness</p>
          <p>• Stock pantry items (grains, condiments) in larger quantities for convenience</p>
          <p>• Verify allergen information on all packaged foods</p>
        </CardContent>
      </Card>

      {llmInsights.data && (
        <Card className="border-indigo-200 bg-indigo-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-indigo-900">
              <Sparkles className="size-4" />
              AI Procurement Insights
            </CardTitle>
            <CardDescription>
              Generated {new Date(llmInsights.data.generatedAt).toLocaleString()}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-gray-800">
            <p>{llmInsights.data.summary}</p>
            <ul className="list-disc space-y-1 pl-5">
              {(llmInsights.data.procurementNotes ?? []).map((note, index) => (
                <li key={`${note}-${index}`}>{note}</li>
              ))}
            </ul>
            {llmInsights.data.tokenUsage && (
              <p className="text-xs text-gray-600">
                Tokens — Prompt: {llmInsights.data.tokenUsage.promptTokens}, Completion: {llmInsights.data.tokenUsage.completionTokens}
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
