# Frontend Setup (`/frontend`)

This guide covers setting up, configuring, and running the **Vite + React 18 + TypeScript** Single-Page Application (SPA) for **Document Copilot**. The frontend connects directly to our FastAPI backend for real-time Server-Sent Events (SSE) chat streaming and Supabase Auth JWT token management.

---

## 🛠 Prerequisites

Ensure you have **Node.js 20+ (LTS)** and **`pnpm`** installed globally:
```bash
node -v
npm install -g pnpm
```

---

## 📦 Init from Scratch (From an Empty `/frontend` Folder)

If you are initializing this project from an empty folder or auditing how our frontend stack (`Vite + React TS + Tailwind + Shadcn + Supabase`) was scaffolded from scratch, these are the exact commands we executed:

```bash
cd frontend
pnpm create vite . --template react-ts
pnpm install
pnpm add react-router-dom @supabase/supabase-js
pnpm add -D tailwindcss @tailwindcss/vite
pnpm dlx shadcn@latest init --yes
```

*(Note: If you have already cloned this repository from GitHub, `package.json` and `pnpm-lock.yaml` already contain all dependencies—you only need to run `pnpm install` in the **Installation & Local Development** section below).*

---

## ⚙️ Environment Configuration (`.env`)

Inside the `/frontend` directory, copy `.env.example` to create your local `.env` file:
```bash
cd frontend
cp .env.example .env
```

Ensure your `.env` contains these 3 variables (`VITE_` prefix is mandatory so Vite embeds them into the browser runtime):
```env
# Backend API base URL
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Supabase Auth Credentials
VITE_SUPABASE_URL=https://<your_project_id>.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_...
```

---

## 🚀 Installation & Local Development

Install all frontend packages (React Router, Tailwind CSS, Lucide Icons, Radix UI/Shadcn, and Supabase client):
```bash
cd frontend
pnpm install
```

Start the Vite hot-module-replacement (HMR) development server:
```bash
pnpm dev
```
* Open **`http://localhost:5173`** in your browser.
* Log in using your Supabase user credentials to access the chat and document exploration interfaces.

---

## 🔍 Type Checking & Production Build

To verify TypeScript correctness across all React components and hooks without starting the dev server:
```bash
pnpm tsc --noEmit
```

To test the optimized static production bundle locally before deploying to Railway:
```bash
pnpm build
```
*(The compiled static files will be placed inside `frontend/dist/`).*
