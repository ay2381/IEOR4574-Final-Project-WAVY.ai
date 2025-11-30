## Backend Game Plan

The frontend already speaks to a REST API. This folder is a starter area for you to implement that service in whatever stack you prefer. Recommended layout:

```
apps/backend/
  src/
    api/            ← route handlers / controllers
    domain/         ← Patient, WeeklyPlan models & validators
    services/       ← business logic, nutrition calculations
    llm/            ← wrappers for OpenAI/Azure/Bedrock, prompt templates
    db/             ← ORM/repository layer (Prisma, SQLAlchemy, etc.)
  tests/
  package.json / pyproject.toml / requirements.txt (choose one stack)
```

### Required Endpoints

| Method | Path | Body | Response |
| --- | --- | --- | --- |
| `GET` | `/patients` | – | `Patient[]` |
| `POST` | `/patients` | `CreatePatientPayload` | `Patient` |
| `DELETE` | `/patients/:id` | – | `204` |
| `GET` | `/plans` | – | `WeeklyPlan[]` |
| `POST` | `/plans/generate` | `{ patientIds: string[]; weekStart?: string; strategy?: 'rule_based' | 'llm' }` | `WeeklyPlan[]` |
| `POST` | `/llm/procurement-insights` | `{ planIds: string[]; instructions?: string }` | `{ summary: string; procurementNotes: string[]; generatedAt: string; tokenUsage?: { promptTokens: number; completionTokens: number } }` |

Types match the frontend definitions in `apps/frontend/lib/types.ts`.

### LLM Responsibilities

`strategy === 'llm'` (plan generation) and `/llm/procurement-insights` should:

1. Gather patient + plan context from the database.
2. Build prompts or tool-call payloads (include dietary restrictions, allergies, calorie targets).
3. Call your preferred provider (OpenAI, Azure OpenAI, Claude, Gemini, etc.).
4. Normalize responses into deterministic JSON before returning to the frontend.

Implement retry/backoff, token accounting, and guardrails (max tokens, profanity filters, etc.).

### Suggested Environment Variables

```
PORT=8080
DATABASE_URL=postgresql://...
OPENAI_API_KEY=...
LLM_PROVIDER=openai|azure|bedrock
SESSION_SECRET=...
ALLOWED_ORIGINS=http://localhost:5173,https://frontend.prod
```

Expose them via `.env` (never commit real secrets). Remember to enable CORS with credentials so the React Query client (which already uses `credentials: 'include'`) works seamlessly.

### Next Steps

1. Pick a stack (FastAPI + SQLModel, Express + Prisma, NestJS + TypeORM, etc.).
2. Scaffold base project inside this folder (`npm init`, `poetry init`, etc.).
3. Implement data models + persistence.
4. Wire up REST routes to match the contract above.
5. Integrate LLM provider + caching layer (Redis or database table) for AI outputs.
6. Document any new endpoints or env vars in this README for the rest of the team.

Once the backend serves live data, update `apps/frontend/.env.local` with the deployed API base URL and the UI will be fully data-driven. Happy building!

