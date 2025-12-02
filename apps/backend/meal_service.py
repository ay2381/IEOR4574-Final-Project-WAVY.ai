"""
Rule-based meal planning service (deterministic)
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from src.domain.plan import NutritionInfo, Meal, DailyMeals

logger = logging.getLogger(__name__)


class RuleBasedMealService:
    """Service for generating rule-based meal plans"""
    
    def __init__(self):
        # Meal database organized by dietary needs
        self.meal_templates = {
            "standard": self._get_standard_meals(),
            "vegetarian": self._get_vegetarian_meals(),
            "vegan": self._get_vegan_meals(),
            "low_sodium": self._get_low_sodium_meals(),
            "diabetic": self._get_diabetic_meals(),
        }
    
    def generate_weekly_plan(self, patient_data: Dict[str, Any], week_start: str) -> List[DailyMeals]:
        """Generate a rule-based weekly meal plan"""
        
        # Select appropriate meal template based on restrictions
        meal_set = self._select_meal_set(patient_data)
        calorie_target = patient_data['calorieTarget']
        
        # Generate 7 days of meals
        days = []
        start_date = datetime.fromisoformat(week_start)
        
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Cycle through meals to provide variety
            day_index = day_offset % len(meal_set["breakfast"])
            
            breakfast = self._adjust_meal_calories(
                meal_set["breakfast"][day_index],
                calorie_target * 0.25  # 25% of daily calories
            )
            
            lunch = self._adjust_meal_calories(
                meal_set["lunch"][day_index],
                calorie_target * 0.35  # 35% of daily calories
            )
            
            dinner = self._adjust_meal_calories(
                meal_set["dinner"][day_index],
                calorie_target * 0.35  # 35% of daily calories
            )
            
            snacks = [
                self._adjust_meal_calories(
                    meal_set["snacks"][day_index % len(meal_set["snacks"])],
                    calorie_target * 0.05  # 5% of daily calories
                )
            ]
            
            # Calculate totals
            total_calories = (
                breakfast.nutrition.calories +
                lunch.nutrition.calories +
                dinner.nutrition.calories +
                sum(s.nutrition.calories for s in snacks)
            )
            
            total_nutrition = NutritionInfo(
                calories=total_calories,
                protein=breakfast.nutrition.protein + lunch.nutrition.protein + dinner.nutrition.protein,
                carbs=breakfast.nutrition.carbs + lunch.nutrition.carbs + dinner.nutrition.carbs,
                fat=breakfast.nutrition.fat + lunch.nutrition.fat + dinner.nutrition.fat,
                fiber=breakfast.nutrition.fiber + lunch.nutrition.fiber + dinner.nutrition.fiber,
                sodium=breakfast.nutrition.sodium + lunch.nutrition.sodium + dinner.nutrition.sodium
            )
            
            daily_meals = DailyMeals(
                date=date_str,
                breakfast=breakfast,
                lunch=lunch,
                dinner=dinner,
                snacks=snacks,
                totalCalories=total_calories,
                totalNutrition=total_nutrition
            )
            
            days.append(daily_meals)
        
        return days
    
    def _select_meal_set(self, patient_data: Dict[str, Any]) -> Dict[str, List[Meal]]:
        """Select appropriate meal set based on patient restrictions"""
        
        # Check for dietary restrictions
        restrictions = [d['type'].lower() for d in patient_data.get('dietaryRestrictions', [])]
        conditions = [c.lower() for c in patient_data.get('medicalConditions', [])]
        
        if 'vegan' in restrictions:
            return self.meal_templates['vegan']
        elif 'vegetarian' in restrictions:
            return self.meal_templates['vegetarian']
        elif 'diabetes' in conditions or 'diabetic' in conditions:
            return self.meal_templates['diabetic']
        elif 'low-sodium' in restrictions or 'hypertension' in conditions:
            return self.meal_templates['low_sodium']
        else:
            return self.meal_templates['standard']
    
    def _adjust_meal_calories(self, meal_template: Meal, target_calories: float) -> Meal:
        """Adjust meal portions to hit target calories"""
        current_calories = meal_template.nutrition.calories
        ratio = target_calories / current_calories if current_calories > 0 else 1.0
        
        return Meal(
            name=meal_template.name,
            description=meal_template.description,
            ingredients=meal_template.ingredients.copy(),
            nutrition=NutritionInfo(
                calories=int(target_calories),
                protein=round(meal_template.nutrition.protein * ratio, 1),
                carbs=round(meal_template.nutrition.carbs * ratio, 1),
                fat=round(meal_template.nutrition.fat * ratio, 1),
                fiber=round(meal_template.nutrition.fiber * ratio, 1),
                sodium=round(meal_template.nutrition.sodium * ratio, 1)
            ),
            preparationTime=meal_template.preparationTime,
            difficulty=meal_template.difficulty
        )
    
    def _get_standard_meals(self) -> Dict[str, List[Meal]]:
        """Standard meal templates"""
        return {
            "breakfast": [
                Meal(
                    name="Greek Yogurt Parfait",
                    description="Protein-rich parfait with berries and granola",
                    ingredients=["Greek yogurt", "mixed berries", "granola", "honey"],
                    nutrition=NutritionInfo(calories=350, protein=20, carbs=45, fat=10, fiber=5, sodium=100),
                    preparationTime=10,
                    difficulty="easy"
                ),
                Meal(
                    name="Scrambled Eggs with Toast",
                    description="Classic eggs with whole wheat toast and avocado",
                    ingredients=["eggs", "whole wheat bread", "avocado", "butter", "salt", "pepper"],
                    nutrition=NutritionInfo(calories=400, protein=22, carbs=35, fat=18, fiber=8, sodium=400),
                    preparationTime=15,
                    difficulty="easy"
                ),
                Meal(
                    name="Oatmeal Bowl",
                    description="Steel-cut oats with banana and almonds",
                    ingredients=["steel-cut oats", "banana", "almonds", "cinnamon", "honey"],
                    nutrition=NutritionInfo(calories=380, protein=12, carbs=58, fat=12, fiber=10, sodium=5),
                    preparationTime=20,
                    difficulty="easy"
                ),
            ],
            "lunch": [
                Meal(
                    name="Grilled Chicken Salad",
                    description="Mixed greens with grilled chicken breast",
                    ingredients=["chicken breast", "mixed greens", "cherry tomatoes", "cucumber", "olive oil", "balsamic vinegar"],
                    nutrition=NutritionInfo(calories=450, protein=40, carbs=25, fat=22, fiber=6, sodium=350),
                    preparationTime=25,
                    difficulty="medium"
                ),
                Meal(
                    name="Turkey Wrap",
                    description="Whole wheat wrap with turkey and vegetables",
                    ingredients=["whole wheat tortilla", "turkey breast", "lettuce", "tomato", "cheese", "mustard"],
                    nutrition=NutritionInfo(calories=420, protein=35, carbs=40, fat=15, fiber=5, sodium=800),
                    preparationTime=10,
                    difficulty="easy"
                ),
                Meal(
                    name="Quinoa Buddha Bowl",
                    description="Quinoa with roasted vegetables and chickpeas",
                    ingredients=["quinoa", "chickpeas", "sweet potato", "broccoli", "tahini dressing"],
                    nutrition=NutritionInfo(calories=480, protein=18, carbs=65, fat=16, fiber=12, sodium=300),
                    preparationTime=30,
                    difficulty="medium"
                ),
            ],
            "dinner": [
                Meal(
                    name="Baked Salmon with Vegetables",
                    description="Herb-crusted salmon with roasted vegetables",
                    ingredients=["salmon fillet", "asparagus", "bell peppers", "olive oil", "herbs", "lemon"],
                    nutrition=NutritionInfo(calories=550, protein=45, carbs=30, fat=28, fiber=8, sodium=450),
                    preparationTime=35,
                    difficulty="medium"
                ),
                Meal(
                    name="Chicken Stir-Fry",
                    description="Asian-style chicken with mixed vegetables",
                    ingredients=["chicken breast", "broccoli", "carrots", "snap peas", "soy sauce", "ginger", "brown rice"],
                    nutrition=NutritionInfo(calories=520, protein=42, carbs=55, fat=14, fiber=7, sodium=600),
                    preparationTime=25,
                    difficulty="medium"
                ),
                Meal(
                    name="Lean Beef with Sweet Potato",
                    description="Grilled lean beef with roasted sweet potato",
                    ingredients=["lean beef", "sweet potato", "green beans", "olive oil", "garlic"],
                    nutrition=NutritionInfo(calories=580, protein=48, carbs=45, fat=20, fiber=9, sodium=400),
                    preparationTime=40,
                    difficulty="medium"
                ),
            ],
            "snacks": [
                Meal(
                    name="Apple with Almond Butter",
                    description="Fresh apple slices with natural almond butter",
                    ingredients=["apple", "almond butter"],
                    nutrition=NutritionInfo(calories=200, protein=6, carbs=25, fat=10, fiber=5, sodium=0),
                    preparationTime=5,
                    difficulty="easy"
                ),
                Meal(
                    name="Protein Smoothie",
                    description="Banana protein smoothie with spinach",
                    ingredients=["banana", "protein powder", "spinach", "almond milk"],
                    nutrition=NutritionInfo(calories=220, protein=20, carbs=28, fat=4, fiber=4, sodium=150),
                    preparationTime=5,
                    difficulty="easy"
                ),
            ]
        }
    
    def _get_vegetarian_meals(self) -> Dict[str, List[Meal]]:
        """Vegetarian meal templates"""
        meals = self._get_standard_meals()
        # Replace meat-based meals with vegetarian alternatives
        meals["lunch"][0] = Meal(
            name="Mediterranean Lentil Salad",
            description="Protein-rich lentils with feta and vegetables",
            ingredients=["lentils", "feta cheese", "cucumber", "tomatoes", "olive oil", "lemon"],
            nutrition=NutritionInfo(calories=420, protein=22, carbs=50, fat=16, fiber=15, sodium=400),
            preparationTime=25,
            difficulty="easy"
        )
        meals["dinner"][0] = Meal(
            name="Eggplant Parmesan",
            description="Baked eggplant with marinara and mozzarella",
            ingredients=["eggplant", "marinara sauce", "mozzarella", "parmesan", "basil"],
            nutrition=NutritionInfo(calories=480, protein=24, carbs=45, fat=22, fiber=10, sodium=700),
            preparationTime=45,
            difficulty="medium"
        )
        return meals
    
    def _get_vegan_meals(self) -> Dict[str, List[Meal]]:
        """Vegan meal templates"""
        return {
            "breakfast": [
                Meal(
                    name="Tofu Scramble",
                    description="Scrambled tofu with vegetables",
                    ingredients=["firm tofu", "bell peppers", "onions", "spinach", "turmeric", "nutritional yeast"],
                    nutrition=NutritionInfo(calories=320, protein=18, carbs=28, fat=16, fiber=6, sodium=300),
                    preparationTime=15,
                    difficulty="easy"
                ),
            ],
            "lunch": [
                Meal(
                    name="Chickpea Buddha Bowl",
                    description="Roasted chickpeas with quinoa and tahini",
                    ingredients=["chickpeas", "quinoa", "kale", "sweet potato", "tahini", "lemon"],
                    nutrition=NutritionInfo(calories=480, protein=20, carbs=65, fat=16, fiber=14, sodium=250),
                    preparationTime=30,
                    difficulty="medium"
                ),
            ],
            "dinner": [
                Meal(
                    name="Lentil Curry",
                    description="Red lentil curry with coconut milk",
                    ingredients=["red lentils", "coconut milk", "curry spices", "tomatoes", "spinach", "brown rice"],
                    nutrition=NutritionInfo(calories=520, protein=22, carbs=68, fat=18, fiber=16, sodium=400),
                    preparationTime=35,
                    difficulty="medium"
                ),
            ],
            "snacks": [
                Meal(
                    name="Hummus with Vegetables",
                    description="Homemade hummus with carrot and celery sticks",
                    ingredients=["chickpeas", "tahini", "lemon", "carrots", "celery"],
                    nutrition=NutritionInfo(calories=180, protein=8, carbs=20, fat=8, fiber=7, sodium=200),
                    preparationTime=10,
                    difficulty="easy"
                ),
            ]
        }
    
    def _get_low_sodium_meals(self) -> Dict[str, List[Meal]]:
        """Low-sodium meal templates"""
        meals = self._get_standard_meals()
        # Adjust sodium levels in all meals
        for meal_type in meals:
            for meal in meals[meal_type]:
                meal.nutrition.sodium = min(meal.nutrition.sodium, 200)
        return meals
    
    def _get_diabetic_meals(self) -> Dict[str, List[Meal]]:
        """Diabetic-friendly meal templates with controlled carbs"""
        meals = self._get_standard_meals()
        # Adjust carb levels and add more fiber
        for meal_type in meals:
            for meal in meals[meal_type]:
                meal.nutrition.carbs = int(meal.nutrition.carbs * 0.7)
                meal.nutrition.fiber = meal.nutrition.fiber * 1.5
                meal.nutrition.protein = meal.nutrition.protein * 1.2
        return meals
