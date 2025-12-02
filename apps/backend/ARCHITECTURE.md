# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         WAVY.ai System                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐                              ┌──────────────────┐
│                  │                              │                  │
│  React Frontend  │◄────── HTTP/REST ──────────►│  FastAPI Backend │
│  (Port 5173)     │         (CORS)              │   (Port 8080)    │
│                  │                              │                  │
└──────────────────┘                              └──────────────────┘
                                                           │
                                                           │
                    ┌──────────────────────────────────────┼────────────────┐
                    │                                      │                │
                    ▼                                      ▼                ▼
           ┌─────────────────┐                   ┌─────────────┐  ┌──────────────┐
           │                 │                   │             │  │              │
           │  PostgreSQL DB  │                   │  OpenAI API │  │ Redis Cache  │
           │  (Patient Data  │                   │  (GPT-4o)   │  │  (Optional)  │
           │   Meal Plans)   │                   │             │  │              │
           │                 │                   │             │  │              │
           └─────────────────┘                   └─────────────┘  └──────────────┘
```

## Backend Internal Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                          FastAPI Application                          │
└───────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                            API Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐           │
│  │  patients.py │  │   plans.py   │  │ llm_insights.py │           │
│  │  (CRUD ops)  │  │  (Generate)  │  │  (AI Analysis)  │           │
│  └──────────────┘  └──────────────┘  └─────────────────┘           │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Domain Layer                                  │
│  ┌──────────────┐                    ┌──────────────┐               │
│  │  patient.py  │                    │   plan.py    │               │
│  │  (Models)    │                    │  (Models)    │               │
│  └──────────────┘                    └──────────────┘               │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Service Layer                                  │
│  ┌────────────────────┐              ┌────────────────────┐         │
│  │  meal_service.py   │              │  plan_service.py   │         │
│  │  (Rule-based Gen)  │◄─────────────┤  (Orchestration)   │         │
│  └────────────────────┘              └────────────────────┘         │
│                                                │                      │
│                                                ▼                      │
│                                      ┌─────────────────┐             │
│                                      │  LLM Provider   │             │
│                                      │  (OpenAI/Azure) │             │
│                                      └─────────────────┘             │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Database Layer                                 │
│  ┌──────────────┐                    ┌──────────────┐               │
│  │ database.py  │                    │  models.py   │               │
│  │ (SQLAlchemy) │                    │ (ORM Models) │               │
│  └──────────────┘                    └──────────────┘               │
└──────────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. Create Patient Flow

```
Client                API Layer           DB Layer            Database
  │                      │                   │                   │
  ├─POST /patients──────►│                   │                   │
  │  {patient_data}      │                   │                   │
  │                      │                   │                   │
  │                      ├─validate────────► │                   │
  │                      │                   │                   │
  │                      │                   ├─INSERT──────────► │
  │                      │                   │                   │
  │                      │                   │◄──ID─────────────┤
  │                      │                   │                   │
  │◄─201 Created─────────┤                   │                   │
  │  {patient_obj}       │                   │                   │
```

### 2. Generate Meal Plan (Rule-Based) Flow

```
Client              API Layer       Service Layer      DB Layer
  │                    │                 │                │
  ├─POST /plans/gen───►│                 │                │
  │  {strategy:rule}   │                 │                │
  │                    │                 │                │
  │                    ├─get_patient────►│                │
  │                    │                 ├─query─────────►│
  │                    │                 │                │
  │                    │◄────patient─────┤                │
  │                    │                 │                │
  │                    ├─generate────────►│                │
  │                    │                 │                │
  │                    │                 ├─apply_rules    │
  │                    │                 ├─calculate      │
  │                    │                 ├─build_plan     │
  │                    │                 │                │
  │                    │◄────plan────────┤                │
  │                    │                 │                │
  │                    ├─save_plan───────────────────────►│
  │                    │                 │                │
  │◄─201 Created───────┤                 │                │
  │  {plan_obj}        │                 │                │
