"""
LLM Insights API endpoints for procurement analysis
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from datetime import datetime
import json
import logging
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Optional

from plan import (
    ProcurementInsightsPayload,
    ProcurementInsightsResponse,
    TokenUsage,
    ProcurementIngredientsPayload,
    AggregatedIngredient,
)
from database import get_db
from models import WeeklyPlanModel, RecipeModel
from provider import get_llm_provider
from prompts import build_procurement_insights_prompt

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/procurement-ingredients", response_model=List[AggregatedIngredient])
async def aggregate_procurement_ingredients(
    payload: ProcurementIngredientsPayload,
    db: Session = Depends(get_db),
):
    """
    Aggregate ingredient totals across selected plans using structured recipe data.
    """
    plans = db.query(WeeklyPlanModel).filter(
        WeeklyPlanModel.id.in_(payload.planIds)
    ).all()

    if len(plans) != len(payload.planIds):
        raise HTTPException(status_code=404, detail="One or more plans not found")

    meal_entries: List[Tuple[Optional[str], float, Optional[str]]] = []

    def _append_meal(meal_data):
        if not meal_data:
            return
        recipe_id = meal_data.get("recipeId") or meal_data.get("recipe_id")
        if not recipe_id:
            recipe_id = None
        portion = meal_data.get("portion") or 1
        try:
            portion_value = float(portion)
        except (TypeError, ValueError):
            portion_value = 1.0
        meal_name = meal_data.get("name") or meal_data.get("dish") or meal_data.get("title")
        meal_entries.append((recipe_id, portion_value, meal_name))

    for plan in plans:
        for day in plan.days or []:
            for meal_key in ["breakfast", "lunch", "dinner"]:
                _append_meal(day.get(meal_key))
            snacks = day.get("snacks")
            if isinstance(snacks, list):
                for snack in snacks:
                    _append_meal(snack)
            elif isinstance(snacks, dict):
                _append_meal(snacks)

    if not meal_entries:
        return []

    recipes = (
        db.query(RecipeModel)
        .options(selectinload(RecipeModel.ingredients))
        .all()
    )
    recipe_map = {recipe.external_id: recipe for recipe in recipes}
    recipe_name_map = _build_recipe_name_index(recipes)

    aggregated: Dict[Tuple[str, str], Dict[str, float | str | None]] = {}

    for recipe_id, portion, meal_name in meal_entries:
        recipe = recipe_map.get(recipe_id)
        if not recipe and meal_name:
            recipe = _match_recipe_by_name(meal_name, recipe_name_map)
        if not recipe:
            continue
        for ingredient in recipe.ingredients:
            if ingredient.quantity is None:
                continue
            canonical_name, display_name = _canonicalize_ingredient_name(
                ingredient.name
            )
            unit = _normalize_unit(ingredient.unit)
            key = (canonical_name, unit)
            if key not in aggregated:
                aggregated[key] = {
                    "name": display_name,
                    "unit": unit or None,
                    "quantity": 0.0,
                }
            aggregated[key]["quantity"] = float(aggregated[key]["quantity"]) + float(
                ingredient.quantity
            ) * portion

    results = []
    for (_, _), payload in sorted(
        aggregated.items(), key=lambda item: float(item[1]["quantity"]), reverse=True
    ):
        results.append(
            AggregatedIngredient(
                name=payload["name"],
                unit=payload["unit"],
                quantity=round(float(payload["quantity"]), 4),
            )
        )

    return results


def _normalize_recipe_key(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _build_recipe_name_index(recipes: List[RecipeModel]) -> Dict[str, RecipeModel]:
    name_index: Dict[str, RecipeModel] = {}
    for recipe in recipes:
        key = _normalize_recipe_key(recipe.meal_name)
        if key:
            name_index[key] = recipe
    return name_index


def _match_recipe_by_name(
    name: Optional[str], name_index: Dict[str, RecipeModel]
) -> Optional[RecipeModel]:
    if not name:
        return None

    normalized = _normalize_recipe_key(name)
    if not normalized:
        return None

    if normalized in name_index:
        return name_index[normalized]

    best_score = 0.0
    best_recipe: Optional[RecipeModel] = None

    for candidate_key, recipe in name_index.items():
        score = SequenceMatcher(None, normalized, candidate_key).ratio()
        if score > best_score:
            best_score = score
            best_recipe = recipe

    if best_score >= 0.8:
        return best_recipe

    return None


COOKING_DESCRIPTORS = {
    "fried",
    "baked",
    "grilled",
    "roasted",
    "roast",
    "scrambled",
    "poached",
    "steamed",
    "soft",
    "braised",
    "pureed",
    "low-sodium",
    "low",
    "high",
    "creamy",
    "plain",
    "with",
    "and",
}


def _canonicalize_ingredient_name(name: Optional[str]) -> Tuple[str, str]:
    if not name:
        return "", ""

    base = name.lower()
    base = re.sub(r"\(.*?\)", "", base)
    tokens = [token for token in re.split(r"[\s\-_/]+", base) if token]
    filtered: List[str] = []
    for token in tokens:
        token_clean = token.strip(",.")
        if token_clean in COOKING_DESCRIPTORS:
            continue
        filtered.append(token_clean)

    if not filtered:
        filtered = tokens if tokens else [base]

    canonical = " ".join(filtered).strip()
    if canonical.endswith("ies"):
        canonical = canonical[:-3] + "y"
    elif canonical.endswith("s") and not canonical.endswith("ss"):
        canonical = canonical[:-1]

    display_name = canonical.title()
    return canonical, display_name


def _normalize_unit(unit: Optional[str]) -> str:
    if not unit:
        return ""
    normalized = unit.strip().lower()
    replacements = {
        "units": "unit",
        "pcs": "pc",
        "pieces": "pc",
        "kgs": "kg",
        "lbs": "lb",
    }
    normalized = replacements.get(normalized, normalized)
    return normalized


def _generate_baseline_insights(plans_data: List[Dict]) -> ProcurementInsightsResponse:
    """Fallback insights when LLM is unavailable."""
    ingredient_counter: Counter[str] = Counter()
    
    for plan in plans_data:
        for day in plan.get("days", []):
            text = " ".join([
                str(day.get("breakfast", "")),
                str(day.get("lunch", "")),
                str(day.get("dinner", "")),
                str(day.get("snacks", "")),
            ]).lower()
            for ingredient in [
                "chicken", "salmon", "turkey", "beef", "egg",
                "quinoa", "oatmeal", "rice", "vegetable", "spinach",
                "broccoli", "potato", "berries", "banana", "apple",
                "yogurt", "nuts", "almond", "granola"
            ]:
                if ingredient in text:
                    ingredient_counter[ingredient] += 1
    
    top_items = ingredient_counter.most_common(5)
    notes = []
    if not top_items:
        notes.append("Unable to detect specific ingredients. Review meal descriptions for manual planning.")
    else:
        notes.append(
            "Top requested ingredients: " +
            ", ".join(f"{item} ({count} mentions)" for item, count in top_items)
        )
    
    notes.append(
        "Consider batching produce purchases mid-week to keep vegetables and fruits fresh."
    )
    notes.append(
        "Verify allergen-friendly substitutions for patients with dietary restrictions."
    )
    
    return ProcurementInsightsResponse(
        summary=f"Generated baseline procurement insights for {len(plans_data)} plan(s) without calling the LLM.",
        procurementNotes=notes,
        generatedAt=datetime.utcnow().isoformat(),
        tokenUsage=None
    )


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
        
        # Get LLM provider if available
        try:
            llm = get_llm_provider()
            llm_available = True
        except Exception as e:
            logger.warning(f"LLM provider unavailable, using baseline insights: {str(e)}")
            llm = None
            llm_available = False
        
        if llm_available:
            try:
                prompt = build_procurement_insights_prompt(
                    plans_data,
                    payload.instructions or ""
                )
                
                result = llm.generate_json_completion(prompt, max_tokens=2000)
                insights_data = json.loads(result['content'])
                
                response = ProcurementInsightsResponse(
                    summary=insights_data.get("summary", "No summary available"),
                    procurementNotes=insights_data.get("procurementNotes", []),
                    generatedAt=datetime.utcnow().isoformat(),
                    tokenUsage=TokenUsage(
                        promptTokens=result['token_usage']['prompt_tokens'],
                        completionTokens=result['token_usage']['completion_tokens']
                    ) if 'token_usage' in result else None
                )
            except Exception as e:
                logger.error(f"LLM insight generation failed, falling back to baseline: {str(e)}")
                response = _generate_baseline_insights(plans_data)
        else:
            response = _generate_baseline_insights(plans_data)
        
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
        from models import PatientModel
        
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
