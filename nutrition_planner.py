import pandas as pd
import json
import re
import os
import sys
from pathlib import Path
import google.generativeai as genai
from typing import List, Dict, Any, Tuple

# Configure Gemini API
# Ensure you have 'GOOGLE_API_KEY' in your environment variables
if "GOOGLE_API_KEY" in os.environ:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
else:
    print("Warning: GOOGLE_API_KEY environment variable not set. LLM calls will fail.")

def load_data(recipes_csv_path: str, rules_csv_path: str) -> Tuple[pd.DataFrame, Dict]:
    """
    Step 1: Data Parsing
    Parses CSV files and processes ingredient_proportion into structured data.
    
    Args:
        recipes_csv_path: Path to Recipes_with_Ingredients.csv
        rules_csv_path: Path to Disease_rules.csv
        
    Returns:
        Tuple of (parsed_recipes_df, rules_dict)
    """
    print(f"[Loading Data] Loading recipes from {recipes_csv_path}")
    print(f"[Loading Data] Loading rules from {rules_csv_path}")
    
    # Load DataFrames
    df_recipes = pd.read_csv(recipes_csv_path)
    df_rules = pd.read_csv(rules_csv_path)
    
    print(f"[Loading Data] Loaded {len(df_recipes)} recipes")
    print(f"[Loading Data] Loaded {len(df_rules)} disease rules")

    # Helper function to parse ingredient string
    def parse_ingredients(ing_str: str) -> List[Dict[str, Any]]:
        """
        Parse ingredient_proportion string into structured format.
        
        Expected format: "Chicken: 0.2 kg; Rice: 0.1 kg"
        Returns: [{'name': 'Chicken', 'quantity': 0.2, 'unit': 'kg'}, ...]
        """
        ingredients = []
        if pd.isna(ing_str):
            return ingredients
        
        # Split by semicolon
        parts = ing_str.split(';')
        for part in parts:
            # Regex to extract Name, Quantity, Unit
            # Matches: "Name: Quantity Unit (Optional Note)" or "Name: Quantity Unit"
            # e.g., "Chicken: 0.2 kg" -> ('Chicken', '0.2', 'kg')
            match = re.search(r'^\s*([^:]+):\s*([\d.]+)\s*([a-zA-Z]+)', part)
            if match:
                ingredients.append({
                    'name': match.group(1).strip(),
                    'quantity': float(match.group(2)),
                    'unit': match.group(3).strip(),
                    'raw': part.strip()
                })
        return ingredients

    # Apply parsing
    df_recipes['parsed_ingredients'] = df_recipes['ingredient_proportion'].apply(parse_ingredients)
    
    # Clean up tags and allergens for easier filtering
    df_recipes['tags_list'] = df_recipes['tags'].fillna('').apply(
        lambda x: [t.strip().lower() for t in x.split(';') if t.strip()]
    )
    df_recipes['allergens_list'] = df_recipes['allergens'].fillna('').apply(
        lambda x: [a.strip().lower() for a in x.split(';') if a.strip().lower() != 'none'] 
        if x.lower() != 'none' else []
    )

    # Process Rules - map disease conditions to forbidden tags
    rules_dict = {}
    for _, row in df_rules.iterrows():
        condition = row['Disease'].strip()
        tags = [t.strip().lower() for t in row['Prohibited_Tags'].split(';') if t.strip()]
        rules_dict[condition] = tags

    print(f"[Loading Data] Parsed {len(rules_dict)} disease rules")
    return df_recipes, rules_dict

def normalize_patient_profile(patient_data: Dict) -> Dict:
    """
    Normalize patient profile JSON to expected format.
    Handles both old format (Medical Condition, Allergies) and new format (medical_conditions, allergies).
    
    Args:
        patient_data: Raw patient JSON data
        
    Returns:
        Normalized patient profile dict
    """
    profile = {
        'name': patient_data.get('Name') or patient_data.get('name') or 'Patient',
        'age': patient_data.get('Age') or patient_data.get('age'),
        'gender': patient_data.get('Gender') or patient_data.get('gender'),
        'medical_conditions': patient_data.get('medical_conditions') or patient_data.get('Medical Condition') or [],
        'allergies': patient_data.get('allergies') or patient_data.get('Allergies') or [],
        'daily_calorie_target': patient_data.get('daily_calorie_target', 2000)  # Default target
    }
    
    # Normalize lists to lowercase for case-insensitive matching
    profile['medical_conditions'] = [str(c).strip() for c in profile['medical_conditions']]
    profile['allergies'] = [str(a).strip().lower() for a in profile['allergies']]
    
    return profile


