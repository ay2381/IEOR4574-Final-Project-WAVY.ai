.PHONY: help install run test clean docker-build docker-up docker-down lint format recipes-import recipes-count recipes-ingredients rules-import

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean up generated files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"

install:
	python -m venv venv || true
	. venv/bin/activate && pip install -r requirements.txt

run:
	python -m uvicorn main:app --reload --port 8080

test:
	pytest tests/ -v --cov=src

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov 2>/dev/null || true
	rm -f *.db 2>/dev/null || true

docker-build:
	docker build -t wavy-backend .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f backend

lint:
	flake8 src/ --max-line-length=120 --ignore=E203,W503
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/
	isort src/ tests/

VENV ?= ./venv
PYTHON := $(VENV)/bin/python

DATA_DIR ?= ../../data

recipes-import:
	$(PYTHON) scripts/import_recipes.py --csv $(DATA_DIR)/Recipes_with_Ingredients.csv --truncate

recipes-count:
	sqlite3 wavy.db "SELECT COUNT(*) FROM recipes;"

recipes-ingredients:
	sqlite3 wavy.db "SELECT meal_name, COUNT(*) FROM recipe_ingredients GROUP BY meal_name LIMIT 10;"

rules-import:
	$(PYTHON) scripts/import_disease_rules.py --csv $(DATA_DIR)/Disease_rules.csv