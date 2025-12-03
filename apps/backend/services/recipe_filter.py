"""
Utilities for filtering safe recipes and building LLM prompts.
"""

from __future__ import annotations

import json
from typing import Iterable, List, Sequence, Set, Any

from sqlalchemy.orm import Session

from models import RecipeModel, DiseaseRuleModel


def _lower_list(values: Iterable[str] | None) -> List[str]:
    return [str(v).strip().lower() for v in (values or []) if str(v).strip()]


def _get_patient_field(patient: Any, attr: str, default=None):
    if hasattr(patient, attr):
        value = getattr(patient, attr)
    elif isinstance(patient, dict):
        value = patient.get(attr, default)
    else:
        value = default
    return value if value is not None else default


class RecipeFilterService:
    def __init__(self, db: Session):
        self.db = db

    def _load_rules(self) -> Sequence[DiseaseRuleModel]:
        return self.db.query(DiseaseRuleModel).all()

    def _match_prohibited_tags(
        self, conditions: Sequence[str], rules: Sequence[DiseaseRuleModel]
    ) -> Set[str]:
        normalized_conditions = [c.lower() for c in conditions]
        prohibited: Set[str] = set()
        for rule in rules:
            rule_name = rule.name.lower()
            if any(c in rule_name or rule_name in c for c in normalized_conditions):
                prohibited.update(_lower_list(rule.prohibited_tags))
        return prohibited

    def get_safe_recipes_for_patient(self, patient: Any) -> List[RecipeModel]:
        conditions = _get_patient_field(patient, "medical_conditions", []) or []
        allergies = _get_patient_field(patient, "allergies", []) or []

        rules = self._load_rules()
        prohibited_tags = self._match_prohibited_tags(conditions, rules)
        allergy_terms = set(_lower_list(allergies))

        recipes = self.db.query(RecipeModel).all()
        safe: List[RecipeModel] = []
        for recipe in recipes:
            if self._is_recipe_safe(recipe, prohibited_tags, allergy_terms):
                safe.append(recipe)
        return safe

    def _is_recipe_safe(
        self, recipe: RecipeModel, prohibited_tags: Set[str], allergies: Set[str]
    ) -> bool:
        recipe_tags = set(_lower_list(recipe.tags))
        if recipe_tags.intersection(prohibited_tags):
            return False

        recipe_allergens = set(_lower_list(recipe.allergens))
        if recipe_allergens.intersection(allergies):
            return False

        for ingredient in recipe.ingredients:
            name = (ingredient.name or "").lower()
            if any(allergen in name or name in allergen for allergen in allergies):
                return False
        return True

    def build_llm_prompt(self, patient: Any, recipes: List[RecipeModel]) -> str:
        recipe_context = [
            {
                "recipe_id": recipe.external_id,
                "meal_name": recipe.meal_name,
                "meal_type": recipe.meal_type,
                "calories_per_serving": recipe.calories_per_serving,
                "protein_g": recipe.protein_g,
                "carbs_g": recipe.carbs_g,
                "fat_g": recipe.fat_g,
                "tags": recipe.tags,
            }
            for recipe in recipes
        ]

        patient_name = _get_patient_field(patient, "name", "Patient")
        age = _get_patient_field(patient, "age", "Unknown")
        gender = _get_patient_field(patient, "gender", "Unknown")
        medical_conditions = _get_patient_field(patient, "medical_conditions", []) or []
        allergies = _get_patient_field(patient, "allergies", []) or []
        calorie_target = _get_patient_field(patient, "calorie_target", 2000)

        prompt = f"""You are an expert Convalescent Home Nutrition Planner.

PATIENT PROFILE:
- Name: {patient_name}
- Age: {age}
- Gender: {gender}
- Medical Conditions: {', '.join(medical_conditions) or 'None'}
- Allergies: {', '.join(allergies) or 'None'}
- Daily Calorie Target: {calorie_target} calories

Use only the following pre-approved recipes:
{json.dumps(recipe_context, indent=2)}

TASK:
Create a complete 7-day meal plan (Day 1 through Day 7).
Each day must include breakfast, lunch, dinner, and an optional snack.
Stay within ±10% of the calorie target per day.
Ensure variety and respect medical and allergy constraints.

Return valid JSON with this structure:
{{
  "days": [
    {{
      "date": "YYYY-MM-DD",
      "breakfast": {{"recipe_id": "r_001", "portion": 1}},
      "lunch": {{ ... }},
      "dinner": {{ ... }},
      "snacks": [{{ ... }}],
      "totalCalories": 0,
      "totalNutrition": {{"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sodium": 0}}
    }}
  ]
}}
"""
        return prompt

