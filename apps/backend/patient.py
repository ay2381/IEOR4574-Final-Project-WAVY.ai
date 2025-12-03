"""
Domain models and Pydantic schemas for Patients
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Any
from datetime import datetime


# Pydantic models for API
class DietaryRestriction(BaseModel):
    """Dietary restriction model"""
    type: str
    severity: Optional[str] = None


class CreatePatientPayload(BaseModel):
    """Request payload for creating a patient"""
    name: str = Field(..., min_length=1, max_length=200)
    age: int = Field(..., ge=0, le=150)
    gender: str = "other"
    weight: Optional[float] = None
    height: Optional[float] = None
    medicalConditions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    dietaryRestrictions: List[Any] = Field(default_factory=list)
    calorieTarget: int = Field(..., ge=500, le=5000)
    macroTargets: Optional[dict] = None
    notes: Optional[str] = ""
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "age": 45,
                "gender": "male",
                "weight": 70.5,
                "height": 170.0,
                "medicalConditions": ["diabetes", "hypertension"],
                "allergies": ["peanuts", "shellfish"],
                "dietaryRestrictions": [
                    {"type": "low-sodium", "severity": "moderate"}
                ],
                "calorieTarget": 2000,
                "macroTargets": {
                    "protein": 150,
                    "carbs": 200,
                    "fat": 65
                },
                "notes": "Prefers Mediterranean meals"
            }
        }

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, value: Optional[str]) -> str:
        if not value:
            return "other"
        normalized = value.lower()
        return normalized if normalized in {"male", "female", "other"} else "other"

    @field_validator("dietaryRestrictions", mode="after")
    @classmethod
    def normalize_restrictions(
        cls, value: List[Any]
    ) -> List[DietaryRestriction]:
        normalized: List[DietaryRestriction] = []
        for item in value:
            if isinstance(item, DietaryRestriction):
                normalized.append(item)
            elif isinstance(item, str):
                normalized.append(DietaryRestriction(type=item.strip(), severity=None))
            elif isinstance(item, dict):
                normalized.append(DietaryRestriction(**item))
        return normalized

    @model_validator(mode="after")
    def ensure_macro_targets(self):
        if not self.macroTargets:
            # Simple macro heuristic: 30% protein, 40% carbs, 30% fat
            protein = round(self.calorieTarget * 0.30 / 4)
            carbs = round(self.calorieTarget * 0.40 / 4)
            fat = round(self.calorieTarget * 0.30 / 9)
            self.macroTargets = {
                "protein": protein,
                "carbs": carbs,
                "fat": fat
            }
        return self


class Patient(BaseModel):
    """Patient model with all fields"""
    id: str
    name: str
    age: int
    gender: str
    weight: Optional[float] = None
    height: Optional[float] = None
    medicalConditions: List[str]
    allergies: List[str]
    dietaryRestrictions: List[str]
    calorieTarget: int
    macroTargets: dict
    notes: Optional[str] = ""
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True
