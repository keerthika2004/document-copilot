# Supabase Setup Guide

We use **Supabase** as our unified cloud database provider for **PostgreSQL** (storing users, chats, source documents, document chunks, 384-dimensional vector embeddings, full-text search `tsvector` indexes, and citations) and **Supabase Auth** (email/password JWT session management).

---

## 1. Create a Supabase Project

1. Go to **[supabase.com](https://supabase.com)** and sign in.
2. Click **`New project`** in your organization dashboard.
3. Set a **Project name** (e.g. `Document Copilot`).
4. Generate a strong **Database password** (save this securely—you will need it for your `DATABASE_URL` direct Postgres connection string).
5. Choose a region close to your users and click **Create new project** (~1–2 minutes to provision).

---

## 2. Collect Required Credentials

Once provisioned, navigate to **Project Settings → API** and **Project Settings → Database** to gather the following keys:

| Credential | Where to find it | Used by |
| :--- | :--- | :--- |
| **Project URL** | Settings → API → Project URL (`https://...supabase.co`) | `backend/.env` & `frontend/.env` (`SUPABASE_URL` / `VITE_SUPABASE_URL`) |
| **`anon` `public` key** | Settings → API → `anon` `public` API key (`sb_publishable_...`) | `backend/.env` & `frontend/.env` (`SUPABASE_ANON_KEY` / `VITE_SUPABASE_ANON_KEY`) |
| **`service_role` `secret` key** | Settings → API → `service_role` `secret` key (`sb_secret_...`) | `backend/.env` only (`SUPABASE_SERVICE_ROLE_KEY`) — **Never expose to frontend!** |
| **Direct Database Connection String** | Settings → Database → Connection string → **Direct connection** | `backend/.env` (`DATABASE_URL`) used by SQLAlchemy & Alembic |

> [!IMPORTANT]
> **Use the Direct Connection String for Migrations**: Make sure your `DATABASE_URL` in `backend/.env` uses port `5432` or the direct connection (`postgresql://postgres.<project_id>:<password>@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres`) rather than the transaction pooler when running Alembic migrations.

---

## 3. Authentication Configuration (`Email/Password`)

Document Copilot uses clean email/password session authentication via `@supabase/supabase-js`.
1. Go to **Authentication → Providers** in the Supabase Dashboard.
2. Ensure **Email** provider is enabled.
3. For local development testing, you can go to **Authentication → Email Templates** or settings and uncheck *"Confirm email"* so new user sign-ups can log directly into the chat app without needing an active email confirmation link.

---

## 4. Database Schema & `pgvector` Management

Do not create database tables manually inside the Supabase SQL editor! All table creation, vector extensions, and indexes are managed deterministically via Python **Alembic** migrations.

Our automated migrations (`backend/alembic/versions/`) configure:
* **`create extension if not exists vector`**: Enables `pgvector` in your Supabase Postgres instance.
* **`vector(384)` Column**: Configures the `embedding` column on `document_chunks` exactly for our local HuggingFace `BAAI/bge-small-en-v1.5` embeddings.
* **`tsvector` Full-Text Search Column**: Configures English keyword stemming for exact-match retrieval (`idx_document_chunks_fts`).
* **HNSW & GIN Indexes**: Fast sub-second cosine distance and lexical queries.
* **Row-Level Security (RLS)**: Protects user chat histories and citation records.

### Applying Schema to Supabase
Open your terminal in `/backend` and run:
```bash
uv run alembic upgrade head
```

---

## 🔗 Next Steps

* Go to **[Backend Setup Guide](backend-setup.md)** (`backend/`) to run the Python API server and ingest sample SEC filings.
* Go to **[Frontend Setup Guide](frontend-setup.md)** (`frontend/`) to start the React SPA chat application.
