# Production Deployment Guide

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

## 3. Environment Variables Reference

### Backend Environment Variables (`backend/.env`)

| Variable | Required? | Purpose | Safe Production Placeholder |
|---|---|---|---|
| `APP_ENV` | **Required** | Defines application environment (`production` or `development`). Affects error detail, CORS strictness, rate limits, and cookie security flags. | `production` |
| `SECRET_KEY` | **Required** | Secret key used for cryptographic signing and session operations. Must be at least 32 random characters. | `openssl rand -hex 32` (e.g., `4a7f9b2c8e1d3...`) |
| `JWT_SECRET` | **Required** | Secret key used for HMAC-SHA256 signing of short-lived access tokens. | `openssl rand -hex 32` (e.g., `8d2e1c9a4b5f0...`) |
| `DATABASE_URL` | **Required** | Pooled PostgreSQL connection string for application queries. | `postgresql+psycopg://neondb_owner:PASSWORD@ep-prod-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require` |
| `DATABASE_URL_DIRECT` | **Required** | Direct PostgreSQL connection string for Alembic schema migrations. | `postgresql+psycopg://neondb_owner:PASSWORD@ep-prod.ap-southeast-1.aws.neon.tech/neondb?sslmode=require` |
| `TEST_DATABASE_URL` | Optional | Neon test branch connection string. Required only when running integration test suite. | `postgresql+psycopg://neondb_owner:PASSWORD@ep-test.ap-southeast-1.aws.neon.tech/neondb?sslmode=require` |
| `GEMINI_API_KEY` | **Required** | API key for Google Gemini model generation and embeddings. | `AIzaSy...` (obtain from Google AI Studio) |
| `GEMINI_MODEL` | Optional | Gemini model identifier for scoring and feedback. Default: `gemini-2.5-flash`. | `gemini-2.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Optional | Embedding model for semantic resume similarity. Default: `text-embedding-004`. | `text-embedding-004` |
| `LLM_PROVIDER` | Optional | LLM provider implementation (`auto`, `gemini`, or `fake`). Must be `auto` or `gemini` in production. | `gemini` |
| `CORS_ORIGINS` | **Required** | Comma-separated list of trusted frontend origins. Never use `*` with credentials. | `https://placement-copilot.vercel.app` |
| `ENABLE_API_DOCS` | Optional | Toggle for `/docs`, `/redoc`, and `/openapi.json`. Recommended `false` for public production. | `false` |
| `LLM_DAILY_QUOTA` | Optional | Max daily LLM calls allowed per candidate. Default: `40`. | `40` |
| `MAX_UPLOAD_MB` | Optional | Max file size allowed for resume uploads. Default: `5`. | `5` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Access token lifetime in minutes. Default: `30`. | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Optional | Refresh token lifetime in days. Default: `7`. | `7` |

#### Cookie Settings in Production:
- Cookie Name: `refresh_token`
- `HttpOnly`: `True` (prevents JavaScript access, mitigating XSS token theft).
- `Secure`: `True` when `APP_ENV=production` (browser only transmits cookie over HTTPS).
- `SameSite`: `"none"` when `APP_ENV=production` (required for cross-site requests between frontend on Vercel and backend container); `"lax"` in development.
- `Path`: `/`
- Note: Cross-origin cookies with `SameSite=None` **require** `Secure=True` and HTTPS on both domains.

---

### Frontend Environment Variables (`frontend/.env`)

| Variable | Required? | Purpose | Safe Production Placeholder |
|---|---|---|---|
| `VITE_API_BASE_URL` | **Required** | Public HTTPS URL where the backend container is reachable. No trailing slash. | `https://api.placementcopilot.com` |
| `VITE_ENABLE_DEMO` | Optional | Whether the 1-click Demo Account login button is visible on the Auth page (`true` or `false`). | `true` (or `false` to disable) |

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
   - Inject environment variables securely via the hosting platform's secret manager (never bake secrets into Docker images).
   - Start container and verify container health check passes (`CMD curl -f http://localhost:8000/api/v1/health || exit 1`).
