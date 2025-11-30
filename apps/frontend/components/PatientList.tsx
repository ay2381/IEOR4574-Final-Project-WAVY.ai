import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Trash2, User } from 'lucide-react';
import type { Patient } from '../lib/types';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from './ui/alert-dialog';

interface PatientListProps {
  patients: Patient[];
  onRemovePatient: (id: string) => Promise<void> | void;
  isLoading?: boolean;
}

export function PatientList({ patients, onRemovePatient, isLoading }: PatientListProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex flex-col gap-2 py-10">
          <div className="h-4 bg-gray-200 rounded animate-pulse w-1/3" />
          <div className="h-4 bg-gray-200 rounded animate-pulse w-2/3" />
          <div className="h-4 bg-gray-200 rounded animate-pulse w-full" />
        </CardContent>
      </Card>
    );
  }

  if (patients.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16">
          <User className="size-16 text-gray-300 mb-4" />
          <p className="text-gray-500">No patients added yet</p>
          <p className="text-gray-400 text-sm">Add a patient profile to get started</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-gray-900">Patient Profiles</h2>
          <p className="text-gray-500 text-sm">{patients.length} patient{patients.length !== 1 ? 's' : ''} registered</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {patients.map((patient) => (
          <Card key={patient.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>{patient.name}</CardTitle>
                  <CardDescription>
                    Age: {patient.age} | BMI: {(patient.weight / Math.pow(patient.height / 100, 2)).toFixed(1)}
                  </CardDescription>
                </div>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="ghost" size="icon" className="text-red-500 hover:text-red-700 hover:bg-red-50">
                      <Trash2 className="size-4" />
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Remove Patient Profile</AlertDialogTitle>
                      <AlertDialogDescription>
                        Are you sure you want to remove {patient.name}'s profile? This action cannot be undone and will also delete their nutrition plans.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction onClick={() => { void onRemovePatient(patient.id); }} className="bg-red-500 hover:bg-red-600">
                        Remove
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Weight:</span> {patient.weight} kg
                </div>
                <div>
                  <span className="text-gray-500">Height:</span> {patient.height} cm
                </div>
                <div className="col-span-2">
                  <span className="text-gray-500">Calorie Target:</span> {patient.calorieTarget} kcal/day
                </div>
              </div>

              {patient.dietaryRestrictions.length > 0 && (
                <div>
                  <p className="text-sm text-gray-500 mb-1">Dietary Restrictions:</p>
                  <div className="flex flex-wrap gap-1">
                    {patient.dietaryRestrictions.map((restriction, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {restriction}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {patient.allergies.length > 0 && (
                <div>
                  <p className="text-sm text-gray-500 mb-1">Allergies:</p>
                  <div className="flex flex-wrap gap-1">
                    {patient.allergies.map((allergy, index) => (
                      <Badge key={index} variant="destructive" className="text-xs">
                        {allergy}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {patient.medicalConditions.length > 0 && (
                <div>
                  <p className="text-sm text-gray-500 mb-1">Medical Conditions:</p>
                  <div className="flex flex-wrap gap-1">
                    {patient.medicalConditions.map((condition, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {condition}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {patient.notes && (
                <div>
                  <p className="text-sm text-gray-500 mb-1">Notes:</p>
                  <p className="text-sm text-gray-700">{patient.notes}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