def filter_recipes(df_recipes: pd.DataFrame, rules_dict: Dict, patient_profile: Dict) -> pd.DataFrame:
    """
    Step 2: Strict Filtering (The "Retrieval" Part)
    Filters recipes based on Disease Rules and Allergies.
    
    Filtering Logic:
    1. Disease Filter: Exclude recipes with tags in the forbidden list for patient's conditions
    2. Allergy Filter (Dual Check):
       - Check explicit allergens column
       - Check ingredient names for substring matches with allergen names
    
    Args:
        df_recipes: DataFrame with recipe data
        rules_dict: Dictionary mapping diseases to forbidden tags
        patient_profile: Patient information with medical_conditions and allergies
        
    Returns:
        DataFrame with only safe recipes
    """
    print(f"\n[Filtering Recipes] Starting recipe filtering for patient...")
    
    conditions = patient_profile.get('medical_conditions', [])
    allergies = patient_profile.get('allergies', [])
    
    print(f"[Filtering Recipes] Patient conditions: {conditions}")
    print(f"[Filtering Recipes] Patient allergies: {allergies}")

    # 1. Identify Prohibited Tags based on Diseases
    prohibited_tags = set()
    for condition in conditions:
        # Simple substring match for condition mapping
        for rule_cond, tags in rules_dict.items():
            if condition.lower() in rule_cond.lower() or rule_cond.lower() in condition.lower():
                print(f"[Filtering Recipes] Matched condition '{condition}' to rule '{rule_cond}'")
                print(f"[Filtering Recipes] Adding forbidden tags: {tags}")
                prohibited_tags.update(tags)

    print(f"[Filtering Recipes] Total prohibited tags: {prohibited_tags}")

    def is_safe(row):
        """
        Check if a recipe is safe for the patient.
        
        Returns False (unsafe) if:
        - Recipe has a tag in the prohibited list
        - Recipe explicitly lists an allergen the patient has
        - Any ingredient contains the allergen name
        """
        recipe_id = row['recipe_id']
        recipe_name = row['meal_name']
        
        # Check Disease Constraints
        for tag in row['tags_list']:
            if tag in prohibited_tags:
                return False
        
        # Check Allergy Constraints (Dual Check)
        # A. Check explicit allergens column
        for allergen in row['allergens_list']:
            for patient_allergy in allergies:
                if patient_allergy in allergen or allergen in patient_allergy:
                    return False
        
        # B. Check ingredient names for substring matches
        for ingredient in row['parsed_ingredients']:
            ing_name = ingredient['name'].lower()
            for allergy in allergies:
                if allergy in ing_name or ing_name in allergy:
                    return False
        
        return True

    # Apply filter
    safe_recipes = df_recipes[df_recipes.apply(is_safe, axis=1)].copy()
    print(f"[Filtering Recipes] Filtered down to {len(safe_recipes)} safe recipes from {len(df_recipes)} total")
    
    return safe_recipes

