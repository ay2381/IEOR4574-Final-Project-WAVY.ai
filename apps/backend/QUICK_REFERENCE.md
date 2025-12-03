# Quick Reference Card

## Essential Commands

### First Time Setup
```bash
cd wavy-backend
cp .env.example .env
# Edit .env and add OPENAI_API_KEY=your_key_here
./run.sh              # Linux/Mac
run.bat               # Windows
```

### Daily Development
```bash
# Start server
./run.sh              # or: python -m uvicorn main:app --reload

# Run tests
pytest tests/ -v

# Check API docs
open http://localhost:8080/docs

# Format code
make format           # or: black src/ tests/

# Clean up
make clean
```

### Docker Commands
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild
docker-compose up --build
```

## API Endpoints Quick Reference

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| GET | `/health` | - | Health status |
| GET | `/api/patients` | - | Patient[] |
| POST | `/api/patients` | CreatePatient | Patient |
| DELETE | `/api/patients/{id}` | - | 204 |
| GET | `/api/plans` | - | Plan[] |
| POST | `/api/plans/generate` | GeneratePlan | Plan[] |
| POST | `/api/llm/procurement-insights` | Insights | Analysis |

## Quick Test Examples

### Create Patient
```bash
curl -X POST http://localhost:8080/api/patients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "age": 30,
    "gender": "male",
    "medicalConditions": [],
    "allergies": [],
    "dietaryRestrictions": [],
    "calorieTarget": 2000,
    "macroTargets": {"protein": 150, "carbs": 200, "fat": 65}
  }'
```

### Generate Plan (Rule-Based)
```bash
curl -X POST http://localhost:8080/api/plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "patientIds": ["<patient-id>"],
    "strategy": "rule_based"
  }'
```

### Generate Plan (LLM)
```bash
curl -X POST http://localhost:8080/api/plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "patientIds": ["<patient-id>"],
    "strategy": "llm"
  }'
```

### Get Insights
```bash
curl -X POST http://localhost:8080/api/llm/procurement-insights \
  -H "Content-Type: application/json" \
  -d '{
    "planIds": ["<plan-id-1>", "<plan-id-2>"]
  }'
```

## Environment Variables Quick Reference

### Required
```bash
OPENAI_API_KEY=sk-...
```

### Recommended
```bash
DATABASE_URL=postgresql://user:pass@localhost/db
ALLOWED_ORIGINS=http://localhost:5173
DEBUG=False
```

### Optional
```bash
LLM_PROVIDER=openai
MAX_TOKENS=2000
TEMPERATURE=0.7
REDIS_URL=redis://localhost:6379
```

## File Locations

| What | Where |
|------|-------|
| API Routes | `src/api/*.py` |
| Data Models | `src/domain/*.py` |
| Business Logic | `src/services/*.py` |
| LLM Code | `src/llm/*.py` |
| Database | `src/db/*.py` |
| Config | `src/config.py` |
| Tests | `tests/*.py` |
| Docs | `*.md` |

## Troubleshooting Quick Fixes

### "Module not found"
```bash
# Ensure you're in project root
cd wavy-backend
# Activate venv
source venv/bin/activate
# Reinstall
pip install -r requirements.txt
```

### "Database error"
```bash
# Delete and recreate
rm *.db
# Restart server
./run.sh
```

### "OpenAI API error"
```bash
# Check .env
cat .env | grep OPENAI
# Should show: OPENAI_API_KEY=sk-...
```

### "Port already in use"
```bash
# Change port in .env
echo "PORT=8000" >> .env
# Or kill process
lsof -ti:8080 | xargs kill -9  # Mac/Linux
```

### "CORS error"
```bash
# Add frontend URL to .env
echo "ALLOWED_ORIGINS=http://localhost:5173" >> .env
# Restart server
```

## Useful URLs

| Service | URL |
|---------|-----|
| API | http://localhost:8080 |
| Docs | http://localhost:8080/docs |
| ReDoc | http://localhost:8080/redoc |
| Health | http://localhost:8080/health |

## Performance Tips

- Use `rule_based` strategy for speed (50ms)
- Use `llm` strategy for quality (2-5s)
- Enable Redis for caching
- Add database indexes for scale
- Monitor with `/health` endpoint

## Deployment Quick Start

### Railway
```bash
railway login
railway init
railway add --plugin postgresql
railway variables set OPENAI_API_KEY=your_key
railway up
```

### Render
1. Connect GitHub repo
2. Add PostgreSQL database
3. Set environment variables
4. Deploy

### Docker
```bash
docker build -t wavy-backend .
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_key \
  wavy-backend
```

## Cost Quick Reference

| Users | Infrastructure | LLM Costs | Total/Month |
|-------|---------------|-----------|-------------|
| <100 | $10 | $0-5 | $10-15 |
| 100-1K | $20 | $5-20 | $25-40 |
| 1K-10K | $50 | $20-100 | $70-150 |

## Getting Help

1. Check docs: `*.md` files
2. View API docs: http://localhost:8080/docs
3. Check logs: console output
4. Review tests: `tests/test_api.py`

## Common Patterns

### Add New Endpoint
1. Create route in `src/api/`
2. Add service logic in `src/services/`
3. Update models in `src/domain/`
4. Add test in `tests/`

### Add New Meal Strategy
1. Create service in `src/services/`
2. Update `plan_service.py`
3. Add strategy type to domain models

### Change Database
```bash
# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:pass@host/db
# Restart
./run.sh
```

---

**Keep this card handy for quick reference!** 📋

For detailed information, see:
- README.md (technical docs)
- QUICKSTART.md (getting started)
- DEPLOYMENT.md (deployment guides)
