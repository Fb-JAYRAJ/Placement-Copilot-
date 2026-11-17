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
| `LLM_GLOBAL_DAILY_LIMIT` | Optional | Max daily LLM calls across all users combined. Default: `300`. | `300` |
| `REGISTER_RATE_LIMIT` | Optional | Per-IP rate limit on `POST /auth/register` in production. Default: `5/hour` (in dev: `1000/hour`). | `5/hour` |
| `ALLOW_SIGNUP` | Optional | Global toggle for new candidate signups (`true` or `false`). Returns 403 when false. Default: `true`. | `true` |
| `DEMO_EMAIL` | Optional | Demo account email guarded against modification, deletion, and export. Default: `demo@placementcopilot.com`. | `demo@placementcopilot.com` |
| `DEMO_LLM_DAILY_QUOTA` | Optional | Max daily LLM calls for demo account. Default: `15`. | `15` |
| `MAX_UPLOAD_MB` | Optional | Max file size for resume uploads. Default: `5`. | `5` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Access token lifetime in minutes. Default: `30`. | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Optional | Refresh token lifetime in days. Default: `7`. | `7` |

---

### Frontend Environment Variables (`frontend/.env`)

| Variable | Required? | Purpose | Safe Production Placeholder |
|---|---|---|---|
| `VITE_API_BASE_URL` | **Required\*** | Backend API base URL (no trailing slash). \*Empty if using Vercel same-domain proxy. | `https://api.placementcopilot.com` |
| `VITE_ENABLE_DEMO` | Optional | Controls visibility of 1-click Demo Account login button (`true` or `false`, default: `true`). | `true` |
| `VITE_SITE_URL` | Optional | Canonical production URL used for Open Graph and Twitter preview metadata (no trailing slash). | `https://placement-copilot.vercel.app` |

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

### 7.4 One-Off Operational Commands with the Same Image
The same production image runs database migrations and seed scripts without modifying container entrypoints:

```bash
# Run Alembic migrations to latest schema version
docker run --rm --env-file backend/.env placement-copilot-backend:latest alembic upgrade head

# Seed initial catalog data (DSA problems, skills taxonomy, question bank)
docker run --rm --env-file backend/.env placement-copilot-backend:latest python scripts/seed.py

# Optional: Seed demo candidate account
docker run --rm --env-file backend/.env placement-copilot-backend:latest python scripts/seed_demo.py
```

### 7.5 Deploying to Cloud Container Platforms

#### Hugging Face Spaces (Docker SDK)
1. In your Hugging Face Space `README.md`, declare the Docker SDK and target port:
   ```yaml
   ---
   title: Placement Copilot API
   emoji: 🚀
   colorFrom: green
   colorTo: gray
   sdk: docker
   app_port: 7860
   ---
   ```
2. Hugging Face automatically exposes `$PORT=7860`. The backend container automatically detects and binds to `0.0.0.0:7860`.
3. Configure environment secrets in the Space's **Settings -> Variables and secrets**.

#### Render (Web Service from Dockerfile)
1. Create a **New + -> Web Service** and link the repository.
2. Select **Language**: `Docker`.
3. Configure the **Dockerfile Path**: `backend/Dockerfile` (or set Root Directory to `backend/`).
4. Render injects the `$PORT` environment variable (typically `10000`) into the container. The startup command automatically binds to `${PORT:-8000}`.
5. In **Environment Variables**, provide all required production keys (`DATABASE_URL`, `DATABASE_URL_DIRECT`, `SECRET_KEY`, `JWT_SECRET`, `GEMINI_API_KEY`, etc.).

### 7.6 Reverse Proxy & Rate Limiting Security Note
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
   A strict Content Security Policy (`default-src 'self'`) is currently disabled in favor of developer velocity and CDN loading (Google Fonts `fonts.googleapis.com` and `fonts.gstatic.com`). Prior to production launch, configure a staged CSP header in Vercel (`vercel.json`) with reporting mode (`Content-Security-Policy-Report-Only`) to monitor font and script dependencies before enforcing strict CSP.
2. **Reverse Proxy IP Trust Boundary**:
   In production setups behind Cloudflare or AWS ALB, replace `--forwarded-allow-ips="*"` in the container startup command with the exact reverse proxy CIDR block to prevent spoofed `X-Forwarded-For` client headers from circumventing rate limit counters.
3. **Database Connection SSL**:
   In production, verify that Neon connection strings always include `?sslmode=require`. Placement Copilot's startup configuration validates this in `production` mode.


