"""
SQLAlchemy ORM models for database tables
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base


def generate_uuid():
    """Generate UUID for primary keys"""
    return str(uuid.uuid4())


class PatientModel(Base):
    """Patient database model"""
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False, default="other")
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    medical_conditions = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    dietary_restrictions = Column(JSON, default=list)
    calorie_target = Column(Integer, nullable=False)
    macro_targets = Column(JSON, default=dict)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    plans = relationship("WeeklyPlanModel", back_populates="patient", cascade="all, delete-orphan")


class WeeklyPlanModel(Base):
    """Weekly meal plan database model"""
    __tablename__ = "weekly_plans"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    patient_name = Column(String(200), nullable=False)
    week_start = Column(String(10), nullable=False)  # ISO date string
    days = Column(JSON, nullable=False)  # Array of DailyMeals
    strategy = Column(String(20), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    weekly_totals = Column(JSON, default=dict)
    
    # Relationship
    patient = relationship("PatientModel", back_populates="plans")


class RecipeModel(Base):
    """Recipe catalog sourced from CSV"""
    __tablename__ = "recipes"

    id = Column(String, primary_key=True, default=generate_uuid)
    external_id = Column(String(100), unique=True, nullable=False, index=True)
    meal_name = Column(String(255), nullable=False)
    meal_type = Column(String(50), nullable=True)
    calories_per_serving = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    tags = Column(JSON, default=list)
    allergens = Column(JSON, default=list)
    ingredient_text = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ingredients = relationship(
        "RecipeIngredientModel",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )


class RecipeIngredientModel(Base):
    """Structured ingredient rows parsed from ingredient_proportion"""
    __tablename__ = "recipe_ingredients"

    id = Column(String, primary_key=True, default=generate_uuid)
    recipe_id = Column(String, ForeignKey("recipes.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    raw = Column(String(255), nullable=True)

    recipe = relationship("RecipeModel", back_populates="ingredients")


class DiseaseRuleModel(Base):
    """Disease to prohibited tag mapping."""
    __tablename__ = "disease_rules"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), unique=True, nullable=False)
    prohibited_tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
