# StatScout Project Context Blueprint

Last Updated: 2026-04-25

## 1) Purpose of this document

This document is the architecture and delivery context for StatScout, intended to support development of a new isolated module without re-discovering the existing platform foundations.

It captures:

- system boundaries and major components
- runtime stack and dependency versions
- data architecture and MongoDB contracts
- API surface areas and frontend integration points
- environment/configuration requirements
- operational workflows and known implementation constraints

## 2) Project overview

StatScout is a football scouting and analytics platform composed of:

- a Python/FastAPI backend exposing role-protected REST endpoints
- a React/TypeScript frontend (Vite) for scouting workflows
- an ETL and scraping subsystem for ingesting and transforming player and event data
- ML and analytics services (impact scoring, PIE analysis, recommendations, transfer-market intelligence, spatial analytics)

Core user-facing modules include authentication, recommendations, comparison, watchlist, impact engine, transfer-market tools, pipeline controls, scout reports, and an in-progress match analyzer.

## 3) Top-level repository structure

```text
statscout-FYP/
  backend/
    app/                 # FastAPI app (routes, services, schemas, core)
    etl/                 # Bronze/Silver/Gold data pipeline components
    scripts/             # Operational scripts and ingestion jobs
    models/              # Trained model/scaler artifacts + metadata
    notebooks/           # Training notebooks
    static/              # Static assets (including drills/media)
    requirements.txt
    run.py
  frontend/
    src/                 # React pages/components/api/context/types
    public/
    package.json
    vite.config.ts
  README.md
```

## 4) Architecture blueprint

### 4.1 Backend architecture (FastAPI)

Backend entrypoint:

- `backend/run.py` runs `uvicorn app.main:app` on `0.0.0.0:8000` with reload enabled.

Application composition (`backend/app/main.py`):

- startup/shutdown lifespan hooks
- MongoDB connection bootstrap via Motor
- cache warmup for impact percentile distributions at startup
- global CORS middleware
- route registration under `/api/v1`

Layering pattern:

- `app/api/routes/`: HTTP layer
- `app/api/dependencies.py`: dependency injection wiring
- `app/services/`: business logic and data orchestration
- `app/schemas/`: Pydantic request/response contracts
- `app/models/`: document model structures and app-level entities
- `app/core/`: settings, security, and database lifecycle

### 4.2 API route domains

Mounted route groups (all under `/api/v1`):

- `/auth` - registration/login/logout, email verification, password reset
- `/users` - user profile and account management
- `/recommendations` - criteria search, similar players, team/club intelligence, wonderkids
- `/comparison` - player search and head-to-head comparison flows
- `/watchlist` - tracked players and suggestion workflows
- `/impact` - impact scoring, ranking, fit analyses, health
- `/transfer-market` - valuation trajectory and transfer risk analyses
- `/pie` - Player Impact Engine tactical and delta-xP analyses
- `/pipeline` - scraper pipeline orchestration + stream status/logging
- `/spatial` - spatial profile and peer metric analytics
- `/admin` - admin-key protected health/stats/pipeline controls
- `/scout-reports` - report snapshot and scouting-report workflows
- `/match-analyzer` - placeholder endpoints (module currently under development)

### 4.3 Frontend architecture (React + TypeScript)

Frontend shell:

- React 18 app initialized from `src/main.tsx`
- route composition in `src/App.tsx`
- authentication state and session lifecycle in `src/context/AuthContext.tsx`
- centralized Axios client in `src/api/client.ts`

Routing model:

- public pages: home, login, register, verify-email, forgot/reset password
- protected pages: dashboard, watchlist, comparison dashboard, smart recommendation, impact engine, transfer market, pipeline panel, scout reports, match analyzer
- unknown routes redirect to `/`

Frontend-backend connectivity:

- `vite.config.ts` defines development proxy `/api -> http://localhost:8000`
- API client base URL is hardcoded to `http://localhost:8000/api/v1`

