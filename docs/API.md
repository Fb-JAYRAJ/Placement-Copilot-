# Placement Copilot — REST API Documentation (v1)

Base API Path: `/api/v1`  
Protocol: JSON over HTTP/1.1 or HTTP/2  
Authentication: Bearer JWT (`Authorization: Bearer <access_token>`) + HTTP-Only Refresh Cookie  

---

## Standard Error Envelope

All error responses return HTTP 4xx or 5xx with a structured error envelope:

```json
{
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "Invalid email or password.",
    "details": null
  }
}
```

Standard Error Codes:
- `AUTHENTICATION_FAILED` (401)
- `TOKEN_EXPIRED` (401)
- `PERMISSION_DENIED` (403)
- `NOT_FOUND` (404)
- `RATE_LIMIT_EXCEEDED` (429)
- `QUOTA_EXCEEDED` (429)
- `VALIDATION_ERROR` (422)
- `INTERNAL_SERVER_ERROR` (500)

---

## Standard List Envelope (`PaginatedResponse[T]`)

All REST list endpoints in Placement Copilot enforce a standardized pagination envelope via Pydantic (`backend/app/schemas/common.py`):

```json
{
  "items": [ ... ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### Envelope Fields:
- `items` (`List[T]`): Array of typed resource records.
- `total` (`int`): Total count of matching resources across all pages.
- `limit` (`int`): Page size limit (defaults to 20 or 50, maximum 100).
- `offset` (`int`): Zero-based pagination offset.

### Endpoints Enforcing This Convention:
1. `GET /api/v1/dsa/topics` -> `PaginatedResponse[TopicOut]`
2. `GET /api/v1/dsa/problems` -> `PaginatedResponse[ProblemOut]`
3. `GET /api/v1/dsa/attempts` -> `PaginatedResponse[AttemptOut]`
4. `GET /api/v1/dsa/mastery` -> `PaginatedResponse[TopicMasteryOut]`
5. `GET /api/v1/dsa/recommendations` -> `PaginatedResponse[ProblemRecommendationOut]`
6. `GET /api/v1/dsa/reviews/due` -> `PaginatedResponse[ReviewDueOut]`
7. `GET /api/v1/resumes` -> `PaginatedResponse[ResumeOut]`
8. `GET /api/v1/job-descriptions` -> `PaginatedResponse[JobDescriptionOut]`
9. `GET /api/v1/ats/analyses` -> `PaginatedResponse[ATSAnalysisSummaryOut]`
10. `GET /api/v1/interviews` -> `PaginatedResponse[InterviewSessionOut]`
11. `GET /api/v1/dashboard/readiness/history` -> `PaginatedResponse[ReadinessDataPointOut]`

---

## 1. Authentication & Session (`/auth`)

### `POST /auth/register`
Creates a candidate account and returns access token.
- **Request Body**:
  ```json
  {
    "email": "candidate@university.edu",
    "name": "Candidate Name",
    "password": "Password123!",
    "college": "University Name",
    "grad_year": 2026,
    "target_role": "Software Engineer"
  }
  ```
- **Response** (`201 Created`): Returns `{ access_token, token_type, user }` and sets `refresh_token` httpOnly cookie.

### `POST /auth/login`
Authenticates with email and password.
- **Request Body**:
  ```json
  {
    "email": "candidate@university.edu",
    "password": "Password123!"
  }
  ```
- **Response** (`200 OK`): Returns `{ access_token, token_type, user }` and sets rotating `refresh_token` cookie.

### `POST /auth/refresh`
Rotates the refresh token and returns a fresh 30-minute access token.
- **Headers**: Requires `Cookie: refresh_token=<token>`
- **Response** (`200 OK`): `{ access_token, token_type }`

### `POST /auth/logout`
Revokes active refresh token and clears auth cookie.
- **Response** (`204 No Content`)

---

## 2. User Profile & Settings (`/users`)

### `GET /users/me`
Fetches authenticated user profile.
- **Response** (`200 OK`):
  ```json
  {
    "id": "uuid",
    "email": "candidate@university.edu",
    "name": "Candidate Name",
    "college": "University",
    "grad_year": 2026,
    "target_role": "Software Engineer",
    "target_companies": ["Google", "Stripe"],
    "created_at": "2026-10-20T12:00:00Z"
  }
  ```

### `PATCH /users/me`
Updates candidate profile preferences.
- **Request Body**:
  ```json
  {
    "name": "Updated Name",
    "college": "New College",
    "grad_year": 2026,
    "target_role": "Backend Engineer",
    "target_companies": ["Google", "Microsoft"]
  }
  ```

### `POST /users/me/password`
Updates candidate password.
- **Request Body**: `{ "current_password": "...", "new_password": "..." }`

### `GET /users/me/export`
Exports all candidate data (profile, resumes, analyses, attempts, mock interviews) as JSON.

### `DELETE /users/me`
Permanently hard-deletes user account and cascades all related records.

---

## 3. Resume & ATS Alignment (`/resumes`, `/ats`)

### `POST /resumes`
Uploads resume (PDF, DOCX via multipart form) or plaintext.
- **Form Fields**: `file` (optional binary), `title` (optional string), `content_text` (optional string)
- **Response** (`201 Created`): `{ id, title, filename, file_type, content_text, created_at }`

### `GET /resumes`
Lists all candidate uploaded resumes.

### `DELETE /resumes/{id}`
Deletes uploaded resume.

### `POST /ats/analyze`
Runs deterministic ATS scoring against job description.
- **Request Body**:
  ```json
  {
    "resume_id": "uuid",
    "inline_jd_text": "Requirements:\n- Proficient in Python...",
    "company": "Google",
    "role": "Software Engineer"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "id": "uuid",
    "overall": 78.4,
    "keyword_score": 82.0,
    "semantic_score": 75.3,
    "tfidf_score": 70.1,
    "quality_score": 85.0,
    "matched": [{ "name": "Python", "evidence": "Developed backend with Python..." }],
    "missing": [{ "name": "Docker", "weight": 1.5 }],
    "suggestions": [{ "target_bullet": "...", "issue": "...", "rewrite": "..." }],
    "degraded": false
  }
  ```

### `GET /ats/analyses`
Lists historical ATS runs for the candidate.

---

## 4. DSA Practice & Mastery (`/dsa`)

### `GET /dsa/topics`
Lists 20 standard DSA topics with categories and target points.

### `GET /dsa/problems?topic={slug}&difficulty={easy|medium|hard}&q={search}`
Searches the 140+ Blind-75 curated problem catalog.

### `POST /dsa/attempts`
Logs a coding attempt and recomputes topic mastery.
- **Request Body**:
  ```json
  {
    "problem_id": "uuid",
    "custom_title": null,
    "topic_id": "uuid",
    "difficulty": "medium",
    "status": "solved",
    "confidence": 4,
    "time_spent_min": 30,
    "notes": "Two-pointer approach"
  }
  ```

### `GET /dsa/mastery`
Returns real-time mastery scores (0–100%) and priorities across topics.

### `GET /dsa/recommendations`
Returns top 5 unsolved recommended problems targeting weak topics.

### `GET /dsa/reviews/due`
Returns problems scheduled for SuperMemo SM-2 review.

### `GET /dsa/stats`
Returns totals, streak, and 7-day velocity bar chart data.

---

## 5. Adaptive Mock Interview (`/interviews`)

### `POST /interviews`
Initializes adaptive session starting at ability $\theta = 2.5$.
- **Request Body**:
  ```json
  {
    "track": "dsa_concepts",
    "company": "Google",
    "role": "Software Engineer",
    "planned_questions": 5
  }
  ```
- **Response** (`201 Created`): Interview session object with initial question.

### `POST /interviews/{id}/answers`
Evaluates answer, updates ability $\theta$ via IRT, and selects next question.
- **Request Body**:
  ```json
  {
    "question_id": "uuid",
    "answer_text": "To solve this problem, we use sliding window...",
    "time_taken_sec": 120
  }
  ```
- **Response** (`200 OK`): Dimension scores (0–10), strengths, gaps, improved answer, updated $\theta$, and next question.

### `POST /interviews/{id}/follow-up`
Generates one follow-up probe for the current question.

### `POST /interviews/{id}/finish`
Concludes session and generates final audit report.

### `GET /interviews/{id}/report`
Fetches final report: overall difficulty-weighted score, $\theta$ trajectory, per-topic scores, top 3 gaps, and 3 action items.

---

## 6. Dashboard Aggregation (`/dashboard`)

### `GET /dashboard/summary?range={7d|30d|90d}`
Returns Placement Readiness Score, component breakdown, top 3 levers, sparkline series, daily focus task, recent activity feed, and onboarding status.

### `GET /dashboard/readiness/history`
Returns historical readiness snapshots over time.

---

## 7. Endpoint Request & Response Shapes (Generated from `/openapi.json`)

Since client-side TypeScript types and `schema.d.ts` have been removed in favor of plain JavaScript, this section provides the exact JSON shapes for every request payload and successful response across the API.

### ATS Endpoints

#### `GET /api/v1/ats/analyses` — List Analyses
**Response** (`HTTP 200`):
```json
[
  {
    "id": "string (uuid)",
    "resume_id": "string (uuid)",
    "jd_id": "string (uuid)",
    "overall": "number",
    "keyword_score": "number",
    "semantic_score": "number",
    "tfidf_score": "number",
    "quality_score": "number",
    "matched": "any",
    "missing": "any",
    "suggestions": "any",
    "degraded": "boolean",
    "created_at": "string (date-time)"
  }
]
```

---

#### `GET /api/v1/ats/analyses/{analysis_id}` — Get Analysis
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `analysis_id` | path | `string` | Yes | - |

**Response** (`HTTP 200`):
```json
{
  "id": "string (uuid)",
  "resume_id": "string (uuid)",
  "jd_id": "string (uuid)",
  "overall": "number",
  "keyword_score": "number",
  "semantic_score": "number",
  "tfidf_score": "number",
  "quality_score": "number",
  "matched": "any",
  "missing": "any",
  "suggestions": "any",
  "degraded": "boolean",
  "created_at": "string (date-time)"
}
```

---

#### `POST /api/v1/ats/analyze` — Analyze Resume Ats
**Request Body** (`application/json`):
```json
{
  "resume_id": "string (uuid)",
  "jd_id": "string (uuid)",
  "inline_jd_text": "string",
  "company": "string",
  "role": "string"
}
```

**Response** (`HTTP 201`):
```json
{
  "id": "string (uuid)",
  "resume_id": "string (uuid)",
  "jd_id": "string (uuid)",
  "overall": "number",
  "keyword_score": "number",
  "semantic_score": "number",
  "tfidf_score": "number",
  "quality_score": "number",
  "matched": "any",
  "missing": "any",
  "suggestions": "any",
  "degraded": "boolean",
  "created_at": "string (date-time)"
}
```

---

### AUTH Endpoints

#### `POST /api/v1/auth/login` — Login
**Request Body** (`application/json`):
```json
{
  "email": "string (email)",
  "password": "string"
}
```

**Response** (`HTTP 200`):
```json
{
  "access_token": "string",
  "token_type": "string",
  "expires_in": "integer",
  "user": {
    "id": "string (uuid)",
    "email": "string",
    "name": "string",
    "college": "string",
    "grad_year": "integer",
    "target_role": "string",
    "target_companies": [
      "string"
    ],
    "created_at": "string (date-time)",
    "updated_at": "string (date-time)"
  }
}
```

---

#### `POST /api/v1/auth/logout` — Logout
**Request Body:** None / multipart

**Response** (`HTTP 200`):
```json
"any"
```

---

#### `POST /api/v1/auth/refresh` — Refresh Tokens
**Request Body:** None / multipart

**Response** (`HTTP 200`):
```json
{
  "access_token": "string",
  "token_type": "string",
  "expires_in": "integer",
  "user": {
    "id": "string (uuid)",
    "email": "string",
    "name": "string",
    "college": "string",
    "grad_year": "integer",
    "target_role": "string",
    "target_companies": [
      "string"
    ],
    "created_at": "string (date-time)",
    "updated_at": "string (date-time)"
  }
}
```

---

#### `POST /api/v1/auth/register` — Register
**Request Body** (`application/json`):
```json
{
  "email": "string (email)",
  "name": "string",
  "password": "string",
  "college": "string",
  "grad_year": "integer",
  "target_role": "string",
  "target_companies": [
    "string"
  ]
}
```

**Response** (`HTTP 201`):
```json
{
  "access_token": "string",
  "token_type": "string",
  "expires_in": "integer",
  "user": {
    "id": "string (uuid)",
    "email": "string",
    "name": "string",
    "college": "string",
    "grad_year": "integer",
    "target_role": "string",
    "target_companies": [
      "string"
    ],
    "created_at": "string (date-time)",
    "updated_at": "string (date-time)"
  }
}
```

---

### DASHBOARD Endpoints

#### `GET /api/v1/dashboard/readiness/history` — Get Readiness History
**Response** (`HTTP 200`):
```json
[
  {
    "id": "string (uuid)",
    "composite": "number",
    "confidence": "number",
    "ats": "number",
    "dsa": "number",
    "interview": "number",
    "consistency": "number",
    "created_at": "string (date-time)"
  }
]
```

---

#### `GET /api/v1/dashboard/summary` — Get Dashboard Summary
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `range` | query | `string` | No | - |

**Response** (`HTTP 200`):
```json
{
  "user_name": "string",
  "composite": "number",
  "confidence": "number",
  "has_enough_data": "boolean",
  "delta_7d": "number",
  "components": {},
  "weights": {},
  "levers": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "gain": "number",
      "type": "string",
      "action_url": "string"
    }
  ],
  "ats_sparkline": [
    {
      "date": "string",
      "value": "number"
    }
  ],
  "dsa_sparkline": [
    {
      "date": "string",
      "value": "number"
    }
  ],
  "mock_sparkline": [
    {
      "date": "string",
      "value": "number"
    }
  ],
  "ats_average": "number",
  "dsa_topics_covered": "integer",
  "dsa_total_topics": "integer",
  "current_streak": "integer",
  "mock_average": "number",
  "daily_focus_task": {},
  "recent_activity": [
    {}
  ],
  "onboarding_checklist": {}
}
```

---

### DSA Endpoints

#### `POST /api/v1/dsa/attempts` — Create Attempt
**Request Body** (`application/json`):
```json
{
  "problem_id": "string (uuid)",
  "custom_title": "string",
  "topic_id": "string (uuid)",
  "difficulty": "string",
  "status": "\"todo\" | \"in_progress\" | \"solved\" | \"failed\"",
  "confidence": "integer",
  "time_spent_min": "integer",
  "notes": "string",
  "attempted_at": "string (date-time)"
}
```

**Response** (`HTTP 201`):
```json
{
  "id": "string (uuid)",
  "problem_id": "string (uuid)",
  "custom_title": "string",
  "topic_id": "string (uuid)",
  "topic_name": "string",
  "problem_title": "string",
  "difficulty": "string",
  "status": "\"todo\" | \"in_progress\" | \"solved\" | \"failed\"",
  "confidence": "integer",
  "time_spent_min": "integer",
  "notes": "string",
  "attempted_at": "string (date-time)",
  "solved_at": "string (date-time)",
  "sm2_ease": "number",
  "sm2_interval_days": "integer",
  "sm2_repetitions": "integer",
  "next_review_at": "string (date-time)"
}
```

---

#### `GET /api/v1/dsa/attempts` — Get Attempts
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `status` | query | `string` | No | - |
| `topic_id` | query | `string` | No | - |
| `difficulty` | query | `string` | No | - |
| `limit` | query | `integer` | No | - |
| `offset` | query | `integer` | No | - |

**Response** (`HTTP 200`):
```json
{
  "items": [
    {
      "id": "string (uuid)",
      "problem_id": "string (uuid)",
      "custom_title": "string",
      "topic_id": "string (uuid)",
      "topic_name": "string",
      "problem_title": "string",
      "difficulty": "string",
      "status": "\"todo\" | \"in_progress\" | \"solved\" | \"failed\"",
      "confidence": "integer",
      "time_spent_min": "integer",
      "notes": "string",
      "attempted_at": "string (date-time)",
      "solved_at": "string (date-time)",
      "sm2_ease": "number",
      "sm2_interval_days": "integer",
      "sm2_repetitions": "integer",
      "next_review_at": "string (date-time)"
    }
  ],
  "total": "integer",
  "limit": "integer",
  "offset": "integer"
}
```

---

#### `PATCH /api/v1/dsa/attempts/{attempt_id}` — Update Attempt
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `attempt_id` | path | `string` | Yes | - |

**Request Body** (`application/json`):
```json
{
  "custom_title": "string",
  "difficulty": "string",
  "status": "\"todo\" | \"in_progress\" | \"solved\" | \"failed\"",
  "confidence": "integer",
  "time_spent_min": "integer",
  "notes": "string"
}
```

**Response** (`HTTP 200`):
```json
{
  "id": "string (uuid)",
  "problem_id": "string (uuid)",
  "custom_title": "string",
  "topic_id": "string (uuid)",
  "topic_name": "string",
  "problem_title": "string",
  "difficulty": "string",
  "status": "\"todo\" | \"in_progress\" | \"solved\" | \"failed\"",
  "confidence": "integer",
  "time_spent_min": "integer",
  "notes": "string",
  "attempted_at": "string (date-time)",
  "solved_at": "string (date-time)",
  "sm2_ease": "number",
  "sm2_interval_days": "integer",
  "sm2_repetitions": "integer",
  "next_review_at": "string (date-time)"
}
```

---

#### `DELETE /api/v1/dsa/attempts/{attempt_id}` — Delete Attempt
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `attempt_id` | path | `string` | Yes | - |

**Response** (`HTTP 204 No Content`): Empty

---

#### `GET /api/v1/dsa/mastery` — Get Mastery
**Response** (`HTTP 200`):
```json
[
  {
    "topic_id": "string (uuid)",
    "slug": "string",
    "name": "string",
    "category": "string",
    "importance": "number",
    "mastery": "number",
    "evidence": "any",
    "last_practiced_at": "string (date-time)"
  }
]
```

---

#### `GET /api/v1/dsa/problems` — Get Problems
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `topic` | query | `string` | No | Topic slug or UUID |
| `difficulty` | query | `string` | No | - |
| `q` | query | `string` | No | Search query |
| `limit` | query | `integer` | No | - |
| `offset` | query | `integer` | No | - |

**Response** (`HTTP 200`):
```json
{
  "items": [
    {
      "id": "string (uuid)",
      "slug": "string",
      "title": "string",
      "difficulty": "string",
      "platform": "string",
      "url": "string",
      "frequency": "number",
      "topic_ids": [
        "string (uuid)"
      ]
    }
  ],
  "total": "integer",
  "limit": "integer",
  "offset": "integer"
}
```

---

#### `GET /api/v1/dsa/recommendations` — Get Recommendations
**Response** (`HTTP 200`):
```json
[
  {
    "problem_id": "string",
    "slug": "string",
    "title": "string",
    "difficulty": "string",
    "topic_name": "string",
    "frequency": "number",
    "reason": "string"
  }
]
```

---

#### `GET /api/v1/dsa/reviews/due` — Get Reviews Due
**Response** (`HTTP 200`):
```json
[
  {
    "attempt_id": "string (uuid)",
    "problem_id": "string (uuid)",
    "title": "string",
    "topic_name": "string",
    "difficulty": "string",
    "next_review_at": "string (date-time)",
    "overdue_days": "integer"
  }
]
```

---

#### `GET /api/v1/dsa/stats` — Get Stats
**Response** (`HTTP 200`):
```json
"any"
```

---

#### `GET /api/v1/dsa/topics` — Get Topics
**Response** (`HTTP 200`):
```json
[
  {
    "id": "string (uuid)",
    "slug": "string",
    "name": "string",
    "category": "string",
    "importance": "number",
    "target_points": "number"
  }
]
```

---

### GENERAL Endpoints

#### `GET /` — Root
**Response** (`HTTP 200`):
```json
"any"
```

---

### INTERVIEWS Endpoints

#### `GET /api/v1/interviews` — List Interviews
**Response** (`HTTP 200`):
```json
[
  {
    "id": "string (uuid)",
    "track": "\"dsa_concepts\" | \"cs_fundamentals\" | \"behavioral\" | \"system_design\"",
    "company": "string",
    "role": "string",
    "planned_questions": "integer",
    "status": "\"active\" | \"completed\" | \"abandoned\"",
    "ability": "number",
    "final_score": "number",
    "current_question": {
      "id": "string (uuid)",
      "interview_id": "string (uuid)",
      "seq": "integer",
      "topic": "string",
      "difficulty": "number",
      "text": "string",
      "ideal_points": [
        "string"
      ],
      "source": "\"bank\" | \"generated\" | \"follow_up\"",
      "parent_question_id": "string (uuid)"
    },
    "questions_answered_count": "integer",
    "started_at": "string (date-time)",
    "ended_at": "string (date-time)"
  }
]
```

---

#### `POST /api/v1/interviews` — Create Interview
**Request Body** (`application/json`):
```json
{
  "track": "\"dsa_concepts\" | \"cs_fundamentals\" | \"behavioral\" | \"system_design\"",
  "company": "string",
  "role": "string",
  "planned_questions": "integer"
}
```

**Response** (`HTTP 201`):
```json
{
  "id": "string (uuid)",
  "track": "\"dsa_concepts\" | \"cs_fundamentals\" | \"behavioral\" | \"system_design\"",
  "company": "string",
  "role": "string",
  "planned_questions": "integer",
  "status": "\"active\" | \"completed\" | \"abandoned\"",
  "ability": "number",
  "final_score": "number",
  "current_question": {
    "id": "string (uuid)",
    "interview_id": "string (uuid)",
    "seq": "integer",
    "topic": "string",
    "difficulty": "number",
    "text": "string",
    "ideal_points": [
      "string"
    ],
    "source": "\"bank\" | \"generated\" | \"follow_up\"",
    "parent_question_id": "string (uuid)"
  },
  "questions_answered_count": "integer",
  "started_at": "string (date-time)",
  "ended_at": "string (date-time)"
}
```

---

#### `GET /api/v1/interviews/{interview_id}` — Get Interview
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | `string` | Yes | - |

**Response** (`HTTP 200`):
```json
{
  "id": "string (uuid)",
  "track": "\"dsa_concepts\" | \"cs_fundamentals\" | \"behavioral\" | \"system_design\"",
  "company": "string",
  "role": "string",
  "planned_questions": "integer",
  "status": "\"active\" | \"completed\" | \"abandoned\"",
  "ability": "number",
  "final_score": "number",
  "current_question": {
    "id": "string (uuid)",
    "interview_id": "string (uuid)",
    "seq": "integer",
    "topic": "string",
    "difficulty": "number",
    "text": "string",
    "ideal_points": [
      "string"
    ],
    "source": "\"bank\" | \"generated\" | \"follow_up\"",
    "parent_question_id": "string (uuid)"
  },
  "questions_answered_count": "integer",
  "started_at": "string (date-time)",
  "ended_at": "string (date-time)"
}
```

---

#### `POST /api/v1/interviews/{interview_id}/answers` — Submit Answer
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | `string` | Yes | - |

**Request Body** (`application/json`):
```json
{
  "question_id": "string (uuid)",
  "answer_text": "string",
  "time_taken_sec": "integer"
}
```

**Response** (`HTTP 200`):
```json
{
  "evaluation": {
    "id": "string (uuid)",
    "question_id": "string (uuid)",
    "overall": "number",
    "scores": {},
    "feedback": {},
    "time_taken_sec": "integer",
    "degraded": "boolean"
  },
  "next_question": {
    "id": "string (uuid)",
    "interview_id": "string (uuid)",
    "seq": "integer",
    "topic": "string",
    "difficulty": "number",
    "text": "string",
    "ideal_points": [
      "string"
    ],
    "source": "\"bank\" | \"generated\" | \"follow_up\"",
    "parent_question_id": "string (uuid)"
  },
  "completed": "boolean",
  "final_score": "number",
  "report": {
    "overall_score": "number",
    "final_ability": "number",
    "theta_trajectory": [
      "number"
    ],
    "per_topic_scores": {},
    "top_gaps": [
      "string"
    ],
    "action_items": [
      "string"
    ],
    "delta_vs_previous": "number"
  }
}
```

---

#### `POST /api/v1/interviews/{interview_id}/finish` — Finish Interview
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | `string` | Yes | - |

**Request Body:** None / multipart

**Response** (`HTTP 200`):
```json
{
  "overall_score": "number",
  "final_ability": "number",
  "theta_trajectory": [
    "number"
  ],
  "per_topic_scores": {},
  "top_gaps": [
    "string"
  ],
  "action_items": [
    "string"
  ],
  "delta_vs_previous": "number"
}
```

---

#### `POST /api/v1/interviews/{interview_id}/follow-up` — Create Follow Up
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | `string` | Yes | - |
| `question_id` | query | `string` | Yes | - |

**Request Body:** None / multipart

**Response** (`HTTP 200`):
```json
{
  "id": "string (uuid)",
  "interview_id": "string (uuid)",
  "seq": "integer",
  "topic": "string",
  "difficulty": "number",
  "text": "string",
  "ideal_points": [
    "string"
  ],
  "source": "\"bank\" | \"generated\" | \"follow_up\"",
  "parent_question_id": "string (uuid)"
}
```

---

#### `GET /api/v1/interviews/{interview_id}/report` — Get Report
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | `string` | Yes | - |

**Response** (`HTTP 200`):
```json
{
  "overall_score": "number",
  "final_ability": "number",
  "theta_trajectory": [
    "number"
  ],
  "per_topic_scores": {},
  "top_gaps": [
    "string"
  ],
  "action_items": [
    "string"
  ],
  "delta_vs_previous": "number"
}
```

---

### JOB-DESCRIPTIONS Endpoints

#### `GET /api/v1/job-descriptions` — List Job Descriptions
**Response** (`HTTP 200`):
```json
[
  {
    "id": "string (uuid)",
    "company": "string",
    "role": "string",
    "jd_text": "string",
    "extracted": "any",
    "created_at": "string (date-time)"
  }
]
```

---

#### `POST /api/v1/job-descriptions` — Create Job Description
**Request Body** (`application/json`):
```json
{
  "company": "string",
  "role": "string",
  "jd_text": "string"
}
```

**Response** (`HTTP 201`):
```json
{
  "id": "string (uuid)",
  "company": "string",
  "role": "string",
  "jd_text": "string",
  "extracted": "any",
  "created_at": "string (date-time)"
}
```

---

#### `GET /api/v1/job-descriptions/{jd_id}` — Get Job Description
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `jd_id` | path | `string` | Yes | - |

**Response** (`HTTP 200`):
```json
{
  "id": "string (uuid)",
  "company": "string",
  "role": "string",
  "jd_text": "string",
  "extracted": "any",
  "created_at": "string (date-time)"
}
```

---

### OPS Endpoints

#### `GET /api/v1/health` — Health Check
**Response** (`HTTP 200`):
```json
"any"
```

---

#### `GET /api/v1/health/db` — Health Db Check
**Response** (`HTTP 200`):
```json
"any"
```

---

### RESUMES Endpoints

#### `GET /api/v1/resumes` — List Resumes
**Response** (`HTTP 200`):
```json
[
  {
    "id": "string (uuid)",
    "title": "string",
    "filename": "string",
    "file_type": "string",
    "is_primary": "boolean",
    "parsed": "any",
    "created_at": "string (date-time)"
  }
]
```

---

#### `POST /api/v1/resumes` — Upload Resume
**Request Body** (`multipart/form-data`):
```json
{
  "file": "string",
  "title": "string",
  "content_text": "string",
  "is_primary": "boolean"
}
```

**Response** (`HTTP 201`):
```json
{
  "id": "string (uuid)",
  "title": "string",
  "filename": "string",
  "file_type": "string",
  "is_primary": "boolean",
  "parsed": "any",
  "created_at": "string (date-time)"
}
```

---

#### `GET /api/v1/resumes/{resume_id}` — Get Resume
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `resume_id` | path | `string` | Yes | - |

**Response** (`HTTP 200`):
```json
{
  "id": "string (uuid)",
  "title": "string",
  "filename": "string",
  "file_type": "string",
  "is_primary": "boolean",
  "parsed": "any",
  "created_at": "string (date-time)"
}
```

---

#### `DELETE /api/v1/resumes/{resume_id}` — Delete Resume
**Parameters:**
| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `resume_id` | path | `string` | Yes | - |

**Response** (`HTTP 204 No Content`): Empty

---

### USERS Endpoints

#### `GET /api/v1/users/me` — Get Me
**Response** (`HTTP 200`):
```json
{
  "id": "string (uuid)",
  "email": "string",
  "name": "string",
  "college": "string",
  "grad_year": "integer",
  "target_role": "string",
  "target_companies": [
    "string"
  ],
  "created_at": "string (date-time)",
  "updated_at": "string (date-time)"
}
```

---

#### `DELETE /api/v1/users/me` — Delete Me
**Response** (`HTTP 204 No Content`): Empty

---

#### `PATCH /api/v1/users/me` — Update Me
**Request Body** (`application/json`):
```json
{
  "name": "string",
  "college": "string",
  "grad_year": "integer",
  "target_role": "string",
  "target_companies": [
    "string"
  ]
}
```

**Response** (`HTTP 200`):
```json
{
  "id": "string (uuid)",
  "email": "string",
  "name": "string",
  "college": "string",
  "grad_year": "integer",
  "target_role": "string",
  "target_companies": [
    "string"
  ],
  "created_at": "string (date-time)",
  "updated_at": "string (date-time)"
}
```

---

#### `GET /api/v1/users/me/export` — Export My Data
**Response** (`HTTP 200`):
```json
{}
```

---

#### `POST /api/v1/users/me/password` — Change Password
**Request Body** (`application/json`):
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

**Response** (`HTTP 200`):
```json
"any"
```

---

