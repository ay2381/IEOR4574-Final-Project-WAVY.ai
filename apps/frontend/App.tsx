import { useState } from 'react';
import { PatientForm } from './components/PatientForm';
import { PatientList } from './components/PatientList';
import { WeeklyPlanGenerator } from './components/WeeklyPlanGenerator';
import { ProcurementSuggestions } from './components/ProcurementSuggestions';
import { Button } from './components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Users, ShoppingCart, UserPlus } from 'lucide-react';
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-indigo-900 mb-2">Convalescent Home Nutrition Planner</h1>
            <p className="text-gray-600">Manage patient profiles and generate procurement suggestions</p>
          </div>
          
          <Dialog open={isAddPatientOpen} onOpenChange={setIsAddPatientOpen}>
            <DialogTrigger asChild>
              <Button className="flex items-center gap-2">
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
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="profiles" className="flex items-center gap-2">
              <Users className="size-4" />
              Patient Profiles
            </TabsTrigger>
            <TabsTrigger value="procurement" className="flex items-center gap-2">
              <ShoppingCart className="size-4" />
              Procurement Suggestions
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profiles">
            <div className="space-y-6">
              <PatientList 
                patients={patients} 
                onRemovePatient={removePatient} 
                isLoading={isLoadingPatients}
              />
              
              {patients.length > 0 && (
                <WeeklyPlanGenerator 
                  patients={patients} 
                  weeklyPlans={weeklyPlans}
                  onGeneratePlans={handleGeneratePlans}
                  isGenerating={generatePlans.isPending}
                  isLoading={isLoadingPlans}
                />
              )}
            </div>
          </TabsContent>

          <TabsContent value="procurement">
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