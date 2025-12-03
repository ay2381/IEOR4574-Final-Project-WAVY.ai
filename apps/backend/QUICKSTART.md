# Quick Start Guide

## Getting Started in 5 Minutes

### Prerequisites
- Python 3.11+ installed
- OpenAI API key (get one at https://platform.openai.com/api-keys)

### Steps

#### Option 1: Automated Setup (Recommended)

**Linux/Mac:**
```bash
./run.sh
```

**Windows:**
```bash
run.bat
```

On first run, the script will:
1. Create a `.env` file from `.env.example`
2. Ask you to add your OpenAI API key
3. Create a virtual environment
4. Install dependencies
5. Start the server

#### Option 2: Manual Setup

1. **Install dependencies:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. **Run the server:**
```bash
python -m uvicorn main:app --reload --port 8080
```

### Access the API

- **API Base:** http://localhost:8080
- **Swagger Docs:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc

### Test It Out

1. Open http://localhost:8080/docs
2. Try the "GET /health" endpoint
3. Create a patient using "POST /api/patients"
4. Generate a meal plan using "POST /api/plans/generate"

### Example API Calls

**Create a Patient:**
```bash
curl -X POST http://localhost:8080/api/patients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "age": 35,
    "gender": "female",
    "medicalConditions": ["diabetes"],
    "allergies": ["peanuts"],
    "dietaryRestrictions": [],
    "calorieTarget": 1800,
    "macroTargets": {"protein": 120, "carbs": 180, "fat": 60}
  }'
```

**Generate Meal Plan (Rule-Based):**
```bash
curl -X POST http://localhost:8080/api/plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "patientIds": ["<patient-id-from-above>"],
    "strategy": "rule_based"
  }'
```

**Generate Meal Plan (AI-Powered):**
```bash
curl -X POST http://localhost:8080/api/plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "patientIds": ["<patient-id-from-above>"],
    "strategy": "llm"
  }'
```

## Connect to Frontend

Update your frontend's `.env.local`:
```
VITE_API_BASE_URL=http://localhost:8080/api
```

## Using Docker

```bash
# Start all services (backend, database, redis)
docker-compose up

# Stop services
docker-compose down
```

## Troubleshooting

**Problem: OpenAI API errors**
- Solution: Verify your OPENAI_API_KEY in `.env` is correct

**Problem: Database errors**
- Solution: Delete `wavy_nutrition.db` and restart (SQLite will recreate it)

**Problem: Port 8080 already in use**
- Solution: Change PORT in `.env` to another port (e.g., 8000)

**Problem: Import errors**
- Solution: Make sure you're running from the project root directory

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API using Swagger UI at http://localhost:8080/docs
- Check out the [tests](tests/) for usage examples
- Review the [domain models](src/domain/) to understand data structures

## Support

Need help? Check:
- Full README: [README.md](README.md)
- API Documentation: http://localhost:8080/docs
- Test Examples: [tests/test_api.py](tests/test_api.py)
