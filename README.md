# StatScout Scaffold

This workspace is scaffolded from the project context in `PROJECT_CONTEXT.md` with:

- `backend/` FastAPI API skeleton with route domains mounted under `/api/v1`
- `frontend/` React + TypeScript + Vite skeleton with public/protected routes
- baseline environment templates and dependency manifests

## Run backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

OpenAPI docs: `http://localhost:8000/api/docs`

## Connect to MongoDB Atlas (`statscout_db`)

1. Create `backend/.env` from `backend/.env.example`.
2. Set your Atlas connection string:

```bash
MONGODB_URL=mongodb+srv://<username>:<password>@<cluster-host>/?retryWrites=true&w=majority&appName=StatScout
MONGODB_DB_NAME=statscout_db
```

3. Start the backend from `backend/` using `python run.py`.

Scout Reports has read-only helper endpoints so you can use existing collections safely:

- `GET /api/v1/scout-reports/health`
- `GET /api/v1/scout-reports/collections?known_only=true`
- `GET /api/v1/scout-reports/collections/{collection_name}/preview?limit=10`

These endpoints do not create, update, or delete collection data.

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`
