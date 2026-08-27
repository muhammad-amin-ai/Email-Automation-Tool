# Email Automation Platform — Frontend

React + Vite single-page app for the Email Automation Platform backend.

## Setup

```bash
cd frontend
npm install
cp .env.example .env
```

`VITE_API_BASE_URL` in `.env` should point at your running backend
(default `http://localhost:8000/api`).

## Run

```bash
npm run dev
```

Open http://localhost:5173. Register an account, then:

1. Add contacts (manually or via CSV import).
2. Create an email template (optionally draft it with AI).
3. Create a campaign, attach one or more templates as steps (each with an
   optional delay in hours), and hit **Start**.
4. Watch the campaign detail page — it polls the backend every 8s and shows
   each queued/sent/failed job as the background scheduler processes them.

## Build for production

```bash
npm run build
npm run preview
```