Implication for isolated modules:

- New modules should follow the same split: page component + API client methods + route protection where needed.

## 5) Data and persistence architecture

### 5.1 Primary database

- MongoDB Atlas via Motor (async)
- configured in `app/core/database.py`
- database name configurable (`MONGODB_DB_NAME`, default `statscout_db`)

### 5.2 Key MongoDB collections in active use

Core identity and user flows:

- `users`
- `watchlist`
- `reports`
- `training_analyses`
- `coaching_drills`

Scouting and analytics datasets:

- `players_outfield_v2`
- `players_gk_v2`
- `season_distributions`
- `player_report_snapshots`
- `player_spatial_profiles`
- `player_current_season` (TTL cache)
- `player_bio`
- `club_logos`
- `player_shot_data` (TTL cache)

Match and event analytics:

- `matches`
- `match_events`
- `match_player_stats`

### 5.3 Indexing strategy

The backend auto-creates a substantial index set at startup, including:

- identity uniqueness (`users.email`)
- watchlist compound indexes
- player/team/season compound indexes for v2 collections
- TTL indexes for cache collections and expiring report snapshots
- spatial and event query acceleration indexes

This means new modules should be designed around indexed query paths; avoid introducing high-cardinality scans without explicit index additions.

## 6) ETL and ingestion architecture

### 6.1 Pipeline model

Current documentation and scripts indicate a Bronze -> Silver -> Gold pipeline with:

- extraction and raw storage in Bronze
- validation/cleaning in Silver
- upsert/load into MongoDB in Gold

Additionally, scripts exist for direct load and event scraping/orchestration.

### 6.2 ETL implementation locations

- `backend/etl/` - pipeline framework, configuration, migration helpers
- `backend/scripts/` - seasonal scraping, ingestion, checks, utilities

### 6.3 Operational behaviors

- designed to favor upserts over destructive full drops
- supports data quality workflows and metadata artifacts
- includes job-style management endpoints (`/pipeline`, `/admin`) for operational control

## 7) ML and model assets

`backend/models/` contains versioned and aliased artifacts such as:

- `impact_scorer_*.joblib`
- `scaler_*.joblib`
- `feature_names_*.json`
- `metadata_*.json`

Observations:

- artifacts include timestamped, production-tagged, and `latest` aliases
- impact service startup warmup and route behavior rely on these assets and season distributions

Guidance for a new isolated module:

- avoid mutating shared model aliases directly
- if introducing new model families, follow the versioned + alias convention

## 8) Runtime stack and versions

### 8.1 Backend runtime and libraries

Declared/platform context:

- Python: project docs indicate Python 3.11+ minimum, with top-level readme noting Python 3.13 usage in current setup
- FastAPI: `0.104.1`
- Uvicorn: `0.24.0`
- Motor: `3.4.0`
- PyMongo: `4.6.2`
- Pydantic: `2.9.2`
- pydantic-settings: `2.6.1`
- python-jose: `3.5.0`
- bcrypt: `5.0.0`
- python-dotenv: `1.0.1`
- scikit-learn: `1.5.0`
- xgboost: `3.2.0`
- shap: `0.45.0`
- pandas: `2.2.1`
- numpy: `1.26.4`
- scipy: `1.15.3`
- pyarrow: `23.0.1`
- pytest: `9.0.2`

Note:

- `backend/requirements.txt` includes broad notebook/data-science packages in addition to runtime API dependencies. Treat it as a combined dev/runtime environment unless split into profile-specific requirement files.

### 8.2 Frontend runtime and libraries

From `frontend/package.json`:

- React: `18.3.1`
- React DOM: `18.3.1`
- React Router DOM: `6.28.0`
- Axios: `1.7.7`
- @tanstack/react-query: `5.59.20`
- Recharts: `2.15.4`
- Framer Motion: `12.38.0`
- Lucide React: `0.454.0`

Build/dev stack:

