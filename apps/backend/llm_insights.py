"""
LLM Insights API endpoints for procurement analysis
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json
import logging

from src.domain.plan import ProcurementInsightsPayload, ProcurementInsightsResponse, TokenUsage
from src.db.database import get_db
from src.db.models import WeeklyPlanModel
from src.llm.provider import get_llm_provider
from src.llm.prompts import build_procurement_insights_prompt

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/procurement-insights", response_model=ProcurementInsightsResponse)
async def generate_procurement_insights(
    payload: ProcurementInsightsPayload,
    db: Session = Depends(get_db)
):
    """
    Generate procurement insights from meal plans using LLM.
    Analyzes ingredients across plans and provides purchasing recommendations.
    """
    try:
        # Fetch the specified plans
        plans = db.query(WeeklyPlanModel).filter(
            WeeklyPlanModel.id.in_(payload.planIds)
        ).all()
        
        if len(plans) != len(payload.planIds):
            raise HTTPException(
                status_code=404,
                detail="One or more plans not found"
            )
        
        logger.info(f"Generating procurement insights for {len(plans)} plans")
        
        # Convert plans to dictionaries for processing
        plans_data = []
        for plan in plans:
            plans_data.append({
                "id": plan.id,
                "patientName": plan.patient_name,
                "weekStart": plan.week_start,
                "days": plan.days
            })
        
        # Get LLM provider
        llm = get_llm_provider()
        
        # Build prompt
        prompt = build_procurement_insights_prompt(
            plans_data,
            payload.instructions or ""
        )
        
        # Generate insights
        result = llm.generate_json_completion(prompt, max_tokens=2000)
        
        # Parse response
        insights_data = json.loads(result['content'])
        
        # Prepare response
        response = ProcurementInsightsResponse(
            summary=insights_data.get("summary", "No summary available"),
            procurementNotes=insights_data.get("procurementNotes", []),
            generatedAt=datetime.utcnow().isoformat(),
            tokenUsage=TokenUsage(
                promptTokens=result['token_usage']['prompt_tokens'],
                completionTokens=result['token_usage']['completion_tokens']
            ) if 'token_usage' in result else None
        )
        
        logger.info(f"Generated procurement insights with {len(response.procurementNotes)} notes")
        
        return response
        
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse procurement insights from LLM"
        )
    except Exception as e:
        logger.error(f"Error generating procurement insights: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate procurement insights: {str(e)}"
        )


@router.post("/meal-suggestions")
async def get_meal_suggestions(
    patient_id: str,
    preferences: dict = None,
    db: Session = Depends(get_db)
):
    """
    Get AI-powered meal suggestions for a patient.
    This is an additional endpoint that could be useful for the frontend.
    """
    try:
        from src.db.models import PatientModel
        
        patient = db.query(PatientModel).filter(PatientModel.id == patient_id).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        llm = get_llm_provider()
        
        prompt = f"""Generate 3 meal suggestions for a patient with the following profile:
        
Patient:
- Age: {patient.age}
- Gender: {patient.gender}
- Calorie Target: {patient.calorie_target}
- Allergies: {', '.join(patient.allergies) if patient.allergies else 'None'}
- Dietary Restrictions: {', '.join([d['type'] for d in patient.dietary_restrictions]) if patient.dietary_restrictions else 'None'}

Additional Preferences: {preferences if preferences else 'None'}

Provide 3 creative, nutritious meal ideas that meet the patient's requirements.

Return JSON:
{{
  "suggestions": [
    {{
      "name": "Meal name",
      "description": "Brief description",
      "ingredients": ["ingredient1", "ingredient2"],
      "nutrition": {{"calories": 0, "protein": 0, "carbs": 0, "fat": 0}},
      "tags": ["tag1", "tag2"]
    }}
  ]
}}"""
        
        result = llm.generate_json_completion(prompt)
        suggestions_data = json.loads(result['content'])
        
        return {
            "patientId": patient_id,
            "suggestions": suggestions_data.get("suggestions", []),
            "generatedAt": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating meal suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate meal suggestions")
