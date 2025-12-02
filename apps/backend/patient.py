"""
Domain models and Pydantic schemas for Patients
"""
from pydantic import BaseModel, Field
from typing import List, Optional
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
    gender: str = Field(..., pattern="^(male|female|other)$")
    medicalConditions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    dietaryRestrictions: List[DietaryRestriction] = Field(default_factory=list)
    calorieTarget: int = Field(..., ge=500, le=5000)
    macroTargets: dict = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "age": 45,
                "gender": "male",
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
                }
            }
        }


class Patient(BaseModel):
    """Patient model with all fields"""
    id: str
    name: str
    age: int
    gender: str
    medicalConditions: List[str]
    allergies: List[str]
    dietaryRestrictions: List[DietaryRestriction]
    calorieTarget: int
    macroTargets: dict
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True
