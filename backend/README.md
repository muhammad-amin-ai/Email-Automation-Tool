# Email Automation Platform — Backend

FastAPI backend powering the Email Automation Platform.

## Requirements
- Python 3.11+
- MySQL 8.0+
- Ollama running locally (for AI features)
- Brevo API key (for email sending)

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your MySQL credentials, a real `SECRET_KEY`, your Brevo API
key, and the sender address you verified with Brevo.

## Run

```bash
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

On startup the app auto-creates the MySQL database (if missing) and runs
every pending Alembic migration (`alembic upgrade head`) to bring the
schema up to date, then starts a background scheduler that checks every
`SCHEDULER_INTERVAL_SECONDS` (default 60s) for queued campaign steps whose
delay has elapsed, and sends them via Brevo. This is what makes multi-step
drip campaigns (`delay_hours` on a step) actually fire on their own — you
don't need a separate worker process or cron job for local dev.

## Database migrations (Alembic)

Schema changes are managed with Alembic instead of manual `ALTER TABLE`s.
Migrations run automatically on every app startup, but you can also drive
them by hand from the `backend/` directory:

```bash
alembic upgrade head              # apply all pending migrations
alembic revision --autogenerate -m "add x column"   # after editing a model
alembic downgrade -1              # roll back one migration
alembic history                   # list migrations
```

`alembic/env.py` reuses `app.core.config.settings` (your `.env`), so DB
credentials are only ever defined in one place — there's nothing to
configure in `alembic.ini` itself.

**Upgrading an existing database** (one that was created by the old
`Base.metadata.create_all()` startup hook, before this project used
Alembic): its tables already exist, so running `alembic upgrade head`
directly will fail trying to re-create them. Run this once instead:

```bash
alembic stamp head
```

This tells Alembic "the DB already matches the initial migration" without
touching any tables. Every migration created after that applies normally.

## Tests

```bash
pytest -v
```

## Notes
- Auth: JWT bearer tokens, bcrypt password hashing, per-user data isolation.
- AI endpoints (`/api/ai/...`) require a local Ollama instance
  (`ollama pull llama3.2` then `ollama serve`).
- Email sending requires `BREVO_API_KEY` and `EMAIL_FROM` in `.env`; without
  them, campaign sends will fail with a clear 503 error instead of silently
  doing nothing.
