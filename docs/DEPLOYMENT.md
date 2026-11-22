# Production Deployment Guide

> [!NOTE]
> **Deployment status: live (November 2026).**
> Frontend: https://placement-copilot-nine.vercel.app · Backend API: https://placement-copilot-morn.onrender.com · Database: Neon `production` branch.

This document details the production architecture, configuration, deployment sequence, post-deployment smoke tests, measured results, operations notes and the production safety audit for Placement Copilot.

---

## 1. Target Architecture & Infrastructure Layout

- **Frontend**: Hosted on [Vercel](https://vercel.com) (static SPA build of `frontend/`, client-side routing via React Router). A Vercel rewrite forwards `/api/*` to the backend so the browser only ever talks to the Vercel domain.
- **Backend**: Containerized FastAPI service on a **Render free web service** (Docker runtime). Choose the region closest to the Neon database (Singapore) and confirm it in the Render dashboard. See section 7.5 for the settings and free-tier caveats.
- **Database**: [Neon](https://neon.tech) Serverless PostgreSQL in `ap-southeast-1` (Singapore, AWS). The `production` branch holds reference data only: no demo user, and no users until real people sign up.
- **AI / LLM Services**: Google AI Studio Gemini API: `gemini-3.1-flash-lite` (primary), `gemini-3.5-flash` (automatic fallback) and `gemini-embedding-001` (embeddings).
  - Google retires models over time. `gemini-3.1-flash-lite` had a published shutdown date of 7 May 2027 when this guide was written, so plan to move to a newer model before then. It is only an environment variable change (`GEMINI_MODEL`).
  - Not suitable as backend hosts: Vercel serverless functions (dependency size) and Hugging Face Spaces (outbound traffic is restricted to ports 80, 443 and 8080, so Neon on port 5432 is unreachable).

```mermaid
flowchart LR
    User["Candidate Browser"] -->|HTTPS| Vercel["Vercel (SPA + /api rewrite)"]
    Vercel -->|"/api/* rewrite"| Backend["FastAPI container on Render"]
    Backend -->|"Pooled (pgbouncer)"| NeonPool["Neon Postgres Production"]
    Alembic["Alembic + seed scripts (run from a laptop)"] -->|"Direct session"| NeonDirect["Neon Postgres Direct"]
    Backend -.->|"HTTPS REST"| Gemini["Google Gemini API"]
```

---

## 2. Neon Database Configuration & Rules

1. **Branch Management**:
   - Use the **default production branch** for production workloads. Create it as a fresh, empty branch. **Do not** create it by branching from `dev`, or the dev users would come along.
   - **CRITICAL**: When creating any branch in the Neon console, untick the pre-ticked "Automatically delete branch after" option. Production branches must **never** have auto-delete enabled.
2. **Dual Connection Endpoints**:
   - `DATABASE_URL`: Must use the **pooled** connection string (containing `-pooler.`) with the SQLAlchemy psycopg driver format: `postgresql+psycopg://<user>:<password>@<endpoint>-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`. Used by application transactions to scale concurrent connections via PgBouncer.
   - `DATABASE_URL_DIRECT`: Must use the **direct** connection string (without `-pooler.`) with driver format: `postgresql+psycopg://<user>:<password>@<endpoint>.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`. Required by Alembic migrations because DDL statements, locks, and schema migrations require native session state. In the Neon console, turn **Connection pooling off** to copy it.
3. **Data Seeding in Production**:
   - `python scripts/seed.py`: Run once on initial deployment to populate static reference data (20 DSA topics, 142 catalog problems, 150 interview questions). It creates no users. The skills taxonomy is a JSON file inside the app, not a table.
   - `python scripts/seed_demo.py`: **Never run on production.** It is a local-development helper only. The production database must contain no users until real people sign up.

---

## 3. Environment Variables & Cookie Setups

### Backend Environment Variables (`backend/.env` locally, Render environment settings in production)

| Variable | Required? | Purpose | Safe Production Placeholder |
|---|---|---|---|
| `APP_ENV` | **Required** | Defines application environment (`production` or `development`). Affects error detail, CORS strictness, rate limits, docs, and cookie defaults. | `production` |
| `SECRET_KEY` | **Required** | Cryptographic signing key (>=32 chars). Blocked at startup if dev default or <32 chars. | `openssl rand -hex 32` |
| `JWT_SECRET` | **Required** | HMAC-SHA256 signing key for access tokens (>=32 chars). Blocked at startup if dev default or <32 chars. | `openssl rand -hex 32` |
| `DATABASE_URL` | **Required** | Pooled PostgreSQL string. Blocked if pointing to localhost in production. | `postgresql+psycopg://neondb_owner:PASSWORD@ep-prod-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require` |
| `DATABASE_URL_DIRECT` | **Required** | Direct PostgreSQL string. Blocked if pointing to localhost in production. | `postgresql+psycopg://neondb_owner:PASSWORD@ep-prod.ap-southeast-1.aws.neon.tech/neondb?sslmode=require` |
| `TEST_DATABASE_URL` | Optional | Neon test branch connection string. Required only when running integration tests. Do not set it in production. | (unset) |
| `GEMINI_API_KEY` | **Required** | API key for Google Gemini generation and embeddings. Blocked if empty in production. | `AIzaSy...` (from Google AI Studio) |
| `GEMINI_MODEL` | Optional | Primary Gemini model for suggestions, questions and answer judging. Default: `gemini-3.1-flash-lite`. | `gemini-3.1-flash-lite` |
| `GEMINI_FALLBACK_MODEL` | Optional | Model tried automatically when the primary fails or times out. Default: `gemini-3.5-flash`. | `gemini-3.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Optional | Embedding model for semantic resume similarity. Default: `gemini-embedding-001`. | `gemini-embedding-001` |
| `LLM_ATTEMPT_TIMEOUT_SECONDS` | Optional | Time limit for one Gemini request (one generation attempt or one embedding batch). Default: `8`. | `8` |
| `LLM_TIMEOUT_SECONDS` | Optional | Total time budget for one generation call across all attempts and models. Default: `25`. | `25` |
| `LLM_THINKING_BUDGET` | Optional | `0` turns Gemini "thinking" off (much faster for short schema-bound JSON). `-1` keeps the model default. Default: `0`. | `0` |
| `LLM_PROVIDER` | Optional | Provider implementation (`auto`, `gemini`, or `fake`). Blocked if `fake` in production. | `gemini` |
| `CORS_ORIGINS` | **Required** | Comma-separated list of origins. Blocked if containing `*` or insecure `http://` in production. | `https://placement-copilot-nine.vercel.app` |
| `ENABLE_API_DOCS` | Optional | Toggle for `/docs`, `/redoc`, and `/openapi.json`. Defaults to `false` in production, `true` in dev. | `false` |
| `COOKIE_SAMESITE` | Optional | SameSite attribute for the refresh cookie (`none`, `lax`, or `strict`). Defaults to `none` in prod, `lax` in dev. Use `lax` with the Vercel rewrite. | `lax` |
| `COOKIE_SECURE` | Optional | Secure flag for the refresh cookie (`true` or `false`). Defaults to `true` in prod, `false` in dev. | `true` |
| `LLM_DAILY_QUOTA` | Optional | Max daily LLM calls per candidate. Default: `40`. | `40` |
| `LLM_GLOBAL_DAILY_LIMIT` | Optional | Max daily LLM calls across all users combined. Default: `300`. Keep it below your Gemini project's own daily request limit (see section 9). | `300` |
| `REGISTER_RATE_LIMIT` | Optional | Per-IP rate limit on `POST /auth/register` in production. Default: `5/hour` (in dev: `1000/hour`). | `5/hour` |
| `ALLOW_SIGNUP` | Optional | Global toggle for new candidate signups (`true` or `false`). Returns 403 when false. Keep it `true`: there is no demo account, so signup is the only way in. | `true` |
| `MAX_UPLOAD_MB` | Optional | Max file size for resume uploads. Default: `5`. | `5` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Access token lifetime in minutes. Default: `30`. | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Optional | Refresh token lifetime in days. Default: `7`. | `7` |

> [!NOTE]
> `DEMO_EMAIL` and `DEMO_LLM_DAILY_QUOTA` are legacy settings for the local demo seed. Leave them unset in production: no demo user exists there, so they have no effect.

---

### Frontend Environment Variables (`frontend/.env` locally, Vercel project settings in production)

| Variable | Required? | Purpose | Production value |
|---|---|---|---|
| `VITE_API_BASE_URL` | Leave **unset** | Backend API base URL. Leave it unset or empty when using the Vercel same-domain proxy, so the app calls relative `/api/v1/...` paths. | (unset) |
| `VITE_SITE_URL` | Optional | Canonical production URL used for Open Graph and Twitter preview metadata (no trailing slash). | `https://placement-copilot-nine.vercel.app` |

> [!IMPORTANT]
> `VITE_SITE_URL` is baked into the page at **build time**. After changing it you must **redeploy** (Vercel: Deployments, then the menu on the newest deployment, then Redeploy). In Vercel, create it with Type **Config**, not Secret: `VITE_` variables are public by design, and Vercel warns about public-prefixed Secrets. A saved Secret cannot be converted, so delete it and add it again.

---

### Cookie Architecture Options

Placement Copilot supports two distinct cookie topologies:

#### Option A: Cross-Domain Architecture (Separate API Domain)
- **Frontend**: a Vercel domain.
- **Backend API**: a separate HTTPS domain.
- **Configuration**:
  - Backend: `COOKIE_SAMESITE=none`, `COOKIE_SECURE=true`, `CORS_ORIGINS=<frontend https origin>`
  - Frontend: `VITE_API_BASE_URL=<backend https URL>`
- **Requirements**:
  - Both domains must have valid SSL/TLS certificates (HTTPS). Modern browsers strictly reject `SameSite=None` over insecure HTTP.
  - Startup check: the backend logs a startup warning if `SameSite=None` is configured without an `https://` origin in `CORS_ORIGINS`.
  - Safari blocks cross-site cookies, so sessions may not persist there. This is why Option B is preferred.

#### Option B: Same-Domain Proxy via Vercel Rewrites (In use)
- **Frontend & API**: Served together under `https://placement-copilot-nine.vercel.app`
- **Vercel Rewrite (`frontend/vercel.json`)**: the `/api` rule comes **before** the single-page-app fallback:
  ```json
  {
    "rewrites": [
      {
        "source": "/api/:path*",
        "destination": "https://placement-copilot-morn.onrender.com/api/:path*"
      },
      {
        "source": "/(.*)",
        "destination": "/index.html"
      }
    ]
  }
  ```
- **Configuration**:
  - Backend: `COOKIE_SAMESITE=lax`, `COOKIE_SECURE=true`, `CORS_ORIGINS=https://placement-copilot-nine.vercel.app`
  - Frontend: `VITE_API_BASE_URL` unset (so requests use relative paths `/api/v1/...`)
- **Benefits**:
  - First-party cookie semantics (`SameSite=Lax`), avoiding Safari Intelligent Tracking Prevention (ITP) issues and third-party cookie blocking. The refresh cookie is set with `path=/` and no domain, so it becomes a first-party cookie on the Vercel domain.
- **Proxy time limit**: Vercel's documentation was not consistent about the proxy timeout when this was written (some pages said 30 seconds, newer ones 120). A cold backend start through the proxy took 38.8 seconds and succeeded (see section 5), which fits the 120-second figure.

---

## 4. Release Order & Execution Procedure

The first production release was executed in this order:

1. **Create the empty Neon `production` branch** (see section 2) and copy its pooled and direct connection strings.
2. **Migrate and seed reference data from your laptop.** Enter the production direct string without it touching shell history or the terminal screen. The safest way is a small script file that reads it with a hidden prompt, refuses to continue if the host is pooled or equals the dev database host, refuses if the target database already has tables, runs `alembic upgrade head`, then `python scripts/seed.py`, and finally prints row counts. The result must show `users` = 0. Do **not** run `scripts/seed_demo.py`. Use the same approach for any later migration.
3. **Deploy Backend Service** on Render (section 7.5).
4. **Verify Health Endpoints**:
   - General API health:
     ```bash
     curl -i https://placement-copilot-morn.onrender.com/api/v1/health
     # Expected HTTP 200: {"status":"ok", ...}
     ```
   - Database connectivity through the pooler:
     ```bash
     curl -i https://placement-copilot-morn.onrender.com/api/v1/health/db
     # Expected HTTP 200: {"status":"ok","db":"connected"}
     ```
5. **Deploy Frontend** on Vercel (section 7.6), then set `CORS_ORIGINS` on Render to the real Vercel URL.
6. **Execute Smoke Tests**: perform the checklist below.

For later releases: push to `main`. Render and Vercel both redeploy automatically. Run `alembic upgrade head` from your laptop first if the change includes a migration (Render's pre-deploy command is not available on the free plan).

---

## 5. Post-Deployment Smoke-Test Checklist

Verify the following primary user journeys against the production environment. Production limits signups to 5 per hour per IP, so register one test user and reuse it. Delete test accounts from **Profile** afterwards.

- [ ] **1. Authentication & Session Persistence**:
  - Register a new user at `/signup` (there is no demo account).
  - Verify redirection to the Dashboard `/` and the onboarding checklist.
  - Hard refresh the page (`Cmd+Shift+R` / `Ctrl+F5`) and confirm the session is restored transparently via the refresh cookie without logging out.
- [ ] **2. Route Traversal & Console Cleanliness**:
  - Navigate to `/dsa`, `/resume`, `/interview`, `/profile`, and back to `/`.
  - Confirm the browser DevTools console has zero unhandled exceptions or 4xx/5xx network errors.
- [ ] **3. DSA Logging & Mastery Recalculation**:
  - Open `/dsa`, click **Log New Problem**, enter a custom problem title, select a topic, and submit.
  - Confirm the new problem appears in the recent attempts table and topic mastery bars reflect the updated evidence.
- [ ] **4. Resume ATS Alignment Scoring**:
  - Navigate to `/resume`, enter sample resume text (or upload a PDF/DOCX), enter a sample Job Description, and click **Run ATS Alignment Analysis**.
  - Verify the overall match score, breakdown bars (Keyword, TF-IDF, Semantic, Quality) and missing skills appear, and that the result is **not** flagged as degraded.
- [ ] **5. Adaptive Mock Interview Cycle**:
  - Navigate to `/interview`, click **Start Interview Session**.
  - Answer question 1 and verify the evaluation is returned with dimension scores and the next question, without a timeout through the Vercel proxy.
  - Complete the session and confirm the final Performance Audit report displays the ability trajectory.
- [ ] **6. Candidate Intelligence Dashboard**:
  - Verify the Readiness gauge reflects combined metrics, top 3 action levers are displayed, and the activity feed contains recent events.
- [ ] **7. Logout Flow**:
  - Click logout in the navigation sidebar.
  - Verify cookies/tokens are cleared and the client is redirected to `/login`.
- [ ] **8. Cold Start**:
  - After 15+ minutes idle, call `curl -s -o /dev/null -w "%{http_code} in %{time_total}s\n" https://placement-copilot-nine.vercel.app/api/v1/health` and note the time. The browser should show the "Waking up the server" notice meanwhile.

### Measured results (November 2026)

| Check | Result |
|---|---|
| Backend `/api/v1/health` and `/api/v1/health/db` (direct, warm) | 200, about 0.2 s, `{"status":"ok","db":"connected"}` |
| API through the Vercel proxy, warm | 200 in about 0.17 s |
| **Cold start through the Vercel proxy** (after 15+ minutes idle) | **200 in 38.8 s** (one measurement) |
| Response security headers | HSTS, `nosniff`, `X-Frame-Options: DENY` and `Referrer-Policy` present on the API and the site |
| `/docs` and `/openapi.json` in production | 404 (disabled) |
| Protected endpoint without a login | 401 |
| CORS | Render allows the exact Vercel origin |
| Link-preview tags | `og:url` and `og:image` point at the real Vercel URL |
| Production database after migration and seeding | 20 DSA topics, 142 problems, 150 interview questions, `users` = 0 |
| Local container test, 512 MB limit (same limit as Render free) | about 290 MiB peak process memory (including a PDF upload and an ATS analysis), no out-of-memory kill |
| Local container test, full ATS analysis | about 6 to 8 seconds |

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

## 7. Docker Build & Container Operation

The backend uses a multi-stage Docker build based on `python:3.12-slim` designed for security, minimal size (~194MB content / ~880MB uncompressed), and multi-cloud compatibility.

### 7.1 Key Image Characteristics
- **Multi-stage build**: Builder stage resolves and installs production-only runtime wheels into `/opt/venv`; dev dependencies (`pytest`, `ruff`, etc.) and build tools are discarded.
- **Non-root user**: The final image runs as `appuser` (UID `1000`, GID `1000`).
- **Optimization flags**: `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`.
- **Exclusions**: `backend/.dockerignore` ensures `.env*`, `.venv`, `.git`, `tests/`, and cache directories never enter the image.
- **Full Source Tree Preserved**: Static JSON data (`app/data/*.json`), migrations (`alembic/`, `alembic.ini`), and utility scripts (`scripts/`) are retained. This permits running migrations and seeding directly from the same image.
- **Built-in Healthcheck**: Native Python `urllib` healthcheck checks `/api/v1/health` every 30s (10s timeout, 3 retries, 5s start period) without requiring external binaries like `curl`.
- **Dynamic Port Binding**: Starts with `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips="*"`.

### 7.2 Building the Image
From the repository root:
```bash
# Build natively (ARM64 on Apple Silicon, AMD64 on Linux x86_64)
docker build -t placement-copilot-backend:latest backend/

# Build for production target architecture (linux/amd64)
docker build --platform linux/amd64 -t placement-copilot-backend:latest backend/
```

### 7.3 Running the Application Container
```bash
# Run with default port 8000
docker run -d --name placement-backend \
  --env-file backend/.env \
  -p 8000:8000 \
  placement-copilot-backend:latest

# Run with custom PORT (e.g. 8001 or cloud-provided $PORT)
docker run -d --name placement-backend \
  --env-file backend/.env \
  -e PORT=8001 \
  -p 8001:8001 \
  placement-copilot-backend:latest
```

> [!NOTE]
> Docker's `--env-file` does not accept spaces around `=`. If `backend/.env` is written as `KEY = value`, make a cleaned temporary copy (create it with `umask 077` and delete it right after the container starts). To test with the same memory limit as Render's free tier, add `--memory=512m`.

### 7.4 One-Off Operational Commands with the Same Image
The same production image can run database migrations and the reference-data seed without modifying container entrypoints:

```bash
# Run Alembic migrations to latest schema version
docker run --rm --env-file backend/.env placement-copilot-backend:latest alembic upgrade head

# Seed initial catalog data (DSA problems, question bank)
docker run --rm --env-file backend/.env placement-copilot-backend:latest python scripts/seed.py
```

### 7.5 Deploying to Render (Free Web Service from the Dockerfile)

1. Create **New +**, then **Web Service**, and connect the GitHub repository (or use the Public Git Repository option for a public repo).
2. **Language**: `Docker`. **Branch**: `main`. **Region**: the one closest to the Neon database (Singapore). **Instance Type**: Free.
3. Open **Advanced** and set:
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Docker Build Context Directory**: `backend`
   - **Health Check Path**: `/api/v1/health`
   - Leave Root Directory, Build Command and Start Command empty. (Render's documentation says the Dockerfile path and the Docker context are both relative to the repository root.)
4. Render injects a `PORT` variable. The startup command already binds to `${PORT:-8000}`.
5. In **Environment**, add every required production variable from section 3. Type secrets directly into the dashboard. To avoid printing them, copy them to the clipboard from the terminal (for example `openssl rand -hex 32 | tr -d '\n' | pbcopy`) and paste.
6. Render redeploys automatically on every push to `main`.

**Free-tier caveats** (from Render's free-tier documentation in November 2026; re-check before relying on them):

- **Memory is 512 MB.** Measured locally with a 512 MB limit: about 290 MiB peak process memory including a PDF upload and an ATS analysis, so there is headroom, but not a lot.
- **The service spins down after 15 minutes without traffic and takes about a minute to wake.** Measured through the Vercel proxy: 38.8 seconds once. The frontend sends a health request when the page loads and shows a "Waking up the server" notice if the API is slow to answer. A free uptime pinger could keep it awake, but check Render's terms first.
- **Outbound traffic on ports 25, 465 and 587 is blocked.** Neon on port 5432 is not affected (confirmed by `/api/v1/health/db` returning 200).
- **Shared free-plan usage.** If you run other free services in the same Render workspace, check Billing for usage warnings.

### 7.6 Deploying the Frontend to Vercel

1. **Add New**, then **Project**, and import the repository.
2. **Root Directory**: `frontend`. **Framework Preset**: Vite. Keep the default build command (`npm run build`) and output directory (`dist`).
3. **Environment Variables**: add `VITE_SITE_URL` (Type **Config**) with the final Vercel URL. Do **not** set `VITE_API_BASE_URL`.
4. Deploy. If the final URL differs from what you entered, fix `VITE_SITE_URL`, set `CORS_ORIGINS` on Render to the real URL, and redeploy both.

### 7.7 Reverse Proxy & Rate Limiting Security Note
The backend uses `slowapi` for per-IP rate limiting (e.g., registration endpoint `POST /auth/register` throttled to `5/hour` in production).

> [!WARNING]
> **Client IP Resolution behind Proxies**:
> Per-IP limits rely on the `X-Forwarded-For` header passed to `uvicorn --proxy-headers --forwarded-allow-ips="*"`. In production environments behind edge proxies (Cloudflare, AWS ALB, Render, Vercel), per-IP limits are **best-effort** unless the edge proxy is strictly configured to strip or overwrite untrusted incoming `X-Forwarded-For` headers. For high-security environments, restrict `--forwarded-allow-ips` to your specific edge proxy VPC CIDR blocks to prevent client-side IP spoofing.

---

## 8. Security Posture & Pre-Deployment Audit Runbook

A comprehensive pre-deployment hardening pass was conducted across dependencies, static analysis, secrets, container vulnerabilities, authorization boundaries, API response headers, rate limiting, and accessibility/SEO.

### 8.1 Audit Scope & Summary

| Audit Domain | Scope / Tools | Initial Result | Remediated Status |
|---|---|---|---|
| **Python Dependencies** | `pip-audit` against `backend/pyproject.toml` | 0 vulnerabilities | **PASS** (0 vulnerabilities) |
| **Node.js Dependencies** | `npm audit` in `frontend/` (full & `--omit=dev`) | 2 vulnerabilities (`zod` GHSA-mrhx-c7xc-m3w5 High, `vite` GHSA-8g5g-mxqh-grgj Moderate) | **PASS** (Upgraded to `zod@4.6.7`, `vite@6.4.6`; 0 vulnerabilities) |
| **Python Static Analysis** | `bandit -r backend/app -ll` + SQL inspection | 0 issues; 100% parameterized ORM queries | **PASS** (0 issues) |
| **Secret Scanning** | Git history scan via `zricethezav/gitleaks:latest` | 4 false-positives (placeholder dummy keys in CI workflow) | **PASS** (0 production secrets leaked) |
| **Container Vulnerabilities** | `aquasec/trivy:latest` on `pc-backend` | 2 HIGH (`zlib1g` in base image, `setuptools 70.3.0` inside pip vendor) | **PASS** (Base `apt-get upgrade` + pip/setuptools purged from runtime `/opt/venv`; 0 HIGH/CRITICAL) |
| **Authorization Matrix** | 42 endpoints analyzed for IDOR & ownership guards | All user-scoped queries protected via `current_user.id` or `get_user_entity_or_404` | **PASS** (Automated cross-user IDOR test suite added) |
| **API Response Headers** | `SecurityHeadersMiddleware` on FastAPI & Vercel | Missing standard security headers & cache controls on API | **PASS** (Added `nosniff`, `DENY`, `strict-origin-when-cross-origin`, HSTS, and `Cache-Control: no-store` on `/api/v1/*`) |
| **Rate Limiting & Caps** | Pagination limits, upload sizes, registration throttle | Uncapped pagination limits on `/resumes`, `/job-descriptions`, `/ats`, `/interviews` | **PASS** (Capped at `ge=1, le=100`, upload size checked against `MAX_UPLOAD_MB`) |
| **Accessibility & SEO** | Lighthouse, Axe-core, Open Graph, Twitter cards, robots.txt | Lighthouse A11y: 78, SEO: 91; missing input labels and contrast issues | **PASS** (Labels/aria added; OG/Twitter/robots.txt/og-image generated) |

---

### 8.2 Reproducible Audit Commands

To re-run the exact security audit suite locally or in CI:

#### 1. Python Dependencies (`pip-audit`)
```bash
# In an isolated temporary virtualenv:
python3 -m venv /tmp/audit-venv
/tmp/audit-venv/bin/pip install --upgrade pip pip-audit
/tmp/audit-venv/bin/pip install "backend/"
/tmp/audit-venv/bin/pip-audit
rm -rf /tmp/audit-venv
```

#### 2. Frontend Dependencies (`npm audit`)
```bash
cd frontend
npm audit
npm audit --omit=dev
```

#### 3. Python Static Analysis & AST Security (`bandit`)
```bash
python3 -m venv /tmp/bandit-venv
/tmp/bandit-venv/bin/pip install bandit
/tmp/bandit-venv/bin/bandit -r backend/app -ll
rm -rf /tmp/bandit-venv
```

#### 4. Git History Secret Scanning (`gitleaks`)
```bash
docker run --rm -v "$(pwd):/repo:ro" zricethezav/gitleaks:latest git --redact -v /repo
```

#### 5. Docker Container Image Vulnerability Scan (`trivy`)
```bash
# Build image first
docker build -t pc-backend:audit backend/
# Run Trivy vulnerability scanner
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity HIGH,CRITICAL pc-backend:audit
```

#### 6. Cross-User IDOR Integration Test Suite
```bash
cd backend
.venv/bin/pytest tests/integration/test_idor_authorization.py -v
```

---

### 8.3 Open Recommendations & Future Hardening

The following items are deferred or recommended for production infrastructure rollout:

1. **Content Security Policy (CSP)**:
   A strict Content Security Policy (`default-src 'self'`) is currently disabled in favor of developer velocity and CDN loading (Google Fonts `fonts.googleapis.com` and `fonts.gstatic.com`). Configure a staged CSP header in Vercel (`vercel.json`) with reporting mode (`Content-Security-Policy-Report-Only`) to monitor font and script dependencies before enforcing strict CSP.
2. **Reverse Proxy IP Trust Boundary**:
   In production setups behind Cloudflare or AWS ALB, replace `--forwarded-allow-ips="*"` in the container startup command with the exact reverse proxy CIDR block to prevent spoofed `X-Forwarded-For` client headers from circumventing rate limit counters.
3. **Database Connection SSL**:
   In production, verify that Neon connection strings always include `?sslmode=require`. Placement Copilot's startup configuration validates this in `production` mode.

---

## 9. Operations Notes

- **Redeploying**: push to `main`. Render and Vercel redeploy automatically. A Vercel redeploy is also required whenever a `VITE_` variable changes.
- **Rotating a secret**: change it in the Render dashboard (the service restarts). Changing `JWT_SECRET` signs everyone out. If a connection string or API key was ever exposed, reset the Neon role password and create a new Gemini key, then update Render.
- **Model retirement**: Google retires Gemini models. If results come back marked `degraded` or the logs show repeated 404s from Gemini, check the model names against the current model list and update `GEMINI_MODEL` / `GEMINI_FALLBACK_MODEL` in Render. `gemini-3.1-flash-lite` had a shutdown date of 7 May 2027.
- **Gemini free-tier limits**: the daily request limit is per project and visible in Google AI Studio's rate-limit page (it was not published per model in the public documentation when this was written). Each ATS analysis makes at least two Gemini calls (one embedding, one generation). Keep `LLM_GLOBAL_DAILY_LIMIT` below your project's daily limit.
- **Starting fresh**: to reset production, create a new empty Neon branch, repeat release step 2 against it, and point `DATABASE_URL` and `DATABASE_URL_DIRECT` at it.
- **Cold starts**: see the caveats in section 7.5. Open the site yourself shortly before sharing the link with anyone.
