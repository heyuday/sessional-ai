# Sessional MVP

Sessional is an asynchronous mental health check-in app where patients record short voice updates and clinicians review structured pre-session briefs.

## Current Implementation

- **Frontend**: Next.js App Router (`frontend/`)
  - Role-based entry flow (`/` -> patient or clinician auth)
  - Patient recording workflow: start, stop, resume, end, submit
  - Clinician dashboard and full brief pages powered by live backend data
- **Backend**: FastAPI (`backend/`)
  - Email/password auth with JWT and role checks
  - Audio upload to PostgreSQL (`bytea`)
  - Hume prosody extraction + Gemini synthesis pipeline (with fallback brief path)
  - Clinician brief list/detail/delete report APIs

## Main Routes

- `/` role chooser
- `/auth/patient` patient login/signup
- `/auth/clinician` clinician login/signup
- `/patient` patient check-in recorder
- `/clinician` clinician dashboard (real data)
- `/clinician/patients/[patientId]` full patient brief

## Core API Endpoints

- `POST /api/v1/auth/signup` (requires `full_name`, `email`, `password`, `role`)
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/checkins/upload` (patient-only)
- `GET /api/v1/checkins/storage/latest` (clinician-only)
- `GET /api/v1/checkins/storage/{recording_id}/download` (clinician-only)
- `GET /api/v1/briefs/patients` (clinician-only)
- `GET /api/v1/briefs/patients/{patient_id}` (clinician-only)
- `DELETE /api/v1/briefs/patients/{patient_id}/reports` (clinician-only)

## Local Setup

See `docs/setup.md` for complete installation, environment, and run instructions.
