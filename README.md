# IEOR4574-Final-Project-WAVY.ai

Repository for the WAVY.ai IEOR4574 final project.  
Both the React nutrition-planner frontend and the backend service scaffolding now live in this monorepo.

## Repository Layout

```
apps/
  backend/        ← FastAPI backend
  frontend/       ← Vite + React + Tailwind interface
data/
  Disease_rules.csv
  Recipes_with_Ingredients.csv
```

All shared CSV assets now live under the root-level `data/` directory. Backend scripts (`make recipes-import`, `make rules-import`) read from that directory by default, so you no longer need to copy files into `apps/backend`. If you add new datasets, drop them into `data/` and commit once.

## Frontend (apps/frontend)

| Command | Description |
| --- | --- |
| `cd apps/frontend` | switch into the frontend workspace |
| `npm install` | install dependencies (React 18, Vite 5, Tailwind 4, React Query, Radix UI, Lucide icons) |
| `npm run dev` | start local dev server (http://localhost:5173) |
| `npm run build` / `npm run preview` | production build + preview |

Environment variable: create `apps/frontend/.env.local` with `VITE_API_BASE_URL=<backend-origin>/api`.

The UI already expects the following REST endpoints:

- `GET /patients`
- `POST /patients`
- `DELETE /patients/:id`
- `GET /plans`
- `POST /plans/generate`
- `POST /llm/procurement-insights`

`POST /plans/generate` accepts `{ patientIds: string[]; weekStart?: string; strategy?: 'rule_based' | 'llm' }`.  
`POST /llm/procurement-insights` accepts `{ planIds: string[]; instructions?: string }` and returns `{ summary, procurementNotes, generatedAt, tokenUsage }`.

## Backend (apps/backend)

The backend folder is intentionally lightweight so you can choose your preferred stack (FastAPI, NestJS, Express, Rails, etc.). See `apps/backend/README.md` for concrete suggestions on:

- Directory layout (`src/api`, `src/services`, `src/llm`, etc.)
- Data models required by the frontend (`Patient`, `WeeklyPlan`, `DailyMeals`)
- LLM proxy responsibilities (wrapping OpenAI/Azure, rate limiting, prompt templating)
- Suggested `.env` keys (`OPENAI_API_KEY`, `DATABASE_URL`, `SESSION_SECRET`, …)

## Backend-to-Frontend Contract

The React app already ships with:

- A typed API client (`apps/frontend/lib/api/*`) that calls the endpoints above.
- React Query hooks that cache patient & plan data.
- UI toggles for deterministic vs. LLM-based plan generation.
- A procurement panel that can call `/llm/procurement-insights` to summarize inventory actions.

Implementing the backend endpoints with the same request/response signatures is enough to make the UI fully dynamic.

## Deployment Notes

- You can deploy frontend independently (e.g., Vercel, Netlify, Cloudflare) and point `VITE_API_BASE_URL` to the backend environment.
- Backend can run anywhere (Render, Railway, Fly, AWS). Just enable CORS + cookies so the existing client works.
- Consider Dockerizing both apps later (`apps/frontend/Dockerfile`, `apps/backend/Dockerfile`) once the backend is implemented.

Feel free to extend this structure with `/packages` for shared code or `/infrastructure` for IaC as the project grows.
