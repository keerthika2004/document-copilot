# 🤖 Document Copilot — Backend & Agentic RAG Service (`/backend`)

The core asynchronous backend service powered by **Python 3.12**, **FastAPI**, and **PydanticAI**. This service manages user authentication, multi-step autonomous LLM retrieval loops, hybrid vector/keyword search with Reciprocal Rank Fusion (RRF), real-time Server-Sent Events (SSE) streaming, and strict citation grounding verification.

---

## 🏗 Backend Architecture & Components

```text
backend/
├── alembic/              # Async PostgreSQL schema migrations (SQLAlchemy + Alembic)
├── app/
│   ├── api/              # REST & SSE API endpoints (`chat.py`, `documents.py`, `auth.py`)
│   ├── assistant/        # PydanticAI agent workflow (`agent.py`) & structured outputs (`outputs.py`)
│   ├── chat/             # SSE stream orchestrator (`orchestrator.py`) & conversation persistence
│   ├── database/         # SQLAlchemy 2.0 ORM models (`document_chunk.py`, `source_document.py`)
│   ├── grounding/        # Hallucination filter & exact quote verification (`validator.py`)
│   └── retrieval/        # Hybrid RRF fusion (`fusion.py`), vector (`service.py`) & keyword search (`queries.py`)
├── ingest/               # Semantic markdown chunker & local embedding indexer (`chunk_and_embed.py`)
├── tests/                # Automated pytest suite (`test_grounding.py`, `test_retrieval.py`)
├── nixpacks.toml         # Railway cloud build configuration
└── pyproject.toml        # Deterministic dependencies managed via `uv`
```

---

## ⚡ Key Engineering Subsystems

### 1. Agentic RAG Engine (`app/assistant`)
* **Typed Orchestration**: Uses `PydanticAI` to execute multi-turn, autonomous reasoning loops against our document database.
* **Structured Outputs (`outputs.py`)**: Enforces strict JSON response schemas (`GroundedAnswer` with `Union[bool, str]` validation resilience for cloud inference models).
* **High-Speed Inference (`Groq Llama 3.3 70B`)**: Streams tokens at ~250 words/sec (`groq:llama-3.3-70b-versatile`) with zero rate-limit friction.

### 2. Hybrid Retrieval with RRF (`app/retrieval`)
Combines dense 384-dimensional vector similarity (`pgvector` via local `BAAI/bge-small-en-v1.5` embeddings) and PostgreSQL lexical full-text search (`tsvector` & `websearch_to_tsquery`) to capture both semantic concepts and exact table numbers/headings.
* *For mathematical details and RRF parameters (`k=60`), see **[app/retrieval/README.md](app/retrieval/README.md)**.*

### 3. Strict Grounding Validator (`app/grounding/validator.py`)
Before any streaming answer is finalized, our `GroundingValidator` audits every inline citation (`[1]`, `[2]`), checks exact quote verbatim exactness (`exact_quote`) against database source text, strips unsupported claims, and ensures zero hallucination.

### 4. Semantic Chunking & Embedding Pipeline (`ingest/`)
Ingests clean markdown files produced by the `/data` Docling toolchain (`data/markdown/`):
* **Section-Aware Chunking (`chunking.py`)**: Splits sections by markdown headers into ~1,000 character chunks (`150-char overlap`) while preserving financial table rows.
* **Zero-Cost Local Embeddings (`embeddings.py`)**: Uses `fastembed`/`sentence-transformers` (`BAAI/bge-small-en-v1.5`) in local memory to generate 384-dimensional vectors without outbound OpenAI API costs.
* **Run Ingestion**:
  ```bash
  uv run python -m ingest.chunk_and_embed
  ```

---

## 🚀 Getting Started

### 1. Setup Environment
Ensure you have a `.env` file in `backend/` copied from `.env.example`:
```bash
cp .env.example .env
```
Key variables needed:
```env
DATABASE_URL="postgresql://postgres.<project_id>:<password>@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"
SUPABASE_URL="https://<project_id>.supabase.co"
SUPABASE_ANON_KEY="sb_publishable_..."
SUPABASE_SERVICE_ROLE_KEY="sb_secret_..."
GROQ_API_KEY="gsk_..."
LLM_MODEL="groq:llama-3.3-70b-versatile"
EMBEDDING_MODEL="BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSIONS=384
ALLOWED_ORIGINS="http://localhost:5173"
```

### 2. Install Dependencies via `uv`
```bash
uv sync
```

### 3. Apply Database Migrations
Run Alembic to create database tables, vector extensions (`pgvector`), and GIN indexes in Supabase:
```bash
uv run alembic upgrade head
```

### 4. Start Development Server
```bash
uv run uvicorn app.main:app --reload --port 8000
```
*Live API server will run at `http://localhost:8000`. Interactive Swagger UI available at `http://localhost:8000/docs`.*

---

## 🧪 Testing & Quality Assurance

Run our automated retrieval and grounding verification test suite:
```bash
uv run pytest -k "test_grounding or test_retrieval" -v
```
To check code formatting and linting:
```bash
uv run ruff check && uv run ruff format
```
