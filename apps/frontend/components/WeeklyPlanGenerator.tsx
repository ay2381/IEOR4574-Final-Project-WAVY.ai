import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Calendar, Download, Sparkles } from 'lucide-react';
import type { Patient, PlanGenerationMode, WeeklyPlan } from '../lib/types';

interface WeeklyPlanGeneratorProps {
  patients: Patient[];
  weeklyPlans: WeeklyPlan[];
  onGeneratePlans: (strategy: PlanGenerationMode) => Promise<void> | void;
  isGenerating?: boolean;
  isLoading?: boolean;
}

const GENERATION_MODES: { value: PlanGenerationMode; label: string; description: string }[] = [
  {
    value: 'rule_based',
    label: 'Rule-based',
    description: 'Use deterministic nutrition templates',
  },
  {
    value: 'llm',
    label: 'LLM-assisted',
    description: 'Call backend LLM pipeline for bespoke plans',
  },
];

export function WeeklyPlanGenerator({
  patients,
  weeklyPlans,
  onGeneratePlans,
  isGenerating,
  isLoading,
}: WeeklyPlanGeneratorProps) {
  const [strategy, setStrategy] = useState<PlanGenerationMode>('rule_based');

  const handleGenerate = () => {
    void onGeneratePlans(strategy);
  };

  const exportPlans = () => {
    const text = weeklyPlans.map(plan => {
      let output = `\n${'='.repeat(60)}\n`;
      output += `WEEKLY NUTRITION PLAN - ${plan.patientName}\n`;
      output += `Week Starting: ${plan.weekStart}\n`;
      output += `${'='.repeat(60)}\n\n`;

      plan.meals.forEach(day => {
        output += `${day.day.toUpperCase()}\n`;
        output += `${'-'.repeat(40)}\n`;
        output += `Breakfast: ${day.breakfast}\n`;
        output += `Lunch: ${day.lunch}\n`;
        output += `Dinner: ${day.dinner}\n`;
        output += `Snacks: ${day.snacks}\n\n`;
      });

      return output;
    }).join('\n');

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nutrition-plans-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatDate = (weekStart: string, dayIndex: number) => {
    const date = new Date(weekStart);
    date.setDate(date.getDate() + dayIndex);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Generate Weekly Nutrition Plans</CardTitle>
          <CardDescription>
            Create personalized weekly meal plans for all {patients.length} patient{patients.length !== 1 ? 's' : ''}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {GENERATION_MODES.map(mode => (
              <button
                key={mode.value}
                type="button"
                onClick={() => setStrategy(mode.value)}
                className={`rounded-lg border p-4 text-left transition-colors ${
                  strategy === mode.value ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-indigo-200'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-gray-900">{mode.label}</p>
                    <p className="text-sm text-gray-600">{mode.description}</p>
                  </div>
                  {strategy === mode.value && <Badge variant="secondary">Selected</Badge>}
                </div>
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2 text-sm text-gray-500">
            <Calendar className="size-4" />
            <span>
              {strategy === 'llm'
                ? 'LLM-assisted plans leverage your backend AI pipeline.'
                : 'Rule-based plans use deterministic clinical templates.'}
            </span>
          </div>

          <Button 
            onClick={handleGenerate} 
            disabled={isGenerating || patients.length === 0}
            className="w-full"
            size="lg"
          >
            <Sparkles className="size-4 mr-2" />
            {isGenerating
              ? strategy === 'llm'
                ? 'Generating AI Plans...'
                : 'Generating Plans...'
              : 'Generate Plans for All Patients'}
          </Button>

          {weeklyPlans.length > 0 && (
            <Button 
              onClick={exportPlans} 
              variant="outline"
              className="w-full"
            >
              <Download className="size-4 mr-2" />
              Export All Plans
            </Button>
          )}
        </CardContent>
      </Card>

      {isLoading && (
        <Card>
          <CardContent className="space-y-4 py-8">
            <div className="h-4 w-1/3 rounded bg-gray-200 animate-pulse" />
            <div className="h-4 w-1/2 rounded bg-gray-200 animate-pulse" />
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="rounded-lg border p-4 space-y-2">
                  <div className="h-4 w-1/2 rounded bg-gray-200 animate-pulse" />
                  <div className="h-3 w-full rounded bg-gray-100 animate-pulse" />
                  <div className="h-3 w-2/3 rounded bg-gray-100 animate-pulse" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {!isLoading && weeklyPlans.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-gray-900">Weekly Nutrition Plans</h2>
            <Badge variant="secondary" className="text-sm">
              Week of {new Date(weeklyPlans[0]?.weekStart).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </Badge>
          </div>

          {weeklyPlans.map((plan) => (
            <Card key={plan.id ?? plan.patientId} className="overflow-hidden">
              <CardHeader className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
                <CardTitle>{plan.patientName}</CardTitle>
                <CardDescription className="text-indigo-100">
                  Personalized 7-day meal plan
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {plan.meals.map((day, index) => (
                    <Card key={day.day} className="border-2 hover:border-indigo-300 transition-colors">
                      <CardHeader className="pb-3 bg-gradient-to-br from-gray-50 to-white">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">{day.day}</CardTitle>
                          <Badge variant="outline" className="bg-indigo-50 text-indigo-700 border-indigo-200">
                            {formatDate(plan.weekStart, index)}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3 pt-4">
                        <div className="space-y-1">
                          <div className="flex items-start gap-2">
                            <Badge className="shrink-0 bg-amber-500">🌅 Breakfast</Badge>
                            <p className="text-sm">{day.breakfast}</p>
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex items-start gap-2">
                            <Badge className="shrink-0 bg-orange-500">☀️ Lunch</Badge>
                            <p className="text-sm">{day.lunch}</p>
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex items-start gap-2">
                            <Badge className="shrink-0 bg-indigo-500">🌙 Dinner</Badge>
                            <p className="text-sm">{day.dinner}</p>
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex items-start gap-2">
                            <Badge className="shrink-0 bg-green-500">🍎 Snacks</Badge>
                            <p className="text-sm">{day.snacks}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}