def generate_prompt(safe_recipes: pd.DataFrame, patient_profile: Dict) -> str:
    """
    Step 3: LLM Prompt Construction
    Constructs a detailed prompt for the LLM to create a 7-day meal plan.
    
    The prompt includes:
    - Patient profile (conditions, allergies, calorie target)
    - Available safe recipes (filtered, lightweight format)
    - Clear instructions for output format (JSON)
    
    Args:
        safe_recipes: DataFrame with pre-filtered safe recipes
        patient_profile: Normalized patient information
        
    Returns:
        Prompt string for LLM
    """
    print(f"\n[Generating Prompt] Creating LLM prompt with {len(safe_recipes)} safe recipes")
    
    # Create a lightweight context list to save tokens
    recipe_context = []
    for _, row in safe_recipes.iterrows():
        recipe_context.append({
            "recipe_id": row['recipe_id'],
            "meal_name": row['meal_name'],
            "meal_type": row['meal_type'],
            "calories_per_serving": int(row['calories_per_serving']),
            "protein_g": float(row['protein_g']),
            "carbs_g": float(row['carbs_g']),
            "tags": row['tags']
        })

    prompt = f"""You are an expert Convalescent Home Nutrition Planner with deep knowledge of medical dietary requirements.

PATIENT PROFILE:
- Age: {patient_profile.get('age', 'Unknown')}
- Gender: {patient_profile.get('gender', 'Unknown')}
- Medical Conditions: {', '.join(patient_profile.get('medical_conditions', ['None']))}
- Allergies: {', '.join(patient_profile.get('allergies', ['None']))}
- Daily Calorie Target: {patient_profile.get('daily_calorie_target')} calories

IMPORTANT: These recipes have been pre-filtered to be SAFE for the patient's conditions and allergies. 
You MUST ONLY select from the recipes listed below. Do NOT suggest any other recipes.

AVAILABLE SAFE RECIPES (Already filtered for safety):
{json.dumps(recipe_context, indent=2)}

TASK:
Create a complete 7-day meal plan (Day 1 through Day 7) for this patient.

Requirements for each day:
- 1 Breakfast recipe
- 1 Lunch recipe  
- 1 Dinner recipe
- 1 Snack recipe

Calorie Target: The total daily calories should be approximately {patient_profile.get('daily_calorie_target')} (±10%).

Selection Rules:
1. ONLY use recipe_ids from the list above
2. Vary recipes across days for dietary diversity
3. Ensure each recipe is safe (already pre-filtered, but verify tags align with patient conditions)
4. Distribute calories evenly across the 7 days
5. Aim for nutritional balance

OUTPUT FORMAT:
Return ONLY a valid JSON array with NO markdown formatting (no ```json markers).
Each day object must have this structure:
{{
  "day": 1,
  "meals": [
    {{"type": "Breakfast", "recipe_id": "r_XXX", "meal_name": "Recipe Name", "calories": 280}},
    {{"type": "Lunch", "recipe_id": "r_XXX", "meal_name": "Recipe Name", "calories": 450}},
    {{"type": "Dinner", "recipe_id": "r_XXX", "meal_name": "Recipe Name", "calories": 520}},
    {{"type": "Snack", "recipe_id": "r_XXX", "meal_name": "Recipe Name", "calories": 250}}
  ],
  "daily_total_calories": 1500
}}

Return the array starting with day 1 through day 7. Example partial output:
[
  {{"day": 1, "meals": [...], "daily_total_calories": 1500}},
  {{"day": 2, "meals": [...], "daily_total_calories": 1550}},
  ...
]
"""
    return prompt


def get_meal_plan_from_llm(prompt: str) -> List[Dict]:
    """
    Calls Gemini API to generate a meal plan.
    
    Args:
        prompt: LLM prompt with patient and recipe information
        
    Returns:
        List of day objects with meal selections, or empty list on error
    """
    try:
        print(f"\n[LLM API] Calling Gemini API...")
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,  # Low temperature for consistency
                response_mime_type="application/json"
            )
        )
        
        text = response.text.strip()
        plan = json.loads(text)
        print(f"[LLM API] Successfully generated meal plan for {len(plan)} days")
        return plan
    except json.JSONDecodeError as e:
        print(f"[LLM API] ERROR: Invalid JSON response from LLM: {e}")
        print(f"[LLM API] Response text: {text[:500]}...")  # First 500 chars
        return []
    except Exception as e:
        print(f"[LLM API] ERROR: {e}")
        return []

