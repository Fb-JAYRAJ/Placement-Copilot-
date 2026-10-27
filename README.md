<div align="center">

# 🚀 Placement Copilot

**An AI-assisted placement-prep platform that combines resume ATS scoring, DSA mastery tracking and adaptive mock interviews into one explainable Readiness Score.**

![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/Postgres-Neon-4169E1?logo=postgresql&logoColor=white)
![Gemini](https://img.shields.io/badge/LLM-Gemini-8E75B2?logo=googlegemini&logoColor=white)

🌐 Live demo: _coming soon_ · 📚 [API reference](docs/API.md) · 🏛️ [Architecture](docs/ARCHITECTURE.md) · 🧭 [Design decisions](docs/DECISIONS.md) · 🗺️ [Frontend tour](docs/FRONTEND_TOUR.md)

</div>

## 📸 Screenshots

<table>
  <tr>
    <td width="50%" align="center">
      <b>📊 Dashboard</b><br />
      <sub>Readiness score, levers and activity feed</sub><br />
      <img src="https://github.com/user-attachments/assets/315fa7a5-a5f7-45d5-afb3-1d59040ac83e" alt="Dashboard with the readiness score gauge" />
    </td>
    <td width="50%" align="center">
      <b>🧮 DSA Tracker</b><br />
      <sub>Mastery bars, recommendations and review schedule</sub><br />
      <img src="https://github.com/user-attachments/assets/537f1a8d-6899-4033-8981-80ff4bd17d86" alt="DSA Tracker with weak-area bars" />
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <b>📄 Resume ATS Analyzer</b><br />
      <sub>Match score, matched and missing skills, rewrite suggestions</sub><br />
      <img src="https://github.com/user-attachments/assets/42d8e223-fa14-4f68-99f3-e60a985181d1" alt="Resume ATS Analyzer results" />
    </td>
    <td width="50%" align="center">
      <b>🎤 Adaptive Mock Interview</b><br />
      <sub>Live difficulty badge and rubric-based feedback</sub><br />
      <img src="https://github.com/user-attachments/assets/3a09c6a8-938c-4abe-a287-ea0b90dda852" alt="Adaptive mock interview session" />
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <b>📈 Interview report</b><br />
      <sub>Ability trajectory and per-question breakdown</sub><br />
      <img src="https://github.com/user-attachments/assets/578fe1eb-4444-4d18-812a-8b68e4a71024" alt="Interview report with ability trajectory" />
    </td>
    <td width="50%" align="center">
      <b>🔐 Sign in</b><br />
      <sub>Email login with a one-click demo account</sub><br />
      <img src="https://github.com/user-attachments/assets/573d7f08-9599-42d7-9084-6a792180e142" alt="Sign in screen" />
    </td>
  </tr>
</table>

## 💡 Why I built it

Placement prep is scattered across resume checkers, problem trackers and mock-interview tools, and none of them tell you what to do next. Placement Copilot connects all three in one loop and turns them into a single score, along with the specific actions that would raise it. It is also my attempt to build a full-stack product where every number on screen comes from an algorithm I can explain.

## ✨ Features

- 📄 **Resume ATS Analyzer.** Upload a PDF or DOCX, or paste text, and compare it with a job description. Skills are matched against a taxonomy of about 380 terms, with fuzzy matching for variants. You get four sub-scores (keyword, TF-IDF, semantic and content quality), matched skills with evidence, missing skills ranked by importance, and rewrite suggestions that reuse your own bullets and never invent experience.
- 🧮 **DSA Tracker.** Log problems from a catalog of 140+ interview problems, or add your own. Mastery is tracked per topic with time decay, SM-2 spaced repetition schedules your reviews, and the app recommends five problems with a reason for each, alongside weak-area bars and a 7-day activity chart.
- 🎤 **Adaptive Mock Interview.** Question difficulty follows a live ability estimate. An LLM judge scores each answer against a fixed rubric, one follow-up is allowed per question, and a final report shows your ability trajectory.
- 📊 **Dashboard.** A readiness gauge with weekly change, a component breakdown, the three actions that would raise your score most, a daily focus task and an activity feed. New users get an onboarding checklist instead of empty charts.
- 👤 **Profile.** Edit your details, change your password, export all your data as JSON, or hard-delete your account.

## 🏗️ Architecture

```mermaid
flowchart LR
    Browser["Browser"] --> FE["React + Vite app"]
    FE -->|"REST + JWT"| API["FastAPI backend"]
    API --> ATS["Resume ATS analyzer"]
    API --> DSA["DSA mastery + SM-2"]
    API --> INT["Adaptive interview engine"]
    API --> RDY["Readiness score"]
    ATS --> DB[("Neon Postgres")]
    DSA --> DB
    INT --> DB
    RDY --> DB
    ATS -.-> LLM["Gemini API"]
    INT -.-> LLM
```

What happens when a user submits an interview answer:

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React app
    participant API as FastAPI
    participant LLM as Gemini
    participant DB as Neon Postgres
    U->>FE: Submit answer
    FE->>API: POST /api/v1/interviews/{id}/answers
    API->>LLM: Judge answer (question, ideal points, answer in delimiters)
    LLM-->>API: Scores and feedback as JSON
    API->>API: Update ability and choose next difficulty
    API->>DB: Save answer, scores and new ability
    API-->>FE: Evaluation and next question
    FE-->>U: Feedback panel and next question
```

More diagrams (database ER, auth and token refresh) are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🧠 How the AI works

Design rule: **algorithms score, LLMs explain.** Scores are deterministic and reproducible. The LLM writes questions, feedback and rewrite suggestions, always as schema-validated JSON, and never changes a score.

| Feature | Method | Details |
|---|---|---|
| Resume match | Hybrid scoring | `overall = 0.40·keyword + 0.25·semantic + 0.15·TF-IDF + 0.20·quality`. Semantic similarity uses Gemini embeddings. If embeddings are unavailable, the semantic term is dropped, the weights are renormalized and the result is flagged as degraded. |
| DSA mastery | Time-decayed evidence | Difficulty weights 1 / 2 / 3.5, decay constant of 45 days, `mastery = 1 − e^(−S / target)`. SM-2 schedules reviews. |
| Adaptive interview | Rasch (1PL) style ability model | Ability θ in [1, 5], starting at 2.5. Expected score `P = 1 / (1 + e^−(θ − b))`. Update `θ += K·(score − P)` with a decaying step. The next question targets a difficulty of about θ + 0.3. |
| Answer judging | LLM rubric | Correctness 40%, depth 25%, structure 20%, communication 15%. The answer is isolated in delimiters and treated as untrusted data. Low temperature, schema-validated output, and a heuristic fallback flagged as degraded. |
| Readiness score | Weighted composite | `0.25·ATS + 0.35·DSA + 0.30·interview + 0.10·consistency`. Components with no data are excluded and the weights renormalized, and a confidence figure is shown. “Levers” are found by simulating the next best action. |

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, JavaScript (JSX), Tailwind CSS v4, Zustand, TanStack Query, React Router, react-hook-form + Zod, Recharts |
| Backend | Python, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic, PyJWT, Argon2 |
| Database | Neon serverless PostgreSQL (pooled connection for the app, direct connection for migrations) |
| AI / ML | Gemini API (generation and embeddings), scikit-learn (TF-IDF), rapidfuzz, NumPy |
| Quality | pytest, ESLint, Ruff |

## 📁 Project structure

```text
placement-copilot/
├── backend/
│   ├── app/
│   │   ├── api/v1/       route handlers
│   │   ├── core/         config, database, security
│   │   ├── models/       SQLAlchemy models
│   │   ├── schemas/      Pydantic request/response models
│   │   ├── services/     ats, dsa, interview, readiness, llm
│   │   └── data/         skills taxonomy, DSA catalog, question bank
│   ├── alembic/          database migrations
│   ├── scripts/          seed.py, seed_demo.py
│   └── tests/            unit and integration tests
├── frontend/
│   └── src/
│       ├── features/     auth, dashboard, dsa, resume, interview, profile
│       ├── components/   shared UI
│       └── lib/api/      API client
├── docs/                 API, architecture, decisions, frontend tour
└── dev.sh                starts backend and frontend together
```

## 🚀 Getting started

**Prerequisites:** Python 3.12+, Node.js 20+, a free [Neon](https://neon.com) account, and a Gemini API key from [Google AI Studio](https://aistudio.google.com).

```bash
git clone https://github.com/Fb-JAYRAJ/Placement-Copilot-.git placement-copilot
cd placement-copilot
```

### 1. Database (Neon)

1. Create a Neon project. Keep the default `production` branch for deployment.
2. Create two branches from it, `dev` and `test`, and **untick “Automatically delete branch after”**. Neon ticks it by default, and your branches would disappear after a day.
3. For each branch, open **Connect** and copy a pooled and a direct connection string. Change the start of each from `postgresql://` to `postgresql+psycopg://`.

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # then fill in the values below
alembic upgrade head          # uses DATABASE_URL_DIRECT
python scripts/seed.py        # skills, topics, problems, question bank
python scripts/seed_demo.py   # optional: demo account with sample data
cd ..
```

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Neon pooled connection string for the `dev` branch (app traffic) |
| `DATABASE_URL_DIRECT` | Neon direct connection string for the `dev` branch (migrations) |
| `TEST_DATABASE_URL` | Neon direct connection string for the `test` branch (integration tests) |
| `GEMINI_API_KEY` | Google AI Studio key |
| `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL` | Model names, verified at startup |
| `SECRET_KEY`, `JWT_SECRET` | Random secrets for signing |
| `CORS_ORIGINS` | Allowed frontend origins |

See `backend/.env.example` for the full list.

### 3. Frontend

```bash
cd frontend
npm install
cd ..
```

### 4. Run everything

```bash
./dev.sh
```

- 🖥️ App: http://localhost:5173
- 📖 API docs (Swagger): http://localhost:8000/docs
- 🎯 Demo account, if you ran the demo seed: `demo@placementcopilot.com` / `DemoCandidate2026!`

## 🧪 Running the tests

```bash
# Backend: unit tests for every scoring formula and integration tests for each endpoint group
cd backend && source .venv/bin/activate && pytest -q

# Frontend: lint and production build
cd ../frontend && npm run lint && npm run build
```

Integration tests run against the Neon `test` branch, so the first request after a pause can take a second or two while the database wakes up.

## 🔌 API

Interactive documentation is served at `/docs` while the backend runs. Request and response shapes for every endpoint are listed in [docs/API.md](docs/API.md).

## 🔒 Security

- Passwords are hashed with Argon2.
- Access tokens are short-lived. Refresh tokens rotate on every use, are stored hashed, and are tracked in families so reuse can be detected and revoked.
- Rate limits protect login and LLM endpoints, and each user has a daily LLM quota.
- Uploads are validated by file signature and size, and only the extracted text is kept.
- Interview answers are isolated from instructions before they reach the LLM, and model output is schema-validated.
- Secrets live in environment variables and are never committed.

## 🧭 Design decisions

- **Two Neon connection strings.** The app uses the pooled endpoint for many short requests, while Alembic uses the direct endpoint because migrations need a normal session.
- **Algorithms score, LLMs explain.** Keeping scores out of the model makes them reproducible, testable and explainable.
- **No claims the data can’t support.** The dashboard shows “not enough data yet” and a confidence figure instead of a fake number.
- **JavaScript on the frontend.** Chosen for clarity and speed of iteration, and recorded in [docs/DECISIONS.md](docs/DECISIONS.md).

## 🛠️ Troubleshooting

- **`password authentication failed` from Neon.** The branch in your connection string has probably expired or its password was reset. Create the branch again with auto-delete switched off, or reset the role password, then update `backend/.env`.
- **Log lines with long IPv6 addresses and `No route to host`.** These are harmless. Your network has no IPv6 route to Neon, so the driver falls back to IPv4.
- **Database errors at startup.** Check that each connection string starts with `postgresql+psycopg://`.
- **A slow first request.** Neon wakes from idle on the first query, which takes a second or two.

## 🚧 Limitations and roadmap

- Scanned, image-only resumes need an OCR step. Text-based PDFs and DOCX files work today.
- Interviews accept written answers only. Voice input is the next planned feature.
- Planned: automatic sync of solved problems from coding platforms, a downloadable PDF report, and Google and GitHub sign-in.

## 👤 Author

**Jayraj Sawant** · [GitHub](https://github.com/Fb-JAYRAJ) · [LinkedIn](https://www.linkedin.com/in/jayraj-sawant12)

## 📄 License

MIT. See [LICENSE](LICENSE).