```

### 3. Generate Meal Plan (LLM) Flow

```
Client          API Layer     Service Layer    LLM Provider    DB Layer
  │                │               │                │            │
  ├─POST /plans───►│               │                │            │
  │  {strategy:llm}│               │                │            │
  │                │               │                │            │
  │                ├─get_patient──►│                │            │
  │                │               ├─query─────────────────────►│
  │                │               │                │            │
  │                │◄──patient─────┤                │            │
  │                │               │                │            │
  │                ├─generate──────►│                │            │
  │                │               │                │            │
  │                │               ├─build_prompt   │            │
  │                │               │                │            │
  │                │               ├─API call──────►│            │
  │                │               │                │            │
  │                │               │                ├─GPT-4o     │
  │                │               │                │            │
  │                │               │◄───JSON────────┤            │
  │                │               │                │            │
  │                │               ├─validate       │            │
  │                │               ├─normalize      │            │
  │                │               │                │            │
  │                │◄──plan────────┤                │            │
  │                │               │                │            │
  │                ├─save─────────────────────────────────────►│
  │                │               │                │            │
  │◄─201 Created───┤               │                │            │
  │  {plan_obj}    │               │                │            │
```

### 4. Procurement Insights Flow

```
Client          API Layer       DB Layer      LLM Provider
  │                │               │                │
  ├─POST /llm/proc►│               │                │
  │  {planIds[]}   │               │                │
  │                │               │                │
  │                ├─get_plans────►│                │
  │                │               │                │
  │                │◄──plans───────┤                │
  │                │               │                │
  │                ├─aggregate     │                │
  │                ├─count_ingred  │                │
  │                ├─build_prompt  │                │
  │                │               │                │
  │                ├─API call──────────────────────►│
  │                │               │                │
  │                │               │                ├─analyze
  │                │               │                ├─insights
  │                │               │                │
  │                │◄──JSON insights────────────────┤
  │                │               │                │
  │◄─200 OK─────────┤               │                │
  │  {summary,     │               │                │
  │   notes[]}     │               │                │
```

## Data Models

### Patient Model

```
Patient
├── id: string (UUID)
├── name: string
├── age: integer
├── gender: string
├── medicalConditions: string[]
├── allergies: string[]
├── dietaryRestrictions: object[]
│   ├── type: string
│   └── severity: string
├── calorieTarget: integer
├── macroTargets: object
│   ├── protein: integer
│   ├── carbs: integer
│   └── fat: integer
├── createdAt: datetime
└── updatedAt: datetime
```

### Weekly Plan Model

```
WeeklyPlan
├── id: string (UUID)
├── patientId: string (FK)
├── patientName: string
├── weekStart: string (ISO date)
├── strategy: string (rule_based | llm)
├── days: DailyMeals[]
│   └── DailyMeals
│       ├── date: string
│       ├── breakfast: Meal
│       ├── lunch: Meal
│       ├── dinner: Meal
│       ├── snacks: Meal[]
│       ├── totalCalories: integer
│       └── totalNutrition: NutritionInfo
├── weeklyTotals: object
├── generatedAt: datetime
└── Meal
    ├── name: string
    ├── description: string
    ├── ingredients: string[]
    ├── nutrition: NutritionInfo
    │   ├── calories: integer
    │   ├── protein: float
    │   ├── carbs: float
    │   ├── fat: float
    │   ├── fiber: float
    │   └── sodium: float
    ├── preparationTime: integer
    └── difficulty: string
```

## Technology Stack

```
┌──────────────────────────────────────────────────────┐
│                   Technology Stack                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Framework:        FastAPI 0.109                    │
│  Language:         Python 3.11+                     │
│  Server:           Uvicorn (ASGI)                   │
│  ORM:              SQLAlchemy 2.0                   │
│  Validation:       Pydantic 2.5                     │
│  Database:         PostgreSQL / SQLite              │
│  LLM:              OpenAI GPT-4o-mini               │
│  Caching:          Redis (optional)                 │
│  Testing:          Pytest                           │
│  Containers:       Docker + Docker Compose          │
│  Documentation:    OpenAPI / Swagger UI             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## Deployment Architecture

