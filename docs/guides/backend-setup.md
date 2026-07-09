# Backend Setup (`/backend`)

This guide covers setting up, configuring, and running the Python + FastAPI backend service for **Document Copilot**. The backend owns all AI orchestration (`PydanticAI`), database access (`SQLAlchemy` + `Alembic`), hybrid vector/keyword retrieval (`pgvector` + `Postgres FTS`), and exact quote grounding verification (`GroundingValidator`).

---

## 🛠 Prerequisites & Package Installation

We use **`uv`** as our deterministic Python package manager (`Python 3.12+`).

If starting from scratch (`backend/`), the exact packages required by our architecture are:
```bash
cd backend
uv sync
uv add fastapi uvicorn pydantic pydantic-settings httpx structlog groq supabase pydantic-ai sqlalchemy alembic "psycopg[binary]" pgvector fastembed
uv add --dev pytest ruff
```
*(If you have already cloned the repo, simply running `uv sync` in `/backend` will install all needed dependencies automatically from `pyproject.toml` / `uv.lock`).*

---

## ⚙️ Environment Configuration (`.env`)

Before running database migrations or the web server, create your `.env` file inside `/backend` from `.env.example`:
```bash
cd backend
cp .env.example .env
```

Ensure your `.env` contains:
```env
# Database Connections
DATABASE_URL="postgresql://postgres.<project_id>:<password>@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"

# Supabase Auth & Storage Credentials
SUPABASE_URL="https://<project_id>.supabase.co"
SUPABASE_ANON_KEY="sb_publishable_..."
SUPABASE_SERVICE_ROLE_KEY="sb_secret_..."

# Inference & Embedding Engine
GROQ_API_KEY="gsk_..."
LLM_MODEL="groq:llama-3.3-70b-versatile"
EMBEDDING_MODEL="BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSIONS=384

# CORS Settings
ALLOWED_ORIGINS="http://localhost:5173"
```

---

## 🗄 Database Migrations (`Alembic`)

Alembic manages all schema migrations, table creations, and index updates in our Supabase PostgreSQL database. Our migrations create:
* The `vector` extension (`create extension if not exists vector`)
* `source_documents` and `document_chunks` tables (`vector(384)` embedding column and `tsvector` full-text column)
* HNSW vector similarity and GIN full-text search indexes
* Row-level security (RLS) policies

### Running Migrations
Always run this command after configuring your `.env` to make sure your database tables match the code:
```bash
uv run alembic upgrade head
```

### Creating New Migrations (When Modifying ORM Models)
If you update any model inside `app/database/models/`, generate a new revision:
```bash
uv run alembic revision --autogenerate -m "description of schema change"
uv run alembic upgrade head
```

---

## 🚀 Running the Server Locally

Start the FastAPI development server with hot-reloading:
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```
* **API Endpoints**: Available at `http://127.0.0.1:8000/api/v1`
* **Interactive Swagger Documentation**: Available at `http://127.0.0.1:8000/docs`

---

## 📥 Ingesting SEC Documents

To populate your database with semantic chunks and 384-dimensional local vector embeddings:
1. Ensure you have converted `.htm` filings to `.md` inside `/data` (see [data/README.md](../../data/README.md)).
2. Run the chunk and embed module from `backend/`:
```bash
uv run python -m ingest.chunk_and_embed
```

---

## 🧪 Running Automated Tests & Code Linter

Execute our unit test suite for hybrid RRF retrieval and grounding exactness:
```bash
uv run pytest -k "test_grounding or test_retrieval" -v
```

Run code quality and formatting checks (`ruff`):
```bash
uv run ruff check
uv run ruff format
```
