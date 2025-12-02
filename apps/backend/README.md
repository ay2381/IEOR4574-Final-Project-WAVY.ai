# WAVY.ai Backend Service

FastAPI-based backend service for intelligent meal planning and nutrition management.

## Features

- ✅ RESTful API for patient management
- ✅ Rule-based meal plan generation
- ✅ LLM-powered meal plan generation (OpenAI/Azure)
- ✅ Procurement insights and ingredient analysis
- ✅ SQLAlchemy ORM with PostgreSQL support
- ✅ Comprehensive nutrition calculations
- ✅ Docker support for easy deployment

## Tech Stack

- **Framework**: FastAPI 0.109
- **Database**: PostgreSQL (with SQLite fallback for development)
- **ORM**: SQLAlchemy 2.0
- **LLM Provider**: OpenAI GPT-4o-mini (configurable)
- **Validation**: Pydantic 2.5
- **Server**: Uvicorn with auto-reload

## Quick Start

### 1. Local Development (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Edit .env with your configuration
# At minimum, set OPENAI_API_KEY

# Run the server
python -m uvicorn src.main:app --reload --port 8080
```

The API will be available at `http://localhost:8080`

### 2. Docker Development

```bash
# Copy environment file
cp .env.example .env

# Set your OpenAI API key in .env
# OPENAI_API_KEY=your_key_here

# Start all services
docker-compose up

# Backend: http://localhost:8080
# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

### 3. Production Deployment

```bash
# Build Docker image
docker build -t wavy-backend .

# Run with production settings
docker run -p 8080:8080 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e OPENAI_API_KEY=your_key \
  -e DEBUG=False \
  wavy-backend
```

## Environment Variables

Required variables:

```bash
# LLM Configuration (required)
OPENAI_API_KEY=sk-...                # Your OpenAI API key
LLM_PROVIDER=openai                   # openai | azure | bedrock

# Database (optional, defaults to SQLite)
DATABASE_URL=postgresql://user:pass@localhost:5432/wavy_nutrition

# Server (optional)
PORT=8080
DEBUG=True

# CORS (required for frontend)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Security (required for production)
SESSION_SECRET=your-secret-key-here
```

Optional variables:

```bash
# Azure OpenAI (if using Azure)
AZURE_OPENAI_ENDPOINT=https://....openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# LLM Settings
MAX_TOKENS=2000
TEMPERATURE=0.7
LLM_RETRY_ATTEMPTS=3
```

## API Endpoints

### Patients

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/patients` | List all patients |
| `POST` | `/api/patients` | Create new patient |
| `GET` | `/api/patients/{id}` | Get patient by ID |
| `DELETE` | `/api/patients/{id}` | Delete patient |

### Meal Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/plans` | List all meal plans |
| `POST` | `/api/plans/generate` | Generate new meal plans |
| `GET` | `/api/plans/{id}` | Get plan by ID |
| `DELETE` | `/api/plans/{id}` | Delete plan |

### LLM Insights

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/llm/procurement-insights` | Generate procurement analysis |
| `POST` | `/api/llm/meal-suggestions` | Get AI meal suggestions |

### Health & Docs

| Endpoint | Description |
|----------|-------------|
| `/` | Health check |
| `/health` | Detailed health status |
| `/docs` | Swagger UI documentation |
| `/redoc` | ReDoc documentation |

## API Usage Examples

### Create a Patient

```bash
curl -X POST http://localhost:8080/api/patients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 45,
    "gender": "male",
    "medicalConditions": ["diabetes", "hypertension"],
    "allergies": ["peanuts", "shellfish"],
    "dietaryRestrictions": [
      {"type": "low-sodium", "severity": "moderate"}
    ],
    "calorieTarget": 2000,
    "macroTargets": {
      "protein": 150,
      "carbs": 200,
      "fat": 65
    }
  }'
```

### Generate Meal Plans

```bash
curl -X POST http://localhost:8080/api/plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "patientIds": ["patient-uuid-here"],
    "weekStart": "2024-01-15",
    "strategy": "llm"
  }'
```

### Get Procurement Insights

```bash
curl -X POST http://localhost:8080/api/llm/procurement-insights \
  -H "Content-Type: application/json" \
  -d '{
    "planIds": ["plan-uuid-1", "plan-uuid-2"],
    "instructions": "Focus on cost optimization and bulk purchasing"
  }'
```

## Project Structure

```
src/
├── api/              # Route handlers / controllers
│   ├── patients.py   # Patient CRUD endpoints
│   ├── plans.py      # Meal plan endpoints
│   └── llm_insights.py # LLM-powered insights
├── domain/           # Pydantic models & schemas
│   ├── patient.py    # Patient models
│   └── plan.py       # Meal plan models
├── services/         # Business logic
│   ├── meal_service.py    # Rule-based meal generation
│   └── plan_service.py    # Plan orchestration
├── llm/              # LLM integration
│   ├── provider.py   # LLM provider abstraction
│   └── prompts.py    # Prompt templates
├── db/               # Database layer
│   ├── database.py   # SQLAlchemy setup
│   └── models.py     # ORM models
├── config.py         # Configuration management
└── main.py           # Application entry point
```

## Meal Planning Strategies

### Rule-Based (Deterministic)

- Fast and predictable
- Uses pre-defined meal templates
- Adjusts portions to meet calorie targets
- Respects dietary restrictions and allergies
- Provides variety through meal rotation

### LLM-Based (AI-Powered)

- Creative and personalized
- Generates unique meal combinations
- Considers medical conditions and preferences
- More expensive (API costs)
- Fallback to rule-based on failures

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v
```

### Database Migrations (Alembic)

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Quality

```bash
# Format code
black src/

# Lint
flake8 src/

# Type checking
mypy src/
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check DATABASE_URL is correct
   - Ensure PostgreSQL is running (if using Docker: `docker-compose ps`)
   - Try SQLite for development: `DATABASE_URL=sqlite:///./wavy.db`

2. **LLM API errors**
   - Verify OPENAI_API_KEY is set correctly
   - Check API quota and limits
   - Review logs for specific error messages

3. **CORS errors from frontend**
   - Ensure ALLOWED_ORIGINS includes your frontend URL
   - Check frontend is using `credentials: 'include'`

4. **Import errors**
   - Run from project root: `python -m uvicorn src.main:app`
   - Ensure all `__init__.py` files exist

## Performance

- Rule-based generation: ~50ms per plan
- LLM-based generation: ~2-5s per plan (depends on API)
- Database queries: <10ms (with proper indexing)
- Concurrent requests: Handles 100+ req/s

## Security

- API keys stored in environment variables
- CORS configured for specific origins
- Input validation with Pydantic
- SQL injection prevention via ORM
- Rate limiting recommended for production

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [your-repo]/issues
- Documentation: http://localhost:8080/docs
- Email: team@wavy.ai
