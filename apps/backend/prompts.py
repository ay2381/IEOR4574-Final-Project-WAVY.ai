"""
Prompt templates for LLM-based meal planning and insights
"""
from typing import List, Dict, Any


def build_meal_plan_prompt(patient_data: Dict[str, Any], week_start: str) -> str:
    """Build prompt for generating a weekly meal plan"""
    
    patient_info = f"""
Patient Information:
- Name: {patient_data['name']}
- Age: {patient_data['age']}
- Gender: {patient_data['gender']}
- Calorie Target: {patient_data['calorieTarget']} calories/day
- Macro Targets: {patient_data['macroTargets']}
- Medical Conditions: {', '.join(patient_data['medicalConditions']) if patient_data['medicalConditions'] else 'None'}
- Allergies: {', '.join(patient_data['allergies']) if patient_data['allergies'] else 'None'}
- Dietary Restrictions: {', '.join([d['type'] for d in patient_data['dietaryRestrictions']]) if patient_data['dietaryRestrictions'] else 'None'}
"""
    
    prompt = f"""You are a professional nutritionist creating a personalized 7-day meal plan.

{patient_info}

Week Starting: {week_start}

Generate a complete 7-day meal plan with breakfast, lunch, dinner, and optional snacks for each day.

Requirements:
1. Each meal must meet the patient's calorie and macro targets.
2. Avoid all listed allergies completely.
3. Respect all dietary restrictions.
4. Consider medical conditions when planning meals.
5. Ensure variety across the week AND across patients (even if constraints match, rotate dishes, sides, or preparation style so plans are not identical).
6. Include realistic, practical recipes.
7. Every meal object MUST include a valid "recipe_id" referencing the provided recipe catalog. If no suitable recipe exists, craft a unique custom dish and supply a synthetic recipe_id (e.g., "custom_lunch_<patientName>_01").

Return ONLY a valid JSON object with this exact structure:
{{
  "days": [
    {{
      "date": "YYYY-MM-DD",
      "breakfast": {{
        "name": "Meal name",
        "description": "Brief description",
        "ingredients": ["ingredient1", "ingredient2"],
        "nutrition": {{
          "calories": 0,
          "protein": 0,
          "carbs": 0,
          "fat": 0,
          "fiber": 0,
          "sodium": 0
        }},
        "recipe_id": "recipe_identifier",
        "preparationTime": 30,
        "difficulty": "easy"
      }},
      "lunch": {{ ... }},
      "dinner": {{ ... }},
      "snacks": [],
      "totalCalories": 0,
      "totalNutrition": {{ ... }}
    }}
  ]
}}

Ensure all 7 days are included and nutrition values are realistic and accurate."""
    
    return prompt


def build_procurement_insights_prompt(plans_data: List[Dict[str, Any]], instructions: str = "") -> str:
    """Build prompt for generating procurement insights"""
    
    # Aggregate ingredients from all plans
    all_ingredients = []
    patient_names = []
    total_meals = 0
    
    for plan in plans_data:
        patient_names.append(plan['patientName'])
        for day in plan['days']:
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                meal = day.get(meal_type)
                if meal and 'ingredients' in meal:
                    all_ingredients.extend(meal['ingredients'])
                    total_meals += 1
            
            # Add snacks
            for snack in day.get('snacks', []):
                if 'ingredients' in snack:
                    all_ingredients.extend(snack['ingredients'])
                    total_meals += 1
    
    ingredient_counts = {}
    for ingredient in all_ingredients:
        ingredient_counts[ingredient] = ingredient_counts.get(ingredient, 0) + 1
    
    sorted_ingredients = sorted(ingredient_counts.items(), key=lambda x: x[1], reverse=True)
    
    prompt = f"""You are a procurement specialist analyzing meal plans for a nutrition facility.

Summary:
- Number of patients: {len(plans_data)}
- Patient names: {', '.join(patient_names)}
- Total meals planned: {total_meals}
- Unique ingredients: {len(ingredient_counts)}

Top 20 Most Used Ingredients:
"""
    
    for ingredient, count in sorted_ingredients[:20]:
        prompt += f"- {ingredient}: {count} times\n"
    
    if instructions:
        prompt += f"\nAdditional Instructions: {instructions}\n"
    
    prompt += """

Please provide:
1. A concise Markdown summary under the heading "### Summary" with 2-3 sentences.
2. A list of 6-8 procurement notes formatted in Markdown bullets that follow this structure:
   - **Bold Topic:** Clear recommendation with one actionable verb. Include categories such as bulk purchasing, storage, seasonal availability, cost optimization, quality requirements, supplier strategy, and dietary/medical considerations.
   - Use professional tone, avoid repetition, and keep each note under 160 characters.
3. Where relevant, highlight patient-specific considerations (e.g., **Diabetic substitutions**) in bold before the detail.

Return ONLY a valid JSON object:
{
  "summary": "Markdown summary text",
  "procurementNotes": [
    "- **Topic:** Recommendation",
    "- **Topic:** Recommendation",
    ...
  ]
}"""
    
    return prompt


def build_llm_meal_validation_prompt(meal_data: Dict[str, Any], patient_data: Dict[str, Any]) -> str:
    """Build prompt for validating meal appropriateness"""
    
    prompt = f"""Validate if this meal is appropriate for the patient.

Patient:
- Allergies: {', '.join(patient_data.get('allergies', [])) or 'None'}
- Dietary Restrictions: {', '.join([d['type'] for d in patient_data.get('dietaryRestrictions', [])]) or 'None'}
- Medical Conditions: {', '.join(patient_data.get('medicalConditions', [])) or 'None'}

Meal:
- Name: {meal_data['name']}
- Ingredients: {', '.join(meal_data['ingredients'])}

Return JSON:
{{
  "isValid": true/false,
  "issues": ["list of any concerns or conflicts"],
  "suggestions": ["alternative suggestions if not valid"]
}}"""
    
    return prompt
