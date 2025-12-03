"""
Meal Plans API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import logging

from plan import WeeklyPlan, GeneratePlanPayload
from database import get_db
from models import PatientModel, WeeklyPlanModel
from plan_service import PlanGenerationService

logger = logging.getLogger(__name__)
router = APIRouter()
plan_service = PlanGenerationService()


@router.get("/plans", response_model=List[WeeklyPlan])
async def get_plans(db: Session = Depends(get_db)):
    """Get all meal plans"""
    try:
        plans = db.query(WeeklyPlanModel).all()
        
        result = []
        for plan in plans:
            result.append(WeeklyPlan(
                id=plan.id,
                patientId=plan.patient_id,
                patientName=plan.patient_name,
                weekStart=plan.week_start,
                days=plan.days,
                strategy=plan.strategy,
                generatedAt=plan.generated_at,
                weeklyTotals=plan.weekly_totals
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error fetching plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch plans")


@router.post("/plans/generate", response_model=List[WeeklyPlan], status_code=status.HTTP_201_CREATED)
async def generate_plans(
    payload: GeneratePlanPayload,
    db: Session = Depends(get_db)
):
    """Generate meal plans for specified patients"""
    try:
        # Validate patients exist
        patients = db.query(PatientModel).filter(
            PatientModel.id.in_(payload.patientIds)
        ).all()
        
        if len(patients) != len(payload.patientIds):
            raise HTTPException(
                status_code=404,
                detail="One or more patients not found"
            )
        
        # Set default week start if not provided
        week_start = payload.weekStart
        if not week_start:
            # Use next Monday as default
            today = datetime.now()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            next_monday = today + timedelta(days=days_until_monday)
            week_start = next_monday.strftime("%Y-%m-%d")
        
        generated_plans = []
        
        # Remove existing plans for targeted patients to avoid duplicates
        db.query(WeeklyPlanModel).filter(
            WeeklyPlanModel.patient_id.in_(payload.patientIds)
        ).delete(synchronize_session=False)
        db.commit()
        
        # Generate plan for each patient
        for patient in patients:
            logger.info(f"Generating plan for patient {patient.id} using {payload.strategy} strategy")
            
            # Prepare patient data
            patient_data = {
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "medicalConditions": patient.medical_conditions,
                "allergies": patient.allergies,
                "dietaryRestrictions": patient.dietary_restrictions,
                "calorieTarget": patient.calorie_target,
                "macroTargets": patient.macro_targets
            }
            
            # Generate plan based on strategy
            if payload.strategy == "llm":
                plan_data = plan_service.generate_plan_llm(patient, week_start, db)
            else:
                plan_data = plan_service.generate_plan_rule_based(patient_data, week_start)
            
            # Create database record
            plan = WeeklyPlanModel(
                patient_id=patient.id,
                patient_name=patient.name,
                week_start=week_start,
                days=plan_data["days"],
                strategy=payload.strategy,
                weekly_totals=plan_data["weeklyTotals"]
            )
            
            db.add(plan)
            db.commit()
            db.refresh(plan)
            
            logger.info(f"Created plan {plan.id} for patient {patient.id}")
            
            # Convert to response model
            generated_plans.append(WeeklyPlan(
                id=plan.id,
                patientId=plan.patient_id,
                patientName=plan.patient_name,
                weekStart=plan.week_start,
                days=plan.days,
                strategy=plan.strategy,
                generatedAt=plan.generated_at,
                weeklyTotals=plan.weekly_totals
            ))
        
        return generated_plans
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating plans: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate plans: {str(e)}")


@router.get("/plans/{plan_id}", response_model=WeeklyPlan)
async def get_plan(plan_id: str, db: Session = Depends(get_db)):
    """Get a specific meal plan by ID"""
    try:
        plan = db.query(WeeklyPlanModel).filter(WeeklyPlanModel.id == plan_id).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return WeeklyPlan(
            id=plan.id,
            patientId=plan.patient_id,
            patientName=plan.patient_name,
            weekStart=plan.week_start,
            days=plan.days,
            strategy=plan.strategy,
            generatedAt=plan.generated_at,
            weeklyTotals=plan.weekly_totals
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch plan")


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: str, db: Session = Depends(get_db)):
    """Delete a meal plan"""
    try:
        plan = db.query(WeeklyPlanModel).filter(WeeklyPlanModel.id == plan_id).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        db.delete(plan)
        db.commit()
        
        logger.info(f"Deleted plan: {plan_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plan: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete plan")