### Option 1: Simple Deployment (Railway/Render)

```
┌───────────────────────────────────────────┐
│              Cloud Platform               │
│  ┌─────────────────────────────────────┐ │
│  │     Web Service (Backend)           │ │
│  │  ┌────────────────────────────┐    │ │
│  │  │   FastAPI Application      │    │ │
│  │  │   (Multiple Instances)     │    │ │
│  │  └────────────────────────────┘    │ │
│  │              │                      │ │
│  │              ▼                      │ │
│  │  ┌────────────────────────────┐    │ │
│  │  │   PostgreSQL Database      │    │ │
│  │  │   (Managed Service)        │    │ │
│  │  └────────────────────────────┘    │ │
│  └─────────────────────────────────────┘ │
│                                           │
│           External APIs:                  │
│           • OpenAI API                   │
│           • (via internet)               │
└───────────────────────────────────────────┘
```

### Option 2: Advanced Deployment (AWS/GCP)

```
┌──────────────────────────────────────────────────────────┐
│                     Cloud Provider                        │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Load Balancer (ALB/GLB)               │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                                │
│           ┌──────────────┴──────────────┐                │
│           │                             │                │
│  ┌────────▼─────────┐        ┌─────────▼────────┐       │
│  │  Backend Instance│        │  Backend Instance│       │
│  │  (Auto-scaling)  │        │  (Auto-scaling)  │       │
│  └──────────────────┘        └──────────────────┘       │
│           │                             │                │
│           └──────────────┬──────────────┘                │
│                          │                                │
│           ┌──────────────┼──────────────┐                │
│           │              │              │                │
│  ┌────────▼────────┐  ┌─▼─────────┐  ┌▼───────────┐     │
│  │   PostgreSQL    │  │   Redis   │  │  S3/Cloud  │     │
│  │  (RDS/Cloud SQL)│  │  (Cache)  │  │  Storage   │     │
│  └─────────────────┘  └───────────┘  └────────────┘     │
│                                                           │
│  External APIs:                                          │
│  • OpenAI API                                            │
│  • Monitoring (DataDog/NewRelic)                         │
└──────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Security Layers                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Transport Layer                                │
│     • HTTPS/TLS encryption                         │
│     • Certificate management                        │
│                                                     │
│  2. API Gateway                                    │
│     • CORS policies                                │
│     • Rate limiting                                │
│     • Request validation                           │
│                                                     │
│  3. Application Layer                              │
│     • Input sanitization (Pydantic)                │
│     • SQL injection prevention (ORM)               │
│     • Authentication (future)                      │
│     • Authorization (future)                       │
│                                                     │
│  4. Data Layer                                     │
│     • Encrypted connections                        │
│     • Encrypted at rest                            │
│     • Access controls                              │
│                                                     │
│  5. Secrets Management                             │
│     • Environment variables                        │
│     • No hardcoded credentials                     │
│     • API key rotation                             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Scalability Considerations

```
Load Level          Architecture                    Cost/Month
───────────────────────────────────────────────────────────────
< 100 users         Single instance                 $10-20
                    SQLite or small PostgreSQL      
                    No caching needed               

100-1,000 users     2-3 instances                   $30-50
                    PostgreSQL (medium)             
                    Redis caching                   
                    Load balancer                   

1,000-10,000 users  Auto-scaling (3-10 instances)   $200-500
                    PostgreSQL read replicas        
                    Redis cluster                   
                    CDN for assets                  

10,000+ users       Microservices architecture      $1,000+
                    Multiple databases              
                    Message queues                  
                    Multi-region deployment         
```

This architecture provides a solid foundation that can scale from prototype to production while maintaining clean code organization and best practices.
