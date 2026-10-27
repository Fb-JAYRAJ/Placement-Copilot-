# Production Deployment Guide

> [!IMPORTANT]
> **Deployment Status**: The project is **not deployed yet**. The configurations, deployment sequence, and verification steps in this guide serve as the validated release runbook for upcoming staging and production rollouts.

This document details the production architecture, configuration, deployment sequence, post-deployment smoke tests, and production safety audit for Placement Copilot.

---

## 1. Target Architecture & Infrastructure Layout

- **Frontend**: Hosted on [Vercel](https://vercel.com) (static SPA edge distribution, client-side routing via React Router).
- **Backend**: Containerized FastAPI service running on a container host (e.g., AWS ECS, Render, Fly.io, or Railway) provisioned in **Singapore (`ap-southeast-1`)** to ensure minimal latency to the Neon database instance.
- **Database**: [Neon](https://neon.tech) Serverless PostgreSQL located in `ap-southeast-1` (Singapore, AWS).
- **AI / LLM Services**: Google AI Studio Gemini API (`gemini-2.5-flash` for evaluation and `text-embedding-004` for vector embeddings).

```mermaid
flowchart LR
    User["Candidate Browser"] -->|HTTPS| Vercel["Vercel Edge (Frontend SPA)"]
    User -->|"HTTPS + JWT / HttpOnly Cookie"| Backend["FastAPI Container (ap-southeast-1)"]
    Backend -->|"Pooled (pgbouncer :6543)"| NeonPool["Neon Postgres Production"]
    Alembic["Alembic Migration Step"] -->|"Direct Session (:5432)"| NeonDirect["Neon Postgres Direct"]
    Backend -.->|"HTTPS REST"| Gemini["Google Gemini API"]
```

---

## 2. Neon Database Configuration & Rules

1. **Branch Management**:
   - Use the **default production branch** (typically `main`) for production workloads.
   - **CRITICAL**: Production branches in Neon must **never** have auto-delete enabled (keep branch protection / deletion protection active).
2. **Dual Connection Endpoints**:
   - `DATABASE_URL`: Must use the **pooled** connection string (typically containing `-pooler.` and port `5432` or `6543`) with SQLAlchemy psycopg driver format: `postgresql+psycopg://<user>:<password>@<endpoint>-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`. Used by application transactions to scale concurrent connections via PgBouncer.
   - `DATABASE_URL_DIRECT`: Must use the **direct** connection string (without `-pooler.`) with driver format: `postgresql+psycopg://<user>:<password>@<endpoint>.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`. Required by Alembic migrations because DDL statements, locks, and schema migrations require native session state.
3. **Data Seeding in Production**:
   - `python scripts/seed.py`: Run once on initial deployment to populate static reference data (skills taxonomy, 140+ DSA catalog problems, interview question bank).
   - `python scripts/seed_demo.py`: **Only run on purpose** if a public demo account (`demo@placementcopilot.com`) is explicitly desired in that environment. Do not run on isolated enterprise or private production databases.

---

## 3. Environment Variables & Cookie Setups

### Backend Environment Variables (`backend/.env`)

| Variable | Required? | Purpose | Safe Production Placeholder |
|---|---|---|---|
| `APP_ENV` | **Required** | Defines application environment (`production` or `development`). Affects error detail, CORS strictness, rate limits, docs, and cookie defaults. | `production` |
| `SECRET_KEY` | **Required** | Cryptographic signing key (>=32 chars). Blocked at startup if dev default or <32 chars. | `openssl rand -hex 32` (e.g., `4a7f9b2c8e1d3...`) |
| `JWT_SECRET` | **Required** | HMAC-SHA256 signing key for access tokens (>=32 chars). Blocked at startup if dev default or <32 chars. | `openssl rand -hex 32` (e.g., `8d2e1c9a4b5f0...`) |
| `DATABASE_URL` | **Required** | Pooled PostgreSQL string. Blocked if pointing to localhost in production. | `postgresql+psycopg://neondb_owner:PASSWORD@ep-prod-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require` |
| `DATABASE_URL_DIRECT` | **Required** | Direct PostgreSQL string. Blocked if pointing to localhost in production. | `postgresql+psycopg://neondb_owner:PASSWORD@ep-prod.ap-southeast-1.aws.neon.tech/neondb?sslmode=require` |
| `TEST_DATABASE_URL` | Optional | Neon test branch connection string. Required only when running integration tests. | `postgresql+psycopg://neondb_owner:PASSWORD@ep-test.ap-southeast-1.aws.neon.tech/neondb?sslmode=require` |
| `GEMINI_API_KEY` | **Required** | API key for Google Gemini model generation and embeddings. Blocked if empty in production. | `AIzaSy...` (obtain from Google AI Studio) |
| `GEMINI_MODEL` | Optional | Gemini model identifier for scoring and feedback. Default: `gemini-2.5-flash`. | `gemini-2.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Optional | Embedding model for semantic resume similarity. Default: `text-embedding-004`. | `text-embedding-004` |
| `LLM_PROVIDER` | Optional | Provider implementation (`auto`, `gemini`, or `fake`). Blocked if `fake` in production. | `gemini` |
| `CORS_ORIGINS` | **Required** | Comma-separated list of origins. Blocked if containing `*` or insecure `http://` in production. | `https://placement-copilot.vercel.app` |
| `ENABLE_API_DOCS` | Optional | Toggle for `/docs`, `/redoc`, and `/openapi.json`. Defaults to `false` in production, `true` in dev. | `false` |
| `COOKIE_SAMESITE` | Optional | SameSite attribute for refresh cookie (`none`, `lax`, or `strict`). Defaults to `none` in prod, `lax` in dev. | `none` (or `lax` if reverse-proxied) |
| `COOKIE_SECURE` | Optional | Secure flag for refresh cookie (`true` or `false`). Defaults to `true` in prod, `false` in dev. | `true` |
| `LLM_DAILY_QUOTA` | Optional | Max daily LLM calls per candidate. Default: `40`. | `40` |
| `MAX_UPLOAD_MB` | Optional | Max file size for resume uploads. Default: `5`. | `5` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Access token lifetime in minutes. Default: `30`. | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Optional | Refresh token lifetime in days. Default: `7`. | `7` |

---

### Frontend Environment Variables (`frontend/.env`)

| Variable | Required? | Purpose | Safe Production Placeholder |
|---|---|---|---|
| `VITE_API_BASE_URL` | **Required\*** | Backend API base URL (no trailing slash). \*Empty if using Vercel same-domain proxy. | `https://api.placementcopilot.com` |
| `VITE_ENABLE_DEMO` | Optional | Controls visibility of 1-click Demo Account login button (`true` or `false`, default: `true`). | `true` |

---

### Cookie Architecture Options

Placement Copilot supports two distinct cookie topologies:

#### Option A: Cross-Domain Architecture (Separate API Domain)
- **Frontend**: `https://placement-copilot.vercel.app`
- **Backend API**: `https://api.placementcopilot.com`
- **Configuration**:
  - Backend: `COOKIE_SAMESITE=none`, `COOKIE_SECURE=true`, `CORS_ORIGINS=https://placement-copilot.vercel.app`
  - Frontend: `VITE_API_BASE_URL=https://api.placementcopilot.com`
- **Requirements**:
  - Both domains must have valid SSL/TLS certificates (HTTPS). Modern browsers strictly reject `SameSite=None` over insecure HTTP.
  - Startup check: The backend logs a startup warning if `SameSite=None` is configured without an `https://` origin in `CORS_ORIGINS`.

#### Option B: Same-Domain Proxy via Vercel Rewrites (Recommended for ITP Resistance)
- **Frontend & API**: Served together under `https://placement-copilot.vercel.app`
- **Vercel Rewrite (`vercel.json`)**:
  ```json
  {
    "rewrites": [
      {
        "source": "/api/:path*",
        "destination": "https://api.placementcopilot.com/api/:path*"
      },
      {
        "source": "/(.*)",
        "destination": "/index.html"
      }
    ]
  }
  ```
- **Configuration**:
  - Backend: `COOKIE_SAMESITE=lax`, `COOKIE_SECURE=true`, `CORS_ORIGINS=https://placement-copilot.vercel.app`
  - Frontend: `VITE_API_BASE_URL=""` (empty string so requests use relative paths `/api/v1/...`)
- **Benefits**:
  - First-party cookie semantics (`SameSite=Lax`), preventing Safari Intelligent Tracking Prevention (ITP) issues and third-party cookie blocking.

---

## 4. Release Order & Execution Procedure

To prevent downtime and ensure database schema compatibility, execute production releases in the following strict order:

1. **Pre-flight & Database Migrations**:
   Run schema migrations using the direct database connection before updating running application containers:
   ```bash
   alembic upgrade head
   ```
2. **Initial Reference Data Seeding (First deployment only)**:
   ```bash
   python scripts/seed.py
   # Optional: only if demo candidate is desired
   python scripts/seed_demo.py
   ```
3. **Deploy Backend Service**:
   - Build container image from `backend/Dockerfile`.
   - Inject environment variables securely via hosting platform secrets (never bake secrets into Docker images).
   - Verify container health check passes (`CMD curl -f http://localhost:8000/api/v1/health || exit 1`).
4. **Verify Health Endpoints**:
   - General API health:
     ```bash
     curl -i https://<backend-host>/api/v1/health
     # Expected HTTP 200: {"status":"ok","app":"Placement Copilot","version":"0.1.0"}
     ```
   - Database connectivity through pooler:
     ```bash
     curl -i https://<backend-host>/api/v1/health/db
     # Expected HTTP 200: {"status":"ok","db":"connected"}
     ```
5. **Deploy Frontend**:
   - Deploy React/Vite application to Vercel with appropriate `VITE_API_BASE_URL`.
   - Verify SPA rewrite rules in `vercel.json`.
6. **Execute Smoke Tests**:
   - Perform the end-to-end verification checklist below.

---

## 5. Post-Deployment Smoke-Test Checklist

Verify the following primary user journeys against the production environment:

- [ ] **1. Authentication & Session Persistence**:
  - Click Demo Sign In (or register a new user at `/signup`).
  - Verify redirection to Dashboard `/` with user greeting.
  - Hard refresh the page (`Cmd+Shift+R` / `Ctrl+F5`) and confirm session is restored transparently via the refresh cookie without logging out.
- [ ] **2. Route Traversal & Console Cleanliness**:
  - Navigate to `/dsa`, `/resume`, `/interview`, `/profile`, and back to `/`.
  - Confirm browser DevTools console has zero unhandled exceptions or 4xx/5xx network errors.
- [ ] **3. DSA Logging & Mastery Recalculation**:
  - Open `/dsa`, click **Log New Problem**, enter a custom problem title, select a topic, and submit.
  - Confirm the new problem appears in the recent attempts table and topic mastery bars reflect the updated evidence.
- [ ] **4. Resume ATS Alignment Scoring**:
  - Navigate to `/resume`, enter sample resume text (or upload a PDF/DOCX), enter a sample Job Description, and click **Run ATS Alignment Analysis**.
  - Verify overall match score, breakdown bars (Keyword, TF-IDF, Semantic, Quality), and missing skills appear.
- [ ] **5. Adaptive Mock Interview Cycle**:
  - Navigate to `/interview`, click **Start Interview Session**.
  - Answer question 1 and verify response evaluation is returned with dimension scores and next question.
  - Complete the session and confirm the final Performance Audit report displays ability trajectory.
- [ ] **6. Candidate Intelligence Dashboard**:
  - Verify the Readiness gauge reflects combined metrics, top 3 action levers are displayed, and activity feed contains recent events.
- [ ] **7. Logout Flow**:
  - Click logout in the navigation sidebar.
  - Verify cookies/tokens are cleared and client is redirected to `/login`.

---

## 6. Production Safety Audit & Resolved Guards

All identified safety gaps have been hardened with strict startup validation guards and covered by automated unit tests in `backend/tests/unit/test_production_guards.py`:

| Guard / Gap | Status | Implementation Details | Unit Test Coverage |
|---|---|---|---|
| **Default & Short Secrets Guard** | **Resolved** | Rejects startup if `SECRET_KEY` or `JWT_SECRET` uses known dev defaults or is <32 characters when `APP_ENV=production`. | `test_guard_secret_key_default`<br>`test_guard_secret_key_short`<br>`test_guard_jwt_secret_default`<br>`test_guard_jwt_secret_short` |
| **Wildcard & Insecure CORS Guard** | **Resolved** | Rejects startup if `CORS_ORIGINS` contains wildcard `*` or insecure `http://` origins in production. | `test_guard_cors_wildcard`<br>`test_guard_cors_http` |
| **Fake LLM Provider Guard** | **Resolved** | Rejects startup if `LLM_PROVIDER="fake"` when `APP_ENV=production`. | `test_guard_llm_provider_fake` |
| **Localhost Database Guard** | **Resolved** | Rejects startup if `DATABASE_URL` or `DATABASE_URL_DIRECT` points to `localhost` or `127.0.0.1` in production. | `test_guard_database_url_localhost`<br>`test_guard_database_url_direct_localhost` |
| **Missing Gemini API Key Guard** | **Resolved** | Rejects startup if `GEMINI_API_KEY` is empty or whitespace in production. | `test_guard_gemini_api_key_empty` |
| **API Documentation Exposure** | **Resolved** | `ENABLE_API_DOCS` defaults to `false` in production and `true` in development. Can be explicitly enabled if needed. | `test_enable_api_docs_defaults` |
| **Configurable Cookie Security** | **Resolved** | `COOKIE_SAMESITE` (`none` in prod, `lax` in dev) and `COOKIE_SECURE` (`true` in prod, `false` in dev) are configurable via env. | `test_cookie_settings_defaults_and_overrides` |
| **SameSite=None without HTTPS Warning** | **Resolved** | Logs a warning during startup if `COOKIE_SAMESITE="none"` is configured without an HTTPS origin in `CORS_ORIGINS`. | `test_cookie_samesite_none_without_https_warning` |
| **Non-Production Immunity** | **Resolved** | Ensures none of the strict production guards block startup in development (`APP_ENV=development`). | `test_dev_mode_allows_dev_settings` |

---

## 7. Docker Build & Container Verification

- **Host Environment Check**: Docker is currently **not installed** on this local host (`which docker` returned non-zero).
- **Image Specification**: `backend/Dockerfile` defines a multi-stage Python 3.12-slim build with non-root installation, system dependencies (`build-essential`, `libpq-dev`, `curl`), health check configuration (`curl -f http://localhost:8000/api/v1/health`), and parameter injection via runtime environment variables (`--env-file backend/.env`). Secrets are never copied or baked into the image.
