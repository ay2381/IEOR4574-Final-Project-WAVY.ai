"""
Plan generation service - orchestrates meal planning strategies
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import json
import logging
import re

from sqlalchemy.orm import Session

from meal_service import RuleBasedMealService
from provider import get_llm_provider
from services.recipe_filter import RecipeFilterService
from models import PatientModel, RecipeModel
from config import settings

logger = logging.getLogger(__name__)


class PlanGenerationService:
    """Service for generating meal plans using different strategies"""
    
    def __init__(self):
        self.rule_based_service = RuleBasedMealService()
    
    def generate_plan_rule_based(
        self,
        patient_data: Dict[str, Any],
        week_start: str
    ) -> Dict[str, Any]:
        """Generate meal plan using rule-based approach"""
        
        logger.info(f"Generating rule-based plan for patient {patient_data['name']}")
        
        days = self.rule_based_service.generate_weekly_plan(patient_data, week_start)
        
        # Calculate weekly totals
        weekly_totals = {
            "totalCalories": sum(day.totalCalories for day in days),
            "avgDailyCalories": sum(day.totalCalories for day in days) / 7,
            "totalProtein": sum(day.totalNutrition.protein for day in days),
            "totalCarbs": sum(day.totalNutrition.carbs for day in days),
            "totalFat": sum(day.totalNutrition.fat for day in days),
        }
        
        return {
            "days": [day.model_dump() for day in days],
            "weeklyTotals": weekly_totals
        }
    
    def generate_plan_llm(
        self,
        patient: PatientModel,
        week_start: str,
        db: Session,
    ) -> Dict[str, Any]:
        """Generate meal plan using LLM + recipe catalog."""

        patient_name = getattr(patient, "name", "patient")
        logger.info(f"Generating LLM-based plan for patient {patient_name}")

        recipe_service = RecipeFilterService(db)
        safe_recipes = recipe_service.get_safe_recipes_for_patient(patient)

        if not safe_recipes:
            logger.error(
                "No safe recipes available for patient %s. Unable to build plan.",
                patient_name,
            )
            raise ValueError(
                f"No safe recipes available for patient {patient_name}. "
                "Please expand the recipe catalog or relax filters."
            )

        try:
            llm = get_llm_provider()
            prompt = recipe_service.build_llm_prompt(patient, safe_recipes)
            result = llm.generate_json_completion(
                prompt, max_tokens=min(4000, settings.MAX_TOKENS)
            )

            plan_data = json.loads(result["content"])
            recipe_lookup = {
                recipe.external_id: recipe for recipe in safe_recipes if recipe.external_id
            }
            recipe_name_lookup = self._build_recipe_name_index(recipe_lookup)
            days = self._normalize_llm_response(
                plan_data.get("days", []),
                week_start,
                recipe_lookup,
                recipe_name_lookup,
            )

            weekly_totals = self._calculate_weekly_totals(days, result.get("token_usage"))
            return {
                "days": days,
                "weeklyTotals": weekly_totals,
            }

        except Exception as exc:
            logger.error("LLM plan generation failed: %s", exc, exc_info=True)
            raise

    def _normalize_llm_response(
        self,
        days: List[Dict[str, Any]],
        week_start: str,
        recipe_lookup: Optional[Dict[str, RecipeModel]] = None,
        recipe_name_lookup: Optional[Dict[str, RecipeModel]] = None,
    ) -> List[Dict[str, Any]]:
        """Normalize and hydrate the LLM response into full meals."""

        normalized_days: List[Dict[str, Any]] = []
        start_date = datetime.fromisoformat(week_start)

        if len(days) != 7:
            raise ValueError("LLM must return exactly 7 days of meals")

        for i in range(7):
            day_payload = days[i]
            date_str = day_payload.get("date") or (start_date + timedelta(days=i)).strftime(
                "%Y-%m-%d"
            )

            day_struct = {
                "date": date_str,
                "breakfast": self._resolve_meal_entry(
                    day_payload.get("breakfast"),
                    "breakfast",
                    recipe_lookup,
                    recipe_name_lookup,
                ),
                "lunch": self._resolve_meal_entry(
                    day_payload.get("lunch"),
                    "lunch",
                    recipe_lookup,
                    recipe_name_lookup,
                ),
                "dinner": self._resolve_meal_entry(
                    day_payload.get("dinner"),
                    "dinner",
                    recipe_lookup,
                    recipe_name_lookup,
                ),
                "snacks": [
                    self._resolve_meal_entry(
                        snack, "snack", recipe_lookup, recipe_name_lookup
                    )
                    for snack in day_payload.get("snacks", []) or []
                ],
            }

            day_struct = self._calculate_daily_totals(day_struct)
            normalized_days.append(day_struct)

        return normalized_days

    def _resolve_meal_entry(
        self,
        meal_data: Optional[Dict[str, Any]],
        meal_type: str,
        recipe_lookup: Optional[Dict[str, RecipeModel]],
        recipe_name_lookup: Optional[Dict[str, RecipeModel]],
    ) -> Dict[str, Any]:
        """Convert a meal spec (recipe reference or full meal) into a canonical meal dict."""

        if meal_data is None:
            raise ValueError(f"Missing {meal_type} entry in LLM response.")

        portion = meal_data.get("portion") or meal_data.get("servings") or 1

        if recipe_lookup:
            recipe_id = meal_data.get("recipe_id") or meal_data.get("recipeId")
            if recipe_id and recipe_id in recipe_lookup:
                return self._meal_from_recipe(recipe_lookup[recipe_id], portion)

            if recipe_name_lookup:
                candidate_name = (
                    meal_data.get("name")
                    or meal_data.get("dish")
                    or meal_data.get("title")
                )
                matched_recipe = self._match_recipe_by_name(
                    candidate_name, recipe_name_lookup
                )
                if matched_recipe:
                    return self._meal_from_recipe(matched_recipe, portion)

        raise ValueError(f"Unable to resolve {meal_type} entry: {meal_data}")

    @staticmethod
    def _normalize_recipe_key(value: Optional[str]) -> str:
        if not value:
            return ""
        return re.sub(r"[^a-z0-9]", "", value.lower())

    def _build_recipe_name_index(
        self, recipe_lookup: Dict[str, RecipeModel]
    ) -> Dict[str, RecipeModel]:
        name_index: Dict[str, RecipeModel] = {}
        for recipe in recipe_lookup.values():
            key = self._normalize_recipe_key(recipe.meal_name)
            if key:
                name_index[key] = recipe
        return name_index

    def _match_recipe_by_name(
        self, name: Optional[str], name_index: Optional[Dict[str, RecipeModel]]
    ) -> Optional[RecipeModel]:
        if not name or not name_index:
            return None

        normalized = self._normalize_recipe_key(name)
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

    def _meal_from_recipe(self, recipe: RecipeModel, portion: float) -> Dict[str, Any]:
        """Create a Meal dict from a recipe and portion size."""

        portion = float(portion or 1)
        calories = (recipe.calories_per_serving or 0) * portion
        protein = (recipe.protein_g or 0) * portion
        carbs = (recipe.carbs_g or 0) * portion
        fat = (recipe.fat_g or 0) * portion

        ingredients = [
            ingredient.raw or f"{ingredient.quantity or ''} {ingredient.unit or ''} {ingredient.name}".strip()
            for ingredient in recipe.ingredients
        ]
        if not ingredients and recipe.ingredient_text:
            ingredients = [
                item.strip()
                for item in recipe.ingredient_text.split(";")
                if item.strip()
            ]

        description = recipe.meal_type or "Chef-crafted meal"
        highlights = recipe.tags or []

        return {
            "name": recipe.meal_name,
            "description": description,
            "highlights": highlights,
            "ingredients": ingredients or [recipe.meal_name],
            "nutrition": {
                "calories": int(round(calories)),
                "protein": round(protein, 1),
                "carbs": round(carbs, 1),
                "fat": round(fat, 1),
                "fiber": 0,
                "sodium": 0,
            },
            "preparationTime": 30,
            "difficulty": "medium",
            "portion": portion,
            "recipeId": recipe.external_id,
        }

    def _calculate_daily_totals(self, day: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total calories and nutrition for a day."""

        totals = {
            "calories": 0,
            "protein": 0.0,
            "carbs": 0.0,
            "fat": 0.0,
            "fiber": 0.0,
            "sodium": 0.0,
        }
        total_calories = 0

        def accumulate(meal: Dict[str, Any]):
            nonlocal total_calories
            nutrition = meal.get("nutrition", {})
            total_calories += nutrition.get("calories", 0) or 0
            for key in totals:
                totals[key] += nutrition.get(key, 0) or 0

        for meal_key in ["breakfast", "lunch", "dinner"]:
            accumulate(day.get(meal_key, {}))

        for snack in day.get("snacks", []):
            accumulate(snack)

        day["totalCalories"] = int(round(total_calories))
        day["totalNutrition"] = {
            "calories": int(round(totals["calories"])),
            "protein": round(totals["protein"], 1),
            "carbs": round(totals["carbs"], 1),
            "fat": round(totals["fat"], 1),
            "fiber": round(totals["fiber"], 1),
            "sodium": round(totals["sodium"], 1),
        }
        return day

    def _calculate_weekly_totals(
        self, days: List[Dict[str, Any]], token_usage: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Aggregate weekly totals."""

        total_calories = sum(day["totalCalories"] for day in days)
        total_protein = sum(day["totalNutrition"]["protein"] for day in days)
        total_carbs = sum(day["totalNutrition"]["carbs"] for day in days)
        total_fat = sum(day["totalNutrition"]["fat"] for day in days)

        weekly_totals = {
            "totalCalories": total_calories,
            "avgDailyCalories": round(total_calories / len(days), 1) if days else 0,
            "totalProtein": round(total_protein, 1),
            "totalCarbs": round(total_carbs, 1),
            "totalFat": round(total_fat, 1),
        }

        if token_usage:
            weekly_totals["tokenUsage"] = token_usage

        return weekly_totals

    def _serialize_patient(self, patient: Any) -> Dict[str, Any]:
        """Convert PatientModel (or dict) into payload used by rule-based service."""

        if isinstance(patient, dict):
            return patient

        return {
            "name": getattr(patient, "name", "Patient"),
            "age": getattr(patient, "age", None),
            "gender": getattr(patient, "gender", "other"),
            "medicalConditions": getattr(patient, "medical_conditions", []) or [],
            "allergies": getattr(patient, "allergies", []) or [],
            "dietaryRestrictions": getattr(patient, "dietary_restrictions", []) or [],
            "calorieTarget": getattr(patient, "calorie_target", 2000),
            "macroTargets": getattr(patient, "macro_targets", {}) or {},
        }
    