def calculate_procurement(meal_plan: List[Dict], df_recipes: pd.DataFrame) -> Dict[str, float]:
    """
    Step 4: Deterministic Calculation (Procurement Aggregation)
    
    This function is deterministic and does NOT rely on LLM.
    It aggregates ingredient quantities from the recipes selected by the LLM.
    
    Args:
        meal_plan: List of day objects with meal selections (from LLM)
        df_recipes: DataFrame with recipe data and parsed ingredients
        
    Returns:
        Dictionary mapping ingredient names with units to total quantities
        Format: {"Chicken (kg)": 1.5, "Rice (kg)": 0.7, "Milk (L)": 1.2}
    """
    print(f"\n[Calculating Procurement] Starting ingredient aggregation...")
    
    shopping_list = {}  # Key: "Name (unit)", Value: Total Quantity

    # Map recipe ID to recipe data for fast lookup
    recipe_lookup = df_recipes.set_index('recipe_id')

    # Process each day and meal in the meal plan
    total_recipes_processed = 0
    for day_plan in meal_plan:
        day_num = day_plan.get('day', '?')
        for meal in day_plan.get('meals', []):
            recipe_id = meal.get('recipe_id')
            meal_type = meal.get('type', 'Unknown')
            
            if recipe_id in recipe_lookup.index:
                recipe_row = recipe_lookup.loc[recipe_id]
                ingredients = recipe_row['parsed_ingredients']
                
                # Aggregate each ingredient
                for ingredient in ingredients:
                    ing_name = ingredient['name']
                    ing_quantity = ingredient['quantity']
                    ing_unit = ingredient['unit']
                    
                    # Create composite key: "Name (unit)"
                    key = f"{ing_name} ({ing_unit})"
                    
                    if key in shopping_list:
                        shopping_list[key] += ing_quantity
                    else:
                        shopping_list[key] = ing_quantity
                
                total_recipes_processed += 1
            else:
                print(f"[Calculating Procurement] WARNING: Recipe '{recipe_id}' not found in database (Day {day_num}, {meal_type})")
    
    # Format and sort output
    formatted_list = {}
    for key, qty in sorted(shopping_list.items()):
        # Round to 3 decimal places for reasonable precision
        formatted_list[key] = round(qty, 3)
    
    print(f"[Calculating Procurement] Processed {total_recipes_processed} recipe selections")
    print(f"[Calculating Procurement] Aggregated into {len(formatted_list)} unique ingredients")
    
    return formatted_list


def normalize_ingredient_names(shopping_list: Dict[str, float]) -> Dict[str, float]:
    """
    Merge similar ingredient names and reformat shopping list.
    Converts "Ingredient (unit)" to "Ingredient : qty unit" format.
    Merges variations like "eggs"/"egg" into single entry.
    
    Args:
        shopping_list: Dictionary with format "Name (unit): quantity"
        
    Returns:
        Merged and reformatted dictionary with format "Name : quantity unit"
    """
    merged = {}
    
    for key, qty in shopping_list.items():
        # Parse "Name (unit)" format
        if '(' in key and ')' in key:
            name = key[:key.rfind('(')].strip()
            unit = key[key.rfind('(')+1:key.rfind(')')].strip()
        else:
            name = key
            unit = ''
        
        # Normalize ingredient name (lowercase, singular form)
        normalized_name = name.lower().strip()
        # Convert plural to singular for merging
        if normalized_name.endswith('es'):
            normalized_name_singular = normalized_name[:-2]
        elif normalized_name.endswith('s') and not normalized_name.endswith('ss'):
            normalized_name_singular = normalized_name[:-1]
        else:
            normalized_name_singular = normalized_name
        
        # Create new key in reformatted style: "Name : qty unit"
        new_key = f"{name} : {unit}" if unit else f"{name}"
        
        # Merge with existing entry if it exists (same ingredient, same unit)
        found = False
        for existing_key in list(merged.keys()):
            existing_name = existing_key.split(' : ')[0].lower().strip()
            existing_unit = existing_key.split(' : ')[1] if ' : ' in existing_key else ''
            
            # Check if names match (considering singular/plural)
            if existing_name.endswith('es'):
                existing_singular = existing_name[:-2]
            elif existing_name.endswith('s') and not existing_name.endswith('ss'):
                existing_singular = existing_name[:-1]
            else:
                existing_singular = existing_name
            
            # Merge if same ingredient and unit
            if (existing_singular == normalized_name_singular or existing_name == normalized_name) and existing_unit == unit:
                merged[existing_key] += qty
                found = True
                break
        
        if not found:
            merged[new_key] = qty
    
    return merged


def generate_meal_plan_summary(meal_plan: List[Dict], shopping_list: Dict[str, float], df_recipes: pd.DataFrame) -> str:
    """
    Generate formatted summary of 7-day meal plan and complete shopping list.
    Uses accurate data from CSV instead of LLM estimates.
    
    Args:
        meal_plan: List of day objects with meals
        shopping_list: Dictionary of ingredients
        df_recipes: Recipe database for accurate data lookup
        
    Returns:
        Formatted summary string
    """
    summary = "\n" + "=" * 100 + "\n"
    summary += "DETAILED 7-DAY MEAL PLAN\n"
    summary += "=" * 100 + "\n"
    
    # Create recipe lookup for accurate data
    recipe_lookup = df_recipes.set_index('recipe_id')
    
    for day_plan in meal_plan:
        day_num = day_plan.get('day')
        daily_total = day_plan.get('daily_total_calories', 0)
        
        summary += f"\n📅 DAY {day_num} (Total: {daily_total:.0f} calories)\n"
        summary += "-" * 100 + "\n"
        
        for meal in day_plan.get('meals', []):
            meal_type = meal.get('type')
            recipe_id = meal.get('recipe_id')
            meal_name = meal.get('meal_name')
            
            # Get accurate data from CSV
            if recipe_id in recipe_lookup.index:
                recipe_row = recipe_lookup.loc[recipe_id]
                calories = float(recipe_row['calories_per_serving'])
                protein = float(recipe_row['protein_g'])
                carbs = float(recipe_row['carbs_g'])
                fat = float(recipe_row['fat_g'])
                meal_name = str(recipe_row['meal_name'])
            else:
                calories = meal.get('calories', 0)
                protein = meal.get('protein_g', 0)
                carbs = meal.get('carbs_g', 0)
                fat = meal.get('fat_g', 0)
            
            summary += f"  ✓ {meal_type:10} : {meal_name:45} ({calories:.0f} cal, P:{protein:.0f}g C:{carbs:.0f}g F:{fat:.0f}g) [{recipe_id}]\n"
    
    summary += "\n" + "=" * 100 + "\n"
    summary += "COMPLETE WEEKLY SHOPPING LIST\n"
    summary += "=" * 100 + "\n"
    
    # Normalize and sort ingredients
    normalized_shopping = normalize_ingredient_names(shopping_list)
    sorted_items = sorted(normalized_shopping.items(), key=lambda x: x[1], reverse=True)
    
    summary += f"\nTotal Ingredients: {len(sorted_items)}\n\n"
    
    for item, qty in sorted_items:
        # Parse to get unit for formatting
        if ' : ' in item:
            name, unit = item.rsplit(' : ', 1)
            summary += f"  - {name:40} : {qty:8.3f} {unit}\n"
        else:
            summary += f"  - {item:40} : {qty:8.3f}\n"
    
    return summary


