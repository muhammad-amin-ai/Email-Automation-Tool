# Email Automation Platform

A full-stack email automation platform: FastAPI + MySQL backend, React +
Vite frontend, AI email drafting via a local Ollama model, and email
delivery via Brevo.

## Structure

```
.
├── backend/     FastAPI API, MySQL models, background scheduler
└── frontend/    React + Vite single-page app
```

## Quick start

```bash
# 1. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in DB / Brevo / secret key
uvicorn app.main:app --reload

# 2. Frontend (in a second terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

Then open http://localhost:5173, register an account, and work through
Contacts → Templates → Campaigns.

## What's included
- JWT auth with per-user data isolation.
- Contacts: CRUD + CSV import with validation/dedup.
- Templates: CRUD, with `{{ first_name }}` / `{{ last_name }}` /
  `{{ email }}` / `{{ full_name }}` variables.
- Campaigns: multi-step drip sequences with per-step delay (in hours).
- Alembic-managed schema migrations (`backend/alembic/`), run automatically
  on startup.
- A background scheduler inside the API process that polls for due steps
  and sends them via Brevo automatically — no separate worker needed for
  local/dev use.
- AI drafting (subject + body, subject-only, and personalization) via a
  local Ollama model.
- Analytics summary endpoint + dashboard.

## Known limitations (worth knowing before production use)
- No rate limiting on `/auth/login` or `/auth/register`.
- No Brevo webhook endpoint for bounce/complaint events — `EmailEvent`
  only records sends made from this app.
- The scheduler runs in-process (APScheduler), which is fine for a single
  backend instance but won't coordinate across multiple replicas; a real
  deployment would want Celery/RQ + Redis or a dedicated worker instead.
