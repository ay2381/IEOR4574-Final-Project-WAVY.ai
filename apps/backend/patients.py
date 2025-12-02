"""
Patients API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from src.domain.patient import Patient, CreatePatientPayload
from src.db.database import get_db
from src.db.models import PatientModel

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/patients", response_model=List[Patient])
async def get_patients(db: Session = Depends(get_db)):
    """Get all patients"""
    try:
        patients = db.query(PatientModel).all()
        
        # Convert to response model
        result = []
        for patient in patients:
            result.append(Patient(
                id=patient.id,
                name=patient.name,
                age=patient.age,
                gender=patient.gender,
                medicalConditions=patient.medical_conditions,
                allergies=patient.allergies,
                dietaryRestrictions=patient.dietary_restrictions,
                calorieTarget=patient.calorie_target,
                macroTargets=patient.macro_targets,
                createdAt=patient.created_at,
                updatedAt=patient.updated_at
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch patients")


@router.post("/patients", response_model=Patient, status_code=status.HTTP_201_CREATED)
async def create_patient(
    payload: CreatePatientPayload,
    db: Session = Depends(get_db)
):
    """Create a new patient"""
    try:
        # Create database model
        patient = PatientModel(
            name=payload.name,
            age=payload.age,
            gender=payload.gender,
            medical_conditions=payload.medicalConditions,
            allergies=payload.allergies,
            dietary_restrictions=[d.model_dump() for d in payload.dietaryRestrictions],
            calorie_target=payload.calorieTarget,
            macro_targets=payload.macroTargets
        )
        
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        logger.info(f"Created patient: {patient.id} - {patient.name}")
        
        # Convert to response model
        return Patient(
            id=patient.id,
            name=patient.name,
            age=patient.age,
            gender=patient.gender,
            medicalConditions=patient.medical_conditions,
            allergies=patient.allergies,
            dietaryRestrictions=patient.dietary_restrictions,
            calorieTarget=patient.calorie_target,
            macroTargets=patient.macro_targets,
            createdAt=patient.created_at,
            updatedAt=patient.updated_at
        )
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create patient")


@router.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    """Delete a patient"""
    try:
        patient = db.query(PatientModel).filter(PatientModel.id == patient_id).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        db.delete(patient)
        db.commit()
        
        logger.info(f"Deleted patient: {patient_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting patient: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete patient")


@router.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get a specific patient by ID"""
    try:
        patient = db.query(PatientModel).filter(PatientModel.id == patient_id).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return Patient(
            id=patient.id,
            name=patient.name,
            age=patient.age,
            gender=patient.gender,
            medicalConditions=patient.medical_conditions,
            allergies=patient.allergies,
            dietaryRestrictions=patient.dietary_restrictions,
            calorieTarget=patient.calorie_target,
            macroTargets=patient.macro_targets,
            createdAt=patient.created_at,
            updatedAt=patient.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch patient")