4. **Verify Health Endpoints**:
   - Check general API health:
     ```bash
     curl -i https://<backend-host>/api/v1/health
     # Expected HTTP 200: {"status":"ok","app":"Placement Copilot","version":"0.1.0"}
     ```
   - Check database connectivity through pooler:
     ```bash
     curl -i https://<backend-host>/api/v1/health/db
     # Expected HTTP 200: {"status":"ok","db":"connected"}
     ```
5. **Deploy Frontend**:
   - Deploy React/Vite application to Vercel with `VITE_API_BASE_URL` pointing to the live backend URL.
   - Ensure Vercel project has SPA rewrite rules configured for React Router (`/* -> /index.html`).
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

## 6. Production Safety Audit & Known Gaps

A static and runtime audit of the backend codebase with placeholder configuration and `APP_ENV=production` identified the following behaviors and gaps:

### Verified Safety Mechanisms
- **Fake LLM Block in Production**: `app.main:lifespan` verifies `settings.APP_ENV == "production" and settings.LLM_PROVIDER.lower() == "fake"`, raising a hard `RuntimeError` during startup to prevent silent fallback to fake responses in production.
- **Degraded Database Mode**: If the database connection cannot be established at startup, `lifespan` catches the exception and logs an error, keeping `/api/v1/health` responsive while `/api/v1/health/db` accurately returns `unhealthy`.
- **Argon2 Password Hashing**: Passwords are securely hashed with Argon2id parameters via `pwdlib`.
- **Token Family Revocation**: Refresh tokens use family IDs (`family_id`). If an already-rotated token is reused outside the 10-second race-condition grace window, the entire family is revoked.

### Known Gaps (Missing Guards)
1. **Default Secrets Guard**:
   - `SECRET_KEY` and `JWT_SECRET` in `backend/app/core/config.py` have default fallback values (`"dev-secret-key-at-least-32-chars-long!"` and `"dev-jwt-secret-at-least-32-chars-long!"`).
   - *Gap*: The backend does not raise an exception if `APP_ENV=production` is set but the default secret keys are left unchanged. Production operators must manually ensure high-entropy random keys are configured.
2. **Wildcard CORS with Credentials Guard**:
   - `backend/app/main.py` attaches `CORSMiddleware` with `allow_origins=settings.CORS_ORIGINS` and `allow_credentials=True`.
   - *Gap*: There is no validator disallowing `CORS_ORIGINS="*"` when `APP_ENV=production`. Because browsers disallow wildcard origins when `credentials: 'include'` is used, setting `*` will break authentication in production. Operators must explicitly set exact origin URLs.
3. **API Docs Default Exposure**:
   - `ENABLE_API_DOCS` defaults to `True` in `backend/app/core/config.py`.
   - *Gap*: Unless explicitly set to `ENABLE_API_DOCS=false` in the production environment, `/docs`, `/redoc`, and `/openapi.json` remain accessible on the production domain.
4. **Cross-Origin Cookie Requirement (HTTPS)**:
   - In production (`APP_ENV=production`), `_set_refresh_cookie` in `app/api/v1/auth.py` sets `SameSite="none"` and `Secure=True`.
   - *Operational Requirement*: Both frontend and backend domains must use valid HTTPS certificates, or modern browsers will reject the refresh token cookie.

---

## 7. Docker Build & Container Verification

- **Host Environment Check**: Docker is currently **not installed** on this host (`which docker` returned non-zero).
- **Image Specification**: `backend/Dockerfile` defines a multi-stage Python 3.12-slim build with non-root installation, system dependencies (`build-essential`, `libpq-dev`, `curl`), health check configuration (`curl -f http://localhost:8000/api/v1/health`), and parameter injection via runtime environment variables (`--env-file backend/.env`). Secrets are never copied or baked into the image.