- Vite: `5.4.10`
- TypeScript: `~5.6.2`
- Tailwind CSS: `3.4.14`
- ESLint: `9.13.0`
- @vitejs/plugin-react: `4.3.3`
- PostCSS: `8.4.47`
- Autoprefixer: `10.4.20`

### 8.3 ETL-specific declared dependencies

From `backend/etl/requirements.txt` (minimum-style constraints):

- pyarrow >= 12.0.0
- pyyaml >= 6.0
- pandera >= 0.15.0
- apscheduler >= 3.10.0
- prometheus-client >= 0.16.0

## 9) Configuration and environment requirements

Primary backend environment file template: `backend/.env.example`

Required/critical variables:

- `MONGODB_URL`
- `MONGODB_DB_NAME`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_FROM_NAME`
- `FRONTEND_URL`
- `ALLOWED_ORIGINS` (JSON array string)
- `DEBUG`
- `API_V1_PREFIX`

Additional operational behavior:

- Admin routes require `x-admin-key`; expected value uses `ADMIN_API_KEY` if set, otherwise falls back to `SECRET_KEY`.

## 10) Security and auth model

- JWT bearer token auth with configurable expiry
- password hashing via bcrypt
- route-level role/identity checks through dependencies and token decode
- frontend token persistence in `localStorage` with 401 interceptor-driven session reset
- CORS allowlist driven by environment configuration

Design implication for new modules:

- backend additions should keep auth consistency via dependency-based user extraction
- frontend additions should use existing API client token flow rather than ad-hoc clients

## 11) Local development and runbook

### 11.1 Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Expected local endpoint:

- API root: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/api/docs`

### 11.2 Frontend

```bash
cd frontend
npm install
npm run dev
```

Expected local endpoint:

- frontend app: `http://localhost:5173`

## 12) Integration contracts for isolated module development

Use this checklist for a new module to remain decoupled and production-compatible.

### 12.1 Backend contract

- create a dedicated route file under `app/api/routes/` with its own prefix
- keep business logic in `app/services/` (no heavy logic in route handlers)
- define request/response schemas in `app/schemas/`
- register the router in `app/main.py`
- use dependency injection for DB and auth context
- define/extend indexes if new query patterns need them

### 12.2 Frontend contract

- add page(s) under `frontend/src/pages/` (or feature subfolder)
- add API methods in `frontend/src/api/client.ts`
- register route in `frontend/src/App.tsx`
- wrap route with `ProtectedRoute` if auth is required
- keep types in `frontend/src/types/`

### 12.3 Data contract

- preserve `*_v2` collection conventions for scouting datasets
- avoid schema-breaking writes to shared collections without compatibility strategy
- if introducing new collection(s), document index and retention strategy up front

## 13) Current implementation notes and constraints

- Match Analyzer routes are currently placeholder/in-progress and return not implemented for several endpoints.
- Backend requirements are broad and include notebook tooling; environment footprint is larger than strictly necessary for API-only deployment.
- There is mixed documentation wording around Python version (3.11+ minimum vs 3.13 used). Validate runtime version when deploying isolated modules.
- Frontend dev proxy uses `/api`, while API client also hardcodes full backend base URL; new modules should keep one clear strategy to avoid environment drift.

## 14) Suggested baseline for a new isolated module

Recommended module boundaries:

- isolated API namespace: `/api/v1/<module-name>`
- service package: `app/services/<module_name>_service.py` (or folder)
- schema package: `app/schemas/<module_name>.py`
- optional persistence: dedicated collection(s) with explicit indexes
- frontend route path: `/<module-name>` with lazy-loaded page
- shared API client methods with typed responses

Minimum acceptance criteria:

- auth and authorization behavior consistent with current patterns
- OpenAPI docs generated with clear summary/description
- structured error responses (4xx/5xx) and logging
- no full-collection scans in hot paths
- local run compatibility with existing backend and frontend startup commands

---

This context file should be refreshed whenever route maps, dependency versions, or data contracts materially change.