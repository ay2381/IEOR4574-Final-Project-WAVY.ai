"""
SQLAlchemy ORM models for database tables
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.db.database import Base


def generate_uuid():
    """Generate UUID for primary keys"""
    return str(uuid.uuid4())


class PatientModel(Base):
    """Patient database model"""
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    medical_conditions = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    dietary_restrictions = Column(JSON, default=list)
    calorie_target = Column(Integer, nullable=False)
    macro_targets = Column(JSON, default=dict)
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
