import { useState, type FormEvent } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { X } from 'lucide-react';
import type { CreatePatientPayload } from '../lib/types';

interface PatientFormProps {
  onAddPatient: (patient: CreatePatientPayload) => Promise<void> | void;
}

export function PatientForm({ onAddPatient }: PatientFormProps) {
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [weight, setWeight] = useState('');
  const [height, setHeight] = useState('');
  const [calorieTarget, setCalorieTarget] = useState('');
  const [notes, setNotes] = useState('');
  const [currentRestriction, setCurrentRestriction] = useState('');
  const [dietaryRestrictions, setDietaryRestrictions] = useState<string[]>([]);
  const [currentAllergy, setCurrentAllergy] = useState('');
  const [allergies, setAllergies] = useState<string[]>([]);
  const [currentCondition, setCurrentCondition] = useState('');
  const [medicalConditions, setMedicalConditions] = useState<string[]>([]);

  const addItem = (
    value: string, 
    setter: (value: string) => void, 
    array: string[], 
    setArray: (value: string[]) => void
  ) => {
    if (value.trim()) {
      setArray([...array, value.trim()]);
      setter('');
    }
  };

  const removeItem = (index: number, array: string[], setArray: (value: string[]) => void) => {
    setArray(array.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!name || !age || !weight || !height || !calorieTarget) {
      alert('Please fill in all required fields');
      return;
    }

    await onAddPatient({
      name,
      age: parseInt(age),
      weight: parseFloat(weight),
      height: parseFloat(height),
      calorieTarget: parseInt(calorieTarget),
      dietaryRestrictions,
      allergies,
      medicalConditions,
      notes,
    });

    // Reset form
    setName('');
    setAge('');
    setWeight('');
    setHeight('');
    setCalorieTarget('');
    setNotes('');
    setDietaryRestrictions([]);
    setAllergies([]);
    setMedicalConditions([]);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">Full Name *</Label>
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="John Doe"
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="age">Age *</Label>
          <Input
            id="age"
            type="number"
            value={age}
            onChange={(e) => setAge(e.target.value)}
            placeholder="75"
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="weight">Weight (kg) *</Label>
          <Input
            id="weight"
            type="number"
            step="0.1"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            placeholder="70.5"
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="height">Height (cm) *</Label>
          <Input
            id="height"
            type="number"
            step="0.1"
            value={height}
            onChange={(e) => setHeight(e.target.value)}
            placeholder="165"
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="calorieTarget">Daily Calorie Target *</Label>
          <Input
            id="calorieTarget"
            type="number"
            value={calorieTarget}
            onChange={(e) => setCalorieTarget(e.target.value)}
            placeholder="1800"
            required
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="restriction">Dietary Restrictions</Label>
        <div className="flex gap-2">
          <Input
            id="restriction"
            value={currentRestriction}
            onChange={(e) => setCurrentRestriction(e.target.value)}
            placeholder="e.g., Low sodium, Diabetic-friendly"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addItem(currentRestriction, setCurrentRestriction, dietaryRestrictions, setDietaryRestrictions);
              }
            }}
          />
          <Button
            type="button"
            onClick={() => addItem(currentRestriction, setCurrentRestriction, dietaryRestrictions, setDietaryRestrictions)}
          >
            Add
          </Button>
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          {dietaryRestrictions.map((restriction, index) => (
            <Badge key={index} variant="secondary" className="gap-1">
              {restriction}
              <X
                className="size-3 cursor-pointer"
                onClick={() => removeItem(index, dietaryRestrictions, setDietaryRestrictions)}
              />
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="allergy">Allergies</Label>
        <div className="flex gap-2">
          <Input
            id="allergy"
            value={currentAllergy}
            onChange={(e) => setCurrentAllergy(e.target.value)}
            placeholder="e.g., Nuts, Dairy, Shellfish"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addItem(currentAllergy, setCurrentAllergy, allergies, setAllergies);
              }
            }}
          />
          <Button
            type="button"
            onClick={() => addItem(currentAllergy, setCurrentAllergy, allergies, setAllergies)}
          >
            Add
          </Button>
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          {allergies.map((allergy, index) => (
            <Badge key={index} variant="destructive" className="gap-1">
              {allergy}
              <X
                className="size-3 cursor-pointer"
                onClick={() => removeItem(index, allergies, setAllergies)}
              />
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="condition">Medical Conditions</Label>
        <div className="flex gap-2">
          <Input
            id="condition"
            value={currentCondition}
            onChange={(e) => setCurrentCondition(e.target.value)}
            placeholder="e.g., Diabetes, Hypertension, Dysphagia"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addItem(currentCondition, setCurrentCondition, medicalConditions, setMedicalConditions);
              }
            }}
          />
          <Button
            type="button"
            onClick={() => addItem(currentCondition, setCurrentCondition, medicalConditions, setMedicalConditions)}
          >
            Add
          </Button>
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          {medicalConditions.map((condition, index) => (
            <Badge key={index} variant="outline" className="gap-1">
              {condition}
              <X
                className="size-3 cursor-pointer"
                onClick={() => removeItem(index, medicalConditions, setMedicalConditions)}
              />
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">Additional Notes</Label>
        <Textarea
          id="notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Any additional dietary preferences or special instructions..."
          rows={4}
        />
      </div>

      <Button type="submit" className="w-full">Add Patient Profile</Button>
    </form>
  );
}