def generate_meal_plan_output(meal_plan: List[Dict], shopping_list: Dict, 
                              patient_profile: Dict, df_recipes: pd.DataFrame) -> Dict[str, Any]:
    """
    Generates a comprehensive output combining meal plan and procurement data.
    
    Args:
        meal_plan: List of day objects with meal selections
        shopping_list: Dictionary of aggregated ingredients
        patient_profile: Patient information
        df_recipes: Recipe database (for meal name lookup)
        
    Returns:
        Comprehensive output dictionary with meal plan, shopping list, and metadata
    """
    # Create recipe lookup for meal details
    recipe_lookup = df_recipes.set_index('recipe_id')
    
    # Enrich meal plan with recipe details
    enriched_meal_plan = []
    total_calories_7days = 0
    
    for day_plan in meal_plan:
        day_num = day_plan.get('day')
        day_meals = []
        day_calories = 0
        
        for meal in day_plan.get('meals', []):
            recipe_id = meal.get('recipe_id')
            meal_type = meal.get('type')
            
            meal_info = {
                'type': meal_type,
                'recipe_id': recipe_id,
                'meal_name': meal.get('meal_name', 'Unknown'),
                'calories': 0  # Will be filled from CSV data
            }
            
            # Get accurate data from CSV
            if recipe_id in recipe_lookup.index:
                recipe_row = recipe_lookup.loc[recipe_id]
                # Use accurate calories from CSV, not from LLM
                meal_info['calories'] = float(recipe_row['calories_per_serving'])
                meal_info['meal_name'] = str(recipe_row['meal_name'])
                meal_info['protein_g'] = float(recipe_row['protein_g'])
                meal_info['carbs_g'] = float(recipe_row['carbs_g'])
                meal_info['fat_g'] = float(recipe_row['fat_g'])
            
            day_meals.append(meal_info)
            day_calories += meal_info['calories']
        
        enriched_meal_plan.append({
            'day': day_num,
            'meals': day_meals,
            'daily_total_calories': day_calories  # Use calculated total from CSV data
        })
        total_calories_7days += day_calories
    
    # Build comprehensive output
    output = {
        'patient_info': {
            'age': patient_profile.get('age'),
            'gender': patient_profile.get('gender'),
            'medical_conditions': patient_profile.get('medical_conditions'),
            'allergies': patient_profile.get('allergies'),
            'daily_calorie_target': patient_profile.get('daily_calorie_target')
        },
        'meal_plan': {
            'plan_duration_days': len(enriched_meal_plan),
            'days': enriched_meal_plan,
            'total_calories_7_days': total_calories_7days,
            'average_daily_calories': round(total_calories_7days / 7, 1) if enriched_meal_plan else 0
        },
        'weekly_procurement': {
            'shopping_list': shopping_list,
            'total_ingredients': len(shopping_list),
            'aggregation_note': 'Ingredients aggregated deterministically from selected recipes'
        },
        'metadata': {
            'generation_timestamp': pd.Timestamp.now().isoformat(),
            'system': 'Convalescent Home Nutrition Planner - RAG System'
        }
    }
    
    return output


