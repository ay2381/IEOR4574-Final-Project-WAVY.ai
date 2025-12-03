import { useState } from 'react';
import { PatientForm } from './components/PatientForm';
import { PatientList } from './components/PatientList';
import { WeeklyPlanGenerator } from './components/WeeklyPlanGenerator';
import { ProcurementSuggestions } from './components/ProcurementSuggestions';
import { Button } from './components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Users, ShoppingCart, UserPlus, Calendar } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { useCreatePatientMutation, useDeletePatientMutation, usePatientsQuery } from './hooks/usePatients';
import { useGeneratePlansMutation, useWeeklyPlansQuery } from './hooks/useWeeklyPlans';
import type { CreatePatientPayload, PlanGenerationMode } from './lib/types';

export default function App() {
  const [isAddPatientOpen, setIsAddPatientOpen] = useState(false);
  const { data: patients = [], isLoading: isLoadingPatients } = usePatientsQuery();
  const { data: weeklyPlans = [], isLoading: isLoadingPlans } = useWeeklyPlansQuery();
  const createPatient = useCreatePatientMutation();
  const deletePatient = useDeletePatientMutation();
  const generatePlans = useGeneratePlansMutation();

  const addPatient = async (patient: CreatePatientPayload) => {
    try {
      await createPatient.mutateAsync(patient);
      setIsAddPatientOpen(false);
    } catch (error) {
      console.error(error);
      alert(error instanceof Error ? error.message : 'Unable to add patient right now.');
    }
  };

  const removePatient = async (id: string) => {
    try {
      await deletePatient.mutateAsync(id);
    } catch (error) {
      console.error(error);
      alert(error instanceof Error ? error.message : 'Unable to delete patient.');
    }
  };

  const handleGeneratePlans = async (strategy: PlanGenerationMode) => {
    if (patients.length === 0) return;
    try {
      await generatePlans.mutateAsync({
        patientIds: patients.map(p => p.id),
        strategy,
      });
    } catch (error) {
      console.error(error);
      alert(error instanceof Error ? error.message : 'Unable to generate plans.');
    }
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="font-serif text-3xl text-[#2F2F2F] mb-2">Convalescent Home Nutrition Planner</h1>
            <p className="text-[#6B6B6B]">Manage patient profiles and generate procurement suggestions</p>
          </div>
          
          <Dialog open={isAddPatientOpen} onOpenChange={setIsAddPatientOpen}>
            <DialogTrigger asChild>
              <Button className="flex items-center gap-2 rounded-2xl bg-[#4A7C59] text-white shadow-lg shadow-emerald-100 transition-transform duration-200 hover:-translate-y-0.5 hover:bg-[#3f6a4c] active:translate-y-[1px]">
                <UserPlus className="size-4" />
                Add Patient
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Add New Patient Profile</DialogTitle>
                <DialogDescription>
                  Enter patient information to create a personalized nutrition profile
                </DialogDescription>
              </DialogHeader>
              <PatientForm onAddPatient={addPatient} />
            </DialogContent>
          </Dialog>
        </div>

        <Tabs defaultValue="profiles" className="w-full">
          <TabsList className="flex w-full justify-center gap-10 mb-8 border-b border-[#d9d2c5] h-14 items-center">
            <TabsTrigger
              value="profiles"
              className="flex h-full items-center justify-center gap-2 px-6 text-base font-medium text-gray-500 transition-colors data-[state=active]:border-b-2 data-[state=active]:border-[#4A7C59] data-[state=active]:text-[#2F2F2F] data-[state=active]:font-semibold hover:text-gray-600"
            >
              <Users className="size-4" />
              Patient Profiles
            </TabsTrigger>
            <TabsTrigger
              value="plans"
              className="flex h-full items-center justify-center gap-2 px-6 text-base font-medium text-gray-500 transition-colors data-[state=active]:border-b-2 data-[state=active]:border-[#4A7C59] data-[state=active]:text-[#2F2F2F] data-[state=active]:font-semibold hover:text-gray-600"
            >
              <Calendar className="size-4" />
              Weekly Nutrition Plans
            </TabsTrigger>
            <TabsTrigger
              value="procurement"
              className="flex h-full items-center justify-center gap-2 px-6 text-base font-medium text-gray-500 transition-colors data-[state=active]:border-b-2 data-[state=active]:border-[#4A7C59] data-[state=active]:text-[#2F2F2F] data-[state=active]:font-semibold hover:text-gray-600"
            >
              <ShoppingCart className="size-4" />
              Procurement Suggestions
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profiles" className="space-y-6">
            <PatientList 
              patients={patients} 
              onRemovePatient={removePatient} 
              isLoading={isLoadingPatients}
            />
          </TabsContent>

          <TabsContent value="plans" className="space-y-6">
            {patients.length === 0 ? (
              <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-gray-500">
                Add at least one patient profile to start generating weekly nutrition plans.
              </div>
            ) : (
              <WeeklyPlanGenerator 
                patients={patients} 
                weeklyPlans={weeklyPlans}
                onGeneratePlans={handleGeneratePlans}
                isGenerating={generatePlans.isPending}
                isLoading={isLoadingPlans}
              />
            )}
          </TabsContent>

          <TabsContent value="procurement" className="space-y-6">
            <ProcurementSuggestions 
              patients={patients}
              weeklyPlans={weeklyPlans}
              isLoading={isLoadingPlans}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}