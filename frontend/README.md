# 💻 Document Copilot — Frontend SPA (`/frontend`)

The modern Single-Page Application (SPA) for **Document Copilot**, built with **Vite**, **React 18**, **TypeScript**, **Tailwind CSS**, and **Shadcn UI**. It delivers a highly responsive, glassmorphic user interface for real-time AI chat streaming, interactive source citation inspection, and document exploration.

---

## ✨ Features & UI Highlights

### 1. 🌊 Real-Time SSE Chat Streaming (`useChat.ts`)
* Connects directly to the backend FastAPI Server-Sent Events (SSE) endpoint (`/api/v1/chat/stream`).
* Streams tokens smoothly at ultra-fast speeds (`~250 words/sec` via Groq) while displaying real-time agent reasoning indicators and tool execution states.

### 2. 🔍 Interactive Citation Drawers (`ReferenceList.tsx` & `MessageBubble.tsx`)
* Every AI response includes clickable inline citation markers (`[1]`, `[2]`).
* Clicking any citation opens an interactive source drawer detailing the exact SEC document title, ticker, fiscal year, section heading, confidence score, and the exact highlighted verbatim quote (`exact_quote`) retrieved from the database.

### 3. 🔐 Secure Supabase Authentication (`useAuth.ts`)
* Integrates `@supabase/supabase-js` for secure user authentication and session persistence.
* Automatically attaches Bearer JWT authorization headers (`Authorization: Bearer <token>`) to every backend API and streaming request.

---

## 📁 Directory Structure

```text
frontend/
├── src/
│   ├── components/
│   │   ├── chat/             # Chat UI (`MessageBubble.tsx`, `ReferenceList.tsx`, `ChatInput.tsx`, `Sidebar.tsx`)
│   │   ├── layout/           # Main workspace and navigation layout (`WorkspaceLayout.tsx`)
│   │   └── ui/               # Reusable Shadcn UI components (`button.tsx`, `tooltip.tsx`, `textarea.tsx`)
│   ├── hooks/                # Custom React hooks (`useChat.ts`, `useAuth.ts`)
│   ├── lib/                  # API client utilities (`api.ts`, `http.ts`, `supabase.ts`)
│   ├── pages/                # Application views (`ChatPage.tsx`, `Login.tsx`, `DocumentsPage.tsx`)
│   ├── App.tsx               # Root application router
│   └── index.css             # Vanilla + Tailwind design tokens and glassmorphism styling
├── nixpacks.toml             # Railway cloud deployment configuration
├── package.json              # Dependencies and scripts (`dev`, `build`, `start`)
└── tsconfig.json             # TypeScript compiler settings
```

---

## 🚀 Getting Started

### 1. Prerequisites
Make sure you have **Node.js 20+** and **`pnpm`** installed:
```bash
npm install -g pnpm
```

### 2. Setup Environment Variables
Copy `.env.example` to `.env` inside `frontend/`:
```bash
cp .env.example .env
```
Add your backend API endpoint and Supabase publishable credentials:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://<your_project_id>.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_...
```
*(When deploying to production on Railway, make sure `VITE_API_BASE_URL` points to your live Railway backend URL ending with `/api/v1`).*

### 3. Install Dependencies & Start Dev Server
```bash
pnpm install
pnpm dev
```
*Open your browser at **`http://localhost:5173`** to log in and interact with your SEC Document Copilot!*

---

## 📦 Production Build & Railway Deployment
To verify the production TypeScript build locally:
```bash
pnpm build
```
When deploying to Railway (`frontend/nixpacks.toml`), Railway automatically runs `pnpm install --frozen-lockfile` and `pnpm build`, serving your compiled single-page application cleanly in production.
