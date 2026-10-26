# Architectural and Design Decisions (ADRs)

This document tracks all non-obvious technical and architectural decisions for Placement Copilot, detailing the context, alternatives considered, and rationale.

---

## ADR 001: Python 3.14 Environment with psycopg v3 and SQLAlchemy Async
- **Context**: The master prompt specifies Python 3.12+ for backend execution with explicit version pinning. Neon PostgreSQL uses PgBouncer connection pooling requiring `prepare_threshold=None` and async engine support.
- **Decision**: Utilized the macOS local Python 3.14 runtime with explicit virtualenv isolation (`backend/.venv`), SQLAlchemy 2.0 async engine with `postgresql+psycopg://` driver.
- **Alternatives Considered**:
  - Python 3.10: Too old; lacks newer typing and performance improvements, fails the "Python 3.12+" spec.
  - Bare `asyncpg`: Does not support psycopg v3 semantics and doesn't handle Neon's PgBouncer pooler without complex custom type codecs.
- **Reason**: `psycopg` (v3) binary with `prepare_threshold=None` is the official recommended driver for Neon serverless PgBouncer connection pooling.

---

## ADR 002: Dual Database Connection Strategy (Pooled vs Direct)
- **Context**: Neon serverless Postgres provides two connection endpoints: a pooled connection for regular app queries and a direct connection for DDL migrations.
- **Decision**: Configure `DATABASE_URL` for FastAPI runtime async queries with `pool_pre_ping=True` and pool size ≤ 5. Configure `DATABASE_URL_DIRECT` for Alembic migrations.
- **Alternatives Considered**: Single connection URL for both migrations and runtime.
- **Reason**: PgBouncer transaction-mode pooling can fail or behave unexpectedly during transactional DDL migrations (e.g. Alembic schema changes, table locks). Direct connection ensures deterministic migrations.

---

## ADR 003: Deterministic Scoring vs Generative Explanations
- **Context**: AI/ML features must be reliable, reproducible, and explainable to candidates and recruiters.
- **Decision**: All scoring formulas (Resume ATS, DSA Mastery S & Mastery%, Mock Interview θ & P, Placement Readiness Composite) are implemented with deterministic algorithms and calibrated constants. The LLM is restricted solely to explaining, rewriting bullets, generating contextual follow-up questions, and providing qualitative feedback returned as schema-validated JSON.
- **Alternatives Considered**: End-to-end LLM scoring (prompting LLM to output a number from 1 to 100).
- **Reason**: Pure LLM scoring suffers from stochastic drift, prompt injection vulnerability, hallucination, and lack of monotonic fairness across candidates. Mathematical formulas guarantee reproducible benchmarks.

---

## ADR 004: Frontend State Architecture (Zustand + TanStack Query)
- **Context**: Placement Copilot handles both client UI/auth state and server-synced state (mock interview session, attempts, ats analyses).
- **Decision**: Use Zustand for client-side authentication tokens, user session state, and persistent UI preferences. Use TanStack Query for all server-side state (caching, optimistic updates on DSA attempts, query invalidation).
- **Alternatives Considered**: Redux Toolkit, Context API alone.
- **Reason**: Zustand has minimal boilerplate and zero context re-rendering penalties. TanStack Query provides built-in deduplication, retry logic, background cache refreshes, and optimistic updates required for responsive UI interactions.

---

## ADR 005: LLM Provider Abstraction with Resilient Fallback
- **Context**: The platform integrates Google Gemini (`google-genai` SDK) for qualitative feedback, but must remain resilient against API rate limits, temporary network partitions, or invalid JSON responses.
- **Decision**: Implement an `LLMProvider` protocol interface with `GeminiProvider` and `FakeProvider`. For evaluations, employ schema validation via Pydantic, a single retry on malformed JSON, and graceful degradation to a deterministic heuristic fallback flagged with `degraded=True` in the database and UI.
- **Alternatives Considered**: Direct ad-hoc Gemini API calls without fallback.
- **Reason**: Guarantees zero unhandled crashes during mock interviews and ATS analyses, while ensuring 100% testability in CI and unit tests without external API dependencies.

---

## ADR 006: Tailwind CSS v4 CSS-First `@theme` Architecture
- **Context**: Tailwind v4 deprecates `tailwind.config.js` in favor of a CSS-first `@theme` block. In v4, defining custom `--spacing-xs|sm|md|lg|xl` tokens causes collisions with named width utilities (e.g. `max-w-lg` silently collapses to 24px).
- **Decision**: Configured color tokens (`--color-surface: #131313`, `--color-primary: #4be277`, etc.) and typography in `frontend/src/styles/index.css`. Adhered strictly to Tailwind's numeric spacing scale and arbitrary values (`max-w-[420px]`, `max-w-[1440px]`), completely avoiding named spacing token overrides.
- **Alternatives Considered**: Defining custom spacing tokens in CSS variables.
- **Reason**: Prevents subtle layout collapse and ensures robust responsive behavior across desktop and mobile screens.

---

## ADR 007: Frontend is JavaScript (JSX) by Owner's Choice
- **Context**: The owner knows JavaScript (JSX) deeply and must be able to confidently explain every single line of code during live technical interviews without friction, syntax confusion, or compiler indirection introduced by TypeScript.
- **Decision**: Converted the frontend completely from TypeScript to idiomatic modern JavaScript (ES6+ and JSX). Stripped all compile-time type annotations, interfaces, generics, type assertions (`as`), and non-null assertions (`!`). Configured ESLint with standard React Hooks and React Refresh rules. Maintained runtime schema validations with Zod and React Hook Form. Documented comprehensive request and response shapes in `docs/API.md` and codebase structure in `docs/FRONTEND_TOUR.md`.
- **Alternatives Considered**: Retaining TypeScript with looser compiler flags (`noImplicitAny: false`).
- **Reason**: Looser TypeScript still requires build-time type checking, complex generic utility types in libraries (Zustand/TanStack Query), and type definitions that do not provide runtime guarantees. Idiomatic JavaScript combined with Zod runtime validation ensures clean, production-grade code that the developer can explain line-by-line with 100% clarity.

