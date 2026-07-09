# 🚂 Railway Production Deployment Guide (`document-copilot`)

Welcome to Railway! This guide is tailored specifically for deploying **Document Copilot** (FastAPI Backend + Vite React Frontend monorepo) to production on Railway for the first time. We have already pre-configured automated `nixpacks.toml` files in both folders, so Railway will build and serve your app automatically with zero guesswork.

---

## 📋 What You Need Handy Before You Start (Checklist)

Before opening Railway, have the following 4 items ready to copy-paste:

1. **GitHub Repository**: Make sure all your latest commits are pushed to your remote GitHub repository (`document-copilot`).
2. **Railway Account**: Log into [Railway.app](https://railway.app/) using your GitHub account.
3. **Supabase Database Credentials** (from your local `backend/.env` file):
   - `SUPABASE_URL` (`https://<your_project_id>.supabase.co`)
   - `SUPABASE_ANON_KEY` (`sb_publishable_...`)
   - `SUPABASE_SERVICE_ROLE_KEY` (`sb_secret_...`)
   - `DATABASE_URL` (Direct PostgreSQL connection string: `postgresql://postgres...`)
4. **AI / LLM API Key**:
   - `OPENAI_API_KEY` (`sk-proj-...`) and/or `GEMINI_API_KEY` (`AIzaSy...`)

---

## 🚀 Step-by-Step Deployment Walkthrough

In Railway, since our codebase is a **monorepo** (backend and frontend inside one repository), you will create **two services inside one single Railway project**.

---

### Step 1: Create the Project & Backend Service (`backend`)

1. Go to your [Railway Dashboard](https://railway.app/dashboard) and click the **`+ New Project`** button.
2. Select **`Deploy from GitHub repo`** and choose `document-copilot` from the list.
3. Railway will immediately add the repository to your project canvas. Click on the newly added card (this will become our **Backend** service).
4. **Configure Root Directory**:
   - In the right sidebar, go to the **Settings** tab.
   - Scroll to **Source** → **Root Directory** and change it from `/` to:
     ```text
     /backend
     ```
   - *Note: Railway will automatically read `backend/nixpacks.toml`, install Python `uv`, run `alembic upgrade head` to verify your database tables on boot, and start `uvicorn`!*
5. **Generate Backend Domain URL**:
   - In the **Settings** tab, scroll to **Networking** → Click **`Generate Domain`**.
   - Copy the generated public URL (for example: `https://document-copilot-backend-production.up.railway.app`). Keep this URL handy for Step 2!
6. **Set Backend Environment Variables**:
   - Go to the **Variables** tab of this backend service and click **`+ New Variable`** (or **`Raw Editor`** to paste all at once):
     ```env
     SUPABASE_URL=https://<your_project_id>.supabase.co
     SUPABASE_ANON_KEY=sb_publishable_...
     SUPABASE_SERVICE_ROLE_KEY=sb_secret_...
     DATABASE_URL=postgresql://postgres.<your_project_id>:<password>@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
     GROQ_API_KEY=gsk_your_groq_api_key_here
     LLM_MODEL=groq:llama-3.3-70b-versatile
     EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
     EMBEDDING_DIMENSIONS=384
     ALLOWED_ORIGINS=http://localhost:5173
     ```
   - *Tip: We will update `ALLOWED_ORIGINS` to your frontend domain right after we create it in Step 2.*

---

### Step 2: Create the Frontend Service (`frontend`)

1. In the **same Railway project canvas**, click the top-right **`+ New`** button → **`GitHub Repo`** → select `document-copilot` again. (You now have two service cards on your screen).
2. Click the second card and rename it to **`frontend`** (click the name at the top or in settings).
3. **Configure Root Directory**:
   - Go to **Settings** → **Source** → **Root Directory** and set it to:
     ```text
     /frontend
     ```
   - *Note: Railway will automatically read `frontend/nixpacks.toml`, run `pnpm install && pnpm build`, and serve the compiled SPA on `$PORT`.*
4. **Generate Frontend Domain URL**:
   - In **Settings** → **Networking** → Click **`Generate Domain`**.
   - Copy your frontend's public URL (for example: `https://document-copilot-frontend-production.up.railway.app`).
5. **Set Frontend Environment Variables (`VITE_*`)**:
   - Go to the **Variables** tab of the `frontend` service and add these 3 variables exactly (`VITE_` variables are required *before* the build completes so Vite can embed them into the static JavaScript):
     ```env
     VITE_API_BASE_URL=https://<YOUR_BACKEND_RAILWAY_DOMAIN>/api/v1
     VITE_SUPABASE_URL=https://<your_project_id>.supabase.co
     VITE_SUPABASE_ANON_KEY=sb_publishable_...
     ```
   - *(Make sure `VITE_API_BASE_URL` points to your exact backend domain from Step 1 ending with `/api/v1`, e.g., `https://document-copilot-backend-production.up.railway.app/api/v1`).*

---

### Step 3: Connect CORS & Verify Deployment 🎉

1. Go back to your **Backend** service card → **Variables** tab.
2. Update **`ALLOWED_ORIGINS`** to include your newly generated frontend domain:
   ```env
   ALLOWED_ORIGINS=https://<YOUR_FRONTEND_RAILWAY_DOMAIN>
   ```
3. Railway will automatically redeploy the backend with the new CORS origin.
4. Once both cards show a green checkmark **`Active / Deployed`**, click your frontend domain link! You can sign in and start analyzing SEC filings live from the cloud!

---

## 🔍 Troubleshooting & Pro-Tips

- **How to view logs if something fails on startup?** Click either service card (`backend` or `frontend`) and go to the **Deployments** tab → Click **View Logs**.
- **What if the frontend shows `Failed to fetch` on login or chat?** Check your browser Console (`F12` -> Console). If it says CORS error or missing API URL, double-check that `VITE_API_BASE_URL` in the frontend variables ends with `/api/v1` and that `ALLOWED_ORIGINS` in the backend variables exactly matches your frontend Railway URL (no trailing slash).
- **Automatic Migrations**: Because we configured `backend/nixpacks.toml`, whenever you push new database models to GitHub, Railway automatically runs `alembic upgrade head` before starting the server so your PostgreSQL database is always perfectly synced!
