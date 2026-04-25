# Sessional Setup

This document explains how to install dependencies and run the current local MVP.

## Prerequisites

- Node.js 20+
- Python 3.11+ (a local venv is already scaffolded under `backend/.venv`)
- PostgreSQL 15+ running locally

## Project Structure

- `frontend`: Next.js (App Router) patient + clinician UI
- `backend`: FastAPI API with auth, audio upload, Hume/Gemini processing, and clinician brief endpoints

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
npm run dev -- --hostname 127.0.0.1 --port 3000
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
- Signup requires a `full_name` field.
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

## Current API Endpoints

- `POST /api/v1/checkins/upload`
- `GET /api/v1/checkins/storage/latest`
- `GET /api/v1/checkins/storage/{recording_id}/download`
- `GET /api/v1/briefs/patients`
- `GET /api/v1/briefs/patients/{patient_id}`
- `DELETE /api/v1/briefs/patients/{patient_id}/reports`

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
PROCESSING_MODE=mock
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
HUME_API_KEY=your_key_here
HUME_BASE_URL=https://api.hume.ai
HUME_TIMEOUT_SECONDS=60
HUME_POLL_INTERVAL_SECONDS=3
HUME_MAX_WAIT_SECONDS=180
HUME_PROSODY_GRANULARITY=utterance
JWT_SECRET_KEY=replace-with-random-secret
```

Notes:

- `PROCESSING_MODE=real` uses Hume + Gemini.
- `PROCESSING_MODE=mock` bypasses external model calls for stable local UI demos.
- Real mode now uses:
  - Hume `prosody` + `language` sentiment at utterance granularity
  - top-6 emotion context + utterance duration
  - divergence candidates based on semantic sentiment vs negative-valence prosody
  - Gemini systemInstruction + deterministic generation config

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
- If external model processing fails in real mode, upload still returns `200` with a fallback brief and records `processed_fallback`.
- Clinician dashboard and full brief pages now use live backend data rather than frontend mock data.
- 60-second snapshot (`summary`) is theme-focused and intentionally avoids explicit divergence wording.
- `clinical_summary` is a separate clinician-facing rationale and includes divergence count context.
- Divergence timeline snippets are normalized to fuller utterance context when model output is too fragmentary.
- Trends are computed against the patient's prior check-in:
  - risk direction uses `Green < Yellow < Red`
  - divergence frequency uses divergence-moment count deltas
  - divergence intensity uses weighted severity-confidence deltas

## Optional Local Reset

To clear all local users and reports for a fresh demo:

```bash
psql "postgresql://postgres:postgres@127.0.0.1:5432/sessional" \
  -c "DELETE FROM audio_recordings; DELETE FROM user_accounts;"
```
