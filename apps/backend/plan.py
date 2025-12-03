"""
Domain models and Pydantic schemas for Weekly Plans and Meals
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, date


class NutritionInfo(BaseModel):
    """Nutrition information for a meal"""
    calories: int
    protein: float
    carbs: float
    fat: float
    fiber: Optional[float] = 0
    sodium: Optional[float] = 0


class Meal(BaseModel):
    """Individual meal model"""
    name: str
    description: str
    ingredients: List[str] = Field(default_factory=list)
    nutrition: NutritionInfo
    preparationTime: Optional[int] = 30  # minutes
    difficulty: Optional[str] = "medium"
    highlights: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    portion: float = 1.0
    recipeId: Optional[str] = None


class DailyMeals(BaseModel):
    """Meals for a single day"""
    date: str  # ISO date string
    breakfast: Meal
    lunch: Meal
    dinner: Meal
    snacks: List[Meal] = Field(default_factory=list)
    totalCalories: int
    totalNutrition: NutritionInfo


class GeneratePlanPayload(BaseModel):
    """Request payload for generating meal plans"""
    patientIds: List[str] = Field(..., min_length=1)
    weekStart: Optional[str] = None  # ISO date string
    strategy: Literal["rule_based", "llm"] = "rule_based"
    
    class Config:
        json_schema_extra = {
            "example": {
                "patientIds": ["patient-123"],
                "weekStart": "2024-01-15",
                "strategy": "llm"
            }
        }


class WeeklyPlan(BaseModel):
    """Weekly meal plan model"""
    id: str
    patientId: str
    patientName: str
    weekStart: str  # ISO date string
    days: List[DailyMeals]
    strategy: str
    generatedAt: datetime
    weeklyTotals: dict
    
    class Config:
        from_attributes = True


class ProcurementInsightsPayload(BaseModel):
    """Request payload for procurement insights"""
    planIds: List[str] = Field(..., min_length=1)
    instructions: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "planIds": ["plan-123", "plan-456"],
                "instructions": "Focus on cost optimization and bulk purchasing opportunities"
            }
        }


class TokenUsage(BaseModel):
    """LLM token usage information"""
    promptTokens: int
    completionTokens: int


class ProcurementInsightsResponse(BaseModel):
    """Response for procurement insights"""
    summary: str
    procurementNotes: List[str]
    generatedAt: str
    tokenUsage: Optional[TokenUsage] = None


class ProcurementIngredientsPayload(BaseModel):
    """Payload for aggregating procurement ingredients"""
    planIds: List[str] = Field(..., min_length=1)


class AggregatedIngredient(BaseModel):
    """Aggregated ingredient totals"""
    name: str
    quantity: float
    unit: Optional[str] = None

