# Sessional Setup

This document explains how to install dependencies and run the current MVP scaffold.

## Prerequisites

- Node.js 20+
- Python 3.11+ (a local venv is already scaffolded under `backend/.venv`)
- PostgreSQL 15+ running locally

## Project Structure

- `frontend`: Next.js (App Router) patient + clinician UI
- `backend`: FastAPI API with mocked check-in and brief endpoints

## Install Dependencies

Run from repo root:

```bash
cd frontend && npm install
```

Backend dependencies are already pinned in `backend/requirements.txt`. If you need to reinstall:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at `http://localhost:3000`.

## Role-Based App Routes

- Start page: `/`
- Patient auth: `/auth/patient`
- Clinician auth: `/auth/clinician`
- Patient home: `/patient`
- Clinician dashboard: `/clinician`

## Minimal Account Lifecycle (MVP)

- Both `patient` and `clinician` can create accounts from their respective auth pages.
- Login and signup are backed by FastAPI auth endpoints and PostgreSQL `user_accounts` table.
- Session cookies are stored in the frontend for route gating.
- Sign out clears session cookies and returns user to `/`.

Auth API endpoints:

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Role behavior:

- `patient` can upload check-ins.
- `clinician` can access clinician dashboard and storage download endpoints.
- For MVP, all clinician accounts can view all patient records.

## Run Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend health check:

```bash
curl http://localhost:8000/health
```

## Current API Endpoints (Mocked)

- `POST /api/v1/checkins/upload`
- `GET /api/v1/briefs/{patient_id}`

## Local PostgreSQL Setup

Create the local database:

```bash
createdb sessional
```

If PostgreSQL is not installed on macOS:

```bash
brew install postgresql@16
brew services start postgresql@16
createdb sessional
```

If `createdb` is not available, you can use Docker:

```bash
docker run --name sessional-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=sessional \
  -p 5432:5432 \
  -d postgres:16
```

Default backend DB URL:

```text
postgresql+psycopg://postgres:postgres@127.0.0.1:5432/sessional
```

Override with `.env` in `backend/`:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/sessional
```

### Verify Audio Persistence

After uploading from the patient UI:

```bash
psql postgresql://postgres:postgres@127.0.0.1:5432/sessional \
  -c "select id, file_name, mime_type, size_bytes, processing_status, created_at from audio_recordings order by created_at desc limit 5;"
```

## Notes

- Frontend upload target defaults to `http://localhost:8000`.
- Override with `NEXT_PUBLIC_API_BASE_URL` if needed.
- Uploaded audio is currently stored in PostgreSQL `audio_recordings.audio_data` (`bytea`) until we add post-processing deletion.
