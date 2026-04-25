# Sessional Tech Stack

This document lists the current implementation stack for the local MVP.

## Frontend

- **Framework**: Next.js (App Router) + React + TypeScript
- **Styling**: Tailwind CSS
- **Audio capture**: Browser `MediaRecorder` API (multi-step flow: start/stop/resume/end/submit)
- **Routing/Auth gating**: Next.js middleware (`proxy.ts`) with role-aware session cookies
- **Data layer**: Fetch-based API client in `frontend/lib/api.ts`

## Backend

- **Framework**: FastAPI (Python)
- **Validation/serialization**: Pydantic
- **ORM/DB access**: SQLAlchemy + psycopg
- **Auth/Security**:
  - Email/password login/signup
  - JWT access tokens
  - Password hashing via `pbkdf2_sha256` (passlib)
  - Role-based route protection (`patient`, `clinician`)

## Data & Storage

- **Database**: PostgreSQL (local-first MVP)
- **Audio storage**: `audio_recordings.audio_data` (`bytea`)
- **Core tables**:
  - `user_accounts` (identity + role + full name)
  - `audio_recordings` (audio blob + generated brief fields)

## AI / Signal Processing

- **Affective extraction**: Hume AI batch inference
  - `prosody` model (vocal affect)
  - `language` sentiment model (semantic sentiment)
  - utterance-level timing and top emotion scores
- **Synthesis LLM**: Gemini (`gemini-2.5-flash` by default)
  - structured JSON output via response schema
  - explicit system instruction + deterministic generation configuration
- **Divergence logic**:
  - compares semantic sentiment with negative-valence prosody
  - emits evidence-backed divergence candidates and summary context
- **Guardrails**:
  - post-validation repair of generated brief output
  - snippet normalization for short/fragment divergence clips
  - basic hallucination mitigation and schema enforcement

## Clinician Brief UX Semantics

- `summary`: theme-focused 60-second snapshot
- `clinical_summary`: richer clinician rationale
- `divergence_moments`: timestamped mismatch events with severity/confidence
- `trends`: computed by comparing latest and previous check-ins

## Local Dev Tooling

- **Frontend tooling**: npm scripts, ESLint
- **Backend tooling**: pytest + lightweight compile checks
- **Runtime**: local services (Next.js + FastAPI + PostgreSQL), no deployment required for MVP