def main():
    """
    Main entry point for the RAG Nutrition Planning System.
    
    This function orchestrates the complete pipeline:
    1. Load and parse data (recipes and disease rules)
    2. Load patient profile
    3. Filter recipes based on patient safety constraints
    4. Generate LLM prompt
    5. Get meal plan from LLM
    6. Calculate procurement/shopping list
    7. Output comprehensive JSON result
    """
    print("=" * 80)
    print("CONVALESCENT HOME NUTRITION PLANNER - RAG SYSTEM")
    print("=" * 80)
    
    # Configuration
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    RECIPES_CSV = data_dir / "Recipes_with_Ingredients.csv"
    RULES_CSV = data_dir / "Disease_rules.csv"
    PATIENT_PROFILE_1 = data_dir / "patient_profile1.json"
    PATIENT_PROFILE_2 = data_dir / "patient_profile2.json"
    
    # Verify files exist
    required_files = [RECIPES_CSV, RULES_CSV]
    missing_required = [f for f in required_files if not f.exists()]
    if missing_required:
        for missing in missing_required:
            print(f"ERROR: Missing required data file: {missing}")
        return
    
    optional_profiles = [PATIENT_PROFILE_1, PATIENT_PROFILE_2]
    for profile in optional_profiles:
        if not profile.exists():
            print(f"Warning: Optional patient profile not found: {profile}")
    
    print(f"\n✓ Data directory: {data_dir}\n")
    
    # ============ STEP 1: Load and Parse Data ============
    df_recipes, rules_dict = load_data(str(RECIPES_CSV), str(RULES_CSV))
    
    # ============ TEST WITH BOTH PATIENTS ============
    test_patients = [
        ("Patient 1 (Heart Disease + Diabetes + Lactose Intolerant)", str(PATIENT_PROFILE_1)),
        ("Patient 2 (Vegan)", str(PATIENT_PROFILE_2))
    ]
    
    all_results = {}
    
    for patient_name, patient_json_path in test_patients:
        print(f"\n" + "=" * 80)
        print(f"PROCESSING: {patient_name}")
        print("=" * 80)
        
        # Load patient profile
        print(f"\n[Loading Patient] Reading {patient_json_path}")
        with open(patient_json_path, 'r') as f:
            patient_raw = json.load(f)
        
        # Normalize patient profile
        patient_profile = normalize_patient_profile(patient_raw)
        print(f"[Loading Patient] Patient normalized: {patient_profile['gender']}, "
              f"Age {patient_profile['age']}, "
              f"Conditions: {patient_profile['medical_conditions']}")
        
        # ============ STEP 2: Filter Recipes ============
        safe_recipes = filter_recipes(df_recipes, rules_dict, patient_profile)
        
        if len(safe_recipes) < 5:
            print(f"\n⚠️  WARNING: Only {len(safe_recipes)} safe recipes found. "
                  "LLM may struggle to create diverse meal plan.")
        else:
            print(f"✓ Successfully filtered to {len(safe_recipes)} safe recipes")
        
        # ============ STEP 3: Generate LLM Prompt ============
        prompt = generate_prompt(safe_recipes, patient_profile)
        
        # ============ STEP 4: Get Meal Plan from LLM ============
        meal_plan = get_meal_plan_from_llm(prompt)
        
        if not meal_plan:
            print(f"\n❌ ERROR: Failed to generate meal plan from LLM. Skipping procurement calculation.")
            continue
        
        print(f"✓ Successfully generated meal plan")
        
        # ============ STEP 5: Calculate Procurement ============
        shopping_list = calculate_procurement(meal_plan, df_recipes)
        
        print(f"✓ Successfully calculated shopping list")
        
        # ============ STEP 6: Generate Comprehensive Output ============
        output = generate_meal_plan_output(meal_plan, shopping_list, patient_profile, df_recipes)
        
        all_results[patient_name] = output
        
        # ============ STEP 7: Output JSON ============
        print(f"\n[Output] Generating JSON output...")
        output_filename = f"{WORKSPACE_PATH}/meal_plan_{patient_name.replace(' ', '_').replace('(', '').replace(')', '')}.json"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Output saved to: {output_filename}")
        
        # Print detailed summary with 7-day meal plan and complete shopping list
        summary_text = generate_meal_plan_summary(meal_plan, output['weekly_procurement']['shopping_list'], df_recipes)
        print(summary_text)
        
        # Print summary statistics
        print(f"[Summary Statistics for {patient_name}]")
        print(f"  Total Days: {output['meal_plan']['plan_duration_days']}")
        print(f"  Total Calories (7 days): {output['meal_plan']['total_calories_7_days']:.0f}")
        print(f"  Average Daily Calories: {output['meal_plan']['average_daily_calories']:.0f}")
        print(f"  Target Daily Calories: {patient_profile['daily_calorie_target']}")
        print(f"  Total Unique Ingredients: {output['weekly_procurement']['total_ingredients']}")
        print(f"  Safe Recipes Available: {len(safe_recipes)}")
    
    # ============ FINAL COMPREHENSIVE OUTPUT ============
    print(f"\n" + "=" * 80)
    print("COMPREHENSIVE RESULTS")
    print("=" * 80)
    
    comprehensive_output = {
        'system': 'Convalescent Home Nutrition Planner - RAG System',
        'description': 'Multi-patient RAG system with filtering, LLM planning, and deterministic procurement',
        'patients_processed': len(all_results),
        'results': all_results,
        'metadata': {
            'generation_timestamp': pd.Timestamp.now().isoformat(),
            'recipes_total': len(df_recipes),
            'recipes_have_allergen_info': len(df_recipes[df_recipes['allergens'].notna()]),
            'disease_rules_total': len(rules_dict)
        }
    }
    
    # Save comprehensive results
    comprehensive_filename = os.path.join(WORKSPACE_PATH, "comprehensive_nutrition_plan.json")
    with open(comprehensive_filename, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Comprehensive results saved to: {comprehensive_filename}")
    print(f"\n✓ RAG System completed successfully!")
    print(f"  - Processed {len(all_results)} patients")
    print(f"  - Generated {len(all_results)} individual meal plans")
    print(f"  - Created shopping lists for {len(all_results)} patients")
    
    return comprehensive_output


if __name__ == "__main__":
    try:
        result = main()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)