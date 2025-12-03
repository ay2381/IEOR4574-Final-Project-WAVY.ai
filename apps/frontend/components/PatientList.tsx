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
      <Card className="rounded-2xl shadow-lg shadow-emerald-50 border border-[#E3DED3] bg-white">
        <CardContent className="flex flex-col gap-2 py-10">
          <div className="h-4 bg-slate-200 rounded animate-pulse w-1/3" />
          <div className="h-4 bg-slate-200 rounded animate-pulse w-2/3" />
          <div className="h-4 bg-slate-200 rounded animate-pulse w-full" />
        </CardContent>
      </Card>
    );
  }

  if (patients.length === 0) {
    return (
      <Card className="rounded-2xl shadow-lg shadow-emerald-50 border border-[#E3DED3] bg-white">
        <CardContent className="flex flex-col items-center justify-center py-16">
          <User className="size-16 text-[#C2CBC0] mb-4" />
          <p className="text-[#5B645C]">No patients added yet</p>
          <p className="text-[#8B9289] text-sm">Add a patient profile to get started</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {patients.map((patient) => (
          <Card
            key={patient.id}
            className="rounded-2xl border border-[#E7E1D5] bg-white shadow-lg shadow-emerald-50 transition-transform duration-200 hover:-translate-y-1 hover:shadow-2xl"
          >
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="font-serif text-2xl text-[#2F2F2F]">{patient.name}</CardTitle>
                  <CardDescription className="text-[#6D6D6D]">
                    <span className="text-sm text-[#7B7F78]">Age</span>{' '}
                    <span className="text-base font-medium text-[#2F2F2F]">{patient.age}</span>
                    <span className="mx-2 text-[#CBC4B6]">|</span>
                    <span className="text-sm text-[#7B7F78]">BMI</span>{' '}
                    <span className="text-base font-medium text-[#2F2F2F]">
                      {(patient.weight / Math.pow(patient.height / 100, 2)).toFixed(1)}
                    </span>
                  </CardDescription>
                </div>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-red-500 hover:text-red-700 hover:bg-red-50 rounded-full transition-transform duration-200 hover:-translate-y-0.5"
                    >
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
            <CardContent className="space-y-4">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-3">
                  <div className="flex flex-col">
                    <span className="text-xs uppercase tracking-wider text-gray-500">Weight</span>
                    <span className="text-base font-semibold text-gray-900">{patient.weight} kg</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs uppercase tracking-wider text-gray-500">Height</span>
                    <span className="text-base font-semibold text-gray-900">{patient.height} cm</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs uppercase tracking-wider text-gray-500">Calorie Target</span>
                    <span className="text-base font-semibold text-gray-900">{patient.calorieTarget} kcal/day</span>
                  </div>
                </div>

                <div className="space-y-3">
                  {patient.dietaryRestrictions.length > 0 && (
                    <div>
                      <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">Dietary Restrictions</p>
                      <div className="flex flex-wrap gap-1.5">
                        {patient.dietaryRestrictions.map((restriction, index) => (
                          <Badge key={index} variant="secondary" className="text-xs rounded-full bg-[#E5ECE2] text-[#4A7C59]">
                            {restriction.replace(/_/g, ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {patient.allergies.length > 0 && (
                    <div>
                      <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">Allergies</p>
                      <div className="flex flex-wrap gap-1.5">
                        {patient.allergies.map((allergy, index) => (
                          <Badge
                            key={index}
                            variant="secondary"
                            className="text-xs rounded-full bg-red-50 text-red-700 border border-red-100"
                          >
                            {allergy}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {patient.medicalConditions.length > 0 && (
                    <div>
                      <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">Medical Conditions</p>
                      <div className="flex flex-wrap gap-1.5">
                        {patient.medicalConditions.map((condition, index) => (
                          <Badge key={index} variant="outline" className="text-xs rounded-full border-[#d5cec0] text-[#4A4A4A]">
                            {condition}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {patient.notes && (
                <div>
                  <p className="text-sm text-[#6F7870] mb-1">Notes</p>
                  <p className="text-sm text-[#3F3F3F]">{patient.notes}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
