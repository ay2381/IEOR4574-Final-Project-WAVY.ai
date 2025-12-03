"""
CLI utility to import recipe data from Recipes_with_Ingredients.csv into the database.

Usage:
    python scripts/import_recipes.py --csv ../../data/Recipes_with_Ingredients.csv --truncate
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import List, Dict

BACKEND_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = WORKSPACE_ROOT / "data"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import Base, SessionLocal, engine  # noqa: E402
from models import RecipeModel, RecipeIngredientModel  # noqa: E402


def parse_float(value: str | None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def split_semicolon_list(value: str | None) -> List[str]:
    if not value:
        return []
    cleaned = value.strip()
    if not cleaned or cleaned.lower() == "none":
        return []
    return [item.strip() for item in cleaned.split(";") if item.strip()]


INGREDIENT_PATTERN = re.compile(r"^\s*([^:]+):\s*([\d.]+)\s*([a-zA-Z]+)")


def parse_ingredient_string(raw: str | None) -> List[Dict[str, str]]:
    if not raw:
        return []
    ingredients: List[Dict[str, str]] = []
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        match = INGREDIENT_PATTERN.search(part)
        if not match:
            continue
        name, qty, unit = match.groups()
        ingredients.append(
            {
                "name": name.strip(),
                "quantity": float(qty),
                "unit": unit.strip(),
                "raw": part,
            }
        )
    return ingredients


def ensure_tables():
    Base.metadata.create_all(bind=engine)


def import_csv(csv_path: Path, truncate: bool = False):
    ensure_tables()
    session = SessionLocal()
    added = 0
    updated = 0
    try:
        if truncate:
            session.query(RecipeIngredientModel).delete()
            session.query(RecipeModel).delete()
            session.commit()
            print("Cleared existing recipe data.")

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                external_id = row.get("recipe_id")
                if not external_id:
                    continue
                recipe = (
                    session.query(RecipeModel)
                    .filter(RecipeModel.external_id == external_id)
                    .one_or_none()
                )
                tags = split_semicolon_list(row.get("tags"))
                allergens = split_semicolon_list(row.get("allergens"))
                ingredients = parse_ingredient_string(row.get("ingredient_proportion"))

                if not recipe:
                    recipe = RecipeModel(
                        external_id=external_id,
                        meal_name=row.get("meal_name", "").strip() or "Unnamed Recipe",
                        meal_type=row.get("meal_type", "").strip() or None,
                        calories_per_serving=parse_float(row.get("calories_per_serving")),
                        protein_g=parse_float(row.get("protein_g")),
                        fat_g=parse_float(row.get("fat_g")),
                        carbs_g=parse_float(row.get("carbs_g")),
                        tags=tags,
                        allergens=allergens,
                        ingredient_text=row.get("ingredient_proportion", ""),
                    )
                    session.add(recipe)
                    added += 1
                else:
                    recipe.meal_name = row.get("meal_name", recipe.meal_name)
                    recipe.meal_type = row.get("meal_type") or recipe.meal_type
                    recipe.calories_per_serving = parse_float(
                        row.get("calories_per_serving")
                    )
                    recipe.protein_g = parse_float(row.get("protein_g"))
                    recipe.fat_g = parse_float(row.get("fat_g"))
                    recipe.carbs_g = parse_float(row.get("carbs_g"))
                    recipe.tags = tags
                    recipe.allergens = allergens
                    recipe.ingredient_text = row.get("ingredient_proportion", "")
                    recipe.ingredients.clear()
                    updated += 1

                for ingredient in ingredients:
                    recipe.ingredients.append(
                        RecipeIngredientModel(
                            name=ingredient["name"],
                            quantity=ingredient.get("quantity"),
                            unit=ingredient.get("unit"),
                            raw=ingredient.get("raw"),
                        )
                    )

        session.commit()
        print(
            f"Import complete. Added {added} recipe(s), updated {updated} existing recipe(s)."
        )
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Import recipes into the database.")
    parser.add_argument(
        "--csv",
        type=str,
        default=str(DATA_DIR / "Recipes_with_Ingredients.csv"),
        help="Path to Recipes_with_Ingredients.csv",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Remove existing recipes before importing",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)

    os.environ.setdefault("PYTHONWARNINGS", "ignore")
    import_csv(csv_path, truncate=args.truncate)


if __name__ == "__main__":
    main()

