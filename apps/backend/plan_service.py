"""
Plan generation service - orchestrates meal planning strategies
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from src.domain.plan import WeeklyPlan, DailyMeals, NutritionInfo, Meal
from src.services.meal_service import RuleBasedMealService
from src.llm.provider import get_llm_provider
from src.llm.prompts import build_meal_plan_prompt

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
        patient_data: Dict[str, Any],
        week_start: str
    ) -> Dict[str, Any]:
        """Generate meal plan using LLM"""
        
        logger.info(f"Generating LLM-based plan for patient {patient_data['name']}")
        
        try:
            # Get LLM provider
            llm = get_llm_provider()
            
            # Build prompt
            prompt = build_meal_plan_prompt(patient_data, week_start)
            
            # Generate completion
            result = llm.generate_json_completion(prompt, max_tokens=4000)
            
            # Parse JSON response
            plan_data = json.loads(result['content'])
            
            # Validate and normalize the response
            days = self._normalize_llm_response(plan_data['days'], week_start)
            
            # Calculate weekly totals
            weekly_totals = {
                "totalCalories": sum(day['totalCalories'] for day in days),
                "avgDailyCalories": sum(day['totalCalories'] for day in days) / 7,
                "totalProtein": sum(day['totalNutrition']['protein'] for day in days),
                "totalCarbs": sum(day['totalNutrition']['carbs'] for day in days),
                "totalFat": sum(day['totalNutrition']['fat'] for day in days),
                "tokenUsage": result.get('token_usage', {})
            }
            
            return {
                "days": days,
                "weeklyTotals": weekly_totals
            }
            
        except Exception as e:
            logger.error(f"LLM plan generation failed: {str(e)}")
            logger.warning("Falling back to rule-based generation")
            # Fallback to rule-based if LLM fails
            return self.generate_plan_rule_based(patient_data, week_start)
    
    def _normalize_llm_response(self, days: List[Dict], week_start: str) -> List[Dict]:
        """Normalize LLM response to match expected schema"""
        
        normalized_days = []
        start_date = datetime.fromisoformat(week_start)
        
        for i, day in enumerate(days):
            # Ensure correct date
            expected_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            day['date'] = expected_date
            
            # Ensure all required meal types exist
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                if meal_type not in day:
                    logger.warning(f"Missing {meal_type} in LLM response, using placeholder")
                    day[meal_type] = self._get_placeholder_meal(meal_type)
            
            # Ensure snacks is a list
            if 'snacks' not in day:
                day['snacks'] = []
            
            # Calculate totals if not provided
            if 'totalCalories' not in day or 'totalNutrition' not in day:
                day = self._calculate_daily_totals(day)
            
            normalized_days.append(day)
        
        # Ensure we have exactly 7 days
        while len(normalized_days) < 7:
            date = (start_date + timedelta(days=len(normalized_days))).strftime("%Y-%m-%d")
            normalized_days.append(self._get_placeholder_day(date))
        
        return normalized_days[:7]
    
    def _calculate_daily_totals(self, day: Dict) -> Dict:
        """Calculate total calories and nutrition for a day"""
        
        total_calories = 0
        total_nutrition = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "sodium": 0
        }
        
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            meal = day.get(meal_type, {})
            nutrition = meal.get('nutrition', {})
            total_calories += nutrition.get('calories', 0)
            for key in total_nutrition:
                total_nutrition[key] += nutrition.get(key, 0)
        
        for snack in day.get('snacks', []):
            nutrition = snack.get('nutrition', {})
            total_calories += nutrition.get('calories', 0)
            for key in total_nutrition:
                total_nutrition[key] += nutrition.get(key, 0)
        
        day['totalCalories'] = total_calories
        day['totalNutrition'] = total_nutrition
        
        return day
    
    def _get_placeholder_meal(self, meal_type: str) -> Dict:
        """Get a placeholder meal"""
        return {
            "name": f"Healthy {meal_type.title()}",
            "description": "A balanced, nutritious meal",
            "ingredients": ["whole grains", "lean protein", "vegetables"],
            "nutrition": {
                "calories": 400,
                "protein": 25,
                "carbs": 45,
                "fat": 12,
                "fiber": 8,
                "sodium": 300
            },
            "preparationTime": 30,
            "difficulty": "medium"
        }
    
    def _get_placeholder_day(self, date: str) -> Dict:
        """Get a placeholder day"""
        return {
            "date": date,
            "breakfast": self._get_placeholder_meal("breakfast"),
            "lunch": self._get_placeholder_meal("lunch"),
            "dinner": self._get_placeholder_meal("dinner"),
            "snacks": [],
            "totalCalories": 1200,
            "totalNutrition": {
                "calories": 1200,
                "protein": 75,
                "carbs": 135,
                "fat": 36,
                "fiber": 24,
                "sodium": 900
            }
        }
