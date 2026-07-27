# BrandGuard — Master Build Prompt & Engineering Knowledge Base

**Purpose of this document:** feed this whole file to your coding agent (Claude Code, Cursor, etc.) at the start of every build session, before it writes a single line of code. It is the agent's constitution for this project — scope, architecture, phase gates, and the anti-patterns that turn a promising idea into "vibe-coded junk": pretty on top, empty underneath.

**Builder profile this is written for:** strong in Python, GenAI/ML/DL/NLP, analytics, and Python backend. No frontend stack of choice — frontend framework is delegated to the agent's judgement, with guardrails so it doesn't become the tail that wags the dog.

---

## 0. How To Use This Document

1. Paste this file (or link it) into the agent's context at the start of every session.
2. Work **one phase at a time** (Section 5). Do not let the agent start Phase N+1 while Phase N's Definition of Done is unmet.
3. At the start of a session, make the agent state out loud: *"Resuming Phase X. DoD for this phase is: ..."* before writing code. This forces it to re-anchor instead of freelancing.
4. At the end of a session, the agent updates `CHANGELOG.md` and `docs/phase-logs/phase-N.md` with what it actually verified — command run, output seen — not just what it wrote.
5. The original BrandGuard product-vision teardown (the 13-section spec) is the **north star**, not the build spec. It lives in `docs/vision.md` as a backlog source, not literal instructions.

---

## 1. Prime Directive — The Anti-"Vibe-Coded Junk" Manifesto

These are non-negotiable. If the agent proposes violating one, it must flag the trade-off explicitly instead of silently doing it.

1. **No feature is "done" until it runs against real (or realistically representative) data.** A hardcoded stub that returns a plausible-looking JSON blob is not a feature — it is a mock, and mocks must be labeled.
2. **Every mock is tracked.** Any placeholder response gets a `# MOCK — replace in Phase X` comment and a line in `MOCKS.md`. If `MOCKS.md` isn't empty by the end of a phase that was supposed to remove it, the phase isn't done.
3. **Every ML component ships with a number, not a vibe.** "Sentiment analysis works" is not acceptable. "F1 0.81 on aspect polarity, N=300 held-out labeled reviews" is. See Section 6.
4. **One concern, one module.** No god-files. If `main.py` or any single file starts doing ingestion + ML + API + business logic, split it before adding more to it.
5. **No silent failure.** Every external call (DB, API, model inference) has explicit error handling. `except: pass` is forbidden — an error is either handled meaningfully or re-raised with context.
6. **Secrets never touch code.** `.env` + `.env.example`, nothing hardcoded, `.env` in `.gitignore`.
7. **Every phase ends with something you can personally run and see work** — a script, an endpoint, a demo — not just "files exist."
8. **Tests are written for logic-bearing code**, especially ML scoring, aggregation, and business rules — not necessarily for trivial CRUD/plumbing. Calibrate rigor to where bugs actually hide.
9. **Boring beats impressive.** Every new dependency must justify itself against "could I do this with what I already have." LangChain, a message queue, a vector DB service, Kubernetes — each is a "prove you need it" decision, not a default.
10. **No frontend logic duplicates backend logic.** If a number is computed twice — once in Python, once in JS — that's two sources of truth waiting to disagree. The frontend calls the API; it doesn't recompute.

---

## 2. Scope Lock — What v1 Actually Is

The full BrandGuard vision (ingestion from 9+ platforms, fake-review detection, white-label agency reporting, browser extension, multi-tenant SSO, video/image analysis...) is an enterprise SaaS roadmap, not a solo v1. Building a thin slice of all nine feature categories is exactly how you get something that demos well for thirty seconds and falls apart under any real question — the "beautiful on top, hollow inside" failure mode you're trying to avoid.

**v1 core loop (build this deep, not wide):**

```
Real review dataset → NLP/ABSA pipeline → structured store
        → dashboard + "Ask BrandGuard" (RAG chat) + anomaly alerts
```

**Explicitly IN scope for v1:**
- Ingest reviews from 1–2 sources (a real public dataset + optional CSV upload — see Section 6)
- Aspect-Based Sentiment Analysis (your DistilBERT + heuristic hybrid, with a real eval report)
- Theme/topic clustering via embeddings
- A queryable API over the structured results
- RAG-based natural-language query ("Ask BrandGuard") with citations back to source reviews
- Basic anomaly detection + alerting on sentiment spikes
- One working dashboard consuming that API

**Explicitly OUT of scope for v1** (park in `docs/vision.md` as backlog, revisit only after the above is real):
- Fake/incentivized review detection
- Named-competitor benchmarking
- White-label agency reporting
- Browser extension / embeddable trust widget
- Multi-tenant RBAC, SSO, data residency
- Video/image review analysis
- Live scraping connectors to Amazon/Trustpilot/etc. (ToS-restricted and a legal problem before it's an engineering one — start from downloadable datasets instead)

If a session's energy is going toward a v2 item before v1's core loop has real numbers behind it, that's scope creep — say so and redirect.

---

## 3. Tech Stack (Python-first, pinned)

### Backend & ML — your zone, own it deeply
| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | — |
| API | FastAPI + Pydantic v2 + Uvicorn | Auto-generated OpenAPI docs, async-native, you likely know this already |
| ORM / migrations | SQLModel (or SQLAlchemy 2.0) + Alembic | Typed models, no hand-edited schema drift |
| Database | Postgres 15 + `pgvector` extension | One database does both structured rows and vector similarity search — avoids standing up a separate vector DB service for v1 |
| Background jobs | `APScheduler` for v1; upgrade to Celery + Redis only if ingestion volume actually demands it | Celery's operational overhead isn't earned yet at v1 scale |
| ABSA / sentiment | Fine-tuned DistilBERT + keyword heuristics (your existing hackathon approach as the v1 baseline) | Improving this is an explicit iteration loop with tracked metrics, not a one-shot |
| Embeddings / clustering | `sentence-transformers` + HDBSCAN or KMeans (scikit-learn) | Theme extraction without predefined categories |
| Aspect/entity preprocessing | spaCy | — |
| GenAI / RAG | Anthropic or OpenAI API, hand-rolled RAG (embed → pgvector similarity search → grounded prompt → cited answer) | Skip LangChain for v1 — a hand-rolled RAG is ~150 lines you fully understand, versus a framework abstraction you have to debug through |
| Testing | pytest, pytest-cov | — |
| Packaging | `uv` or Poetry + `pyproject.toml` | — |
| Local infra | Docker + docker-compose (Postgres, Redis) | Reproducible environment, not "works on my machine" |
| Observability | `structlog` or stdlib logging with JSON formatting; `/health` endpoint | — |

### Frontend — delegated, with guardrails
You have no frontend stack of choice, so the agent decides — but not blindly:

- **Fast path (recommended for the first real demo):** Streamlit or Gradio. Plays entirely to Python, gets the full loop (ingest → ML → dashboard) working end-to-end fastest, and defers frontend-skill debt until the backend is actually proven.
- **Polish path (once the backend is proven, Phase 6+):** Next.js + Tailwind + shadcn/ui, calling the FastAPI backend as a pure client. Only worth the investment after the ML core has real metrics behind it — polishing a UI in front of an unproven pipeline is exactly the "beautiful on top" trap.
- Either way: the frontend **only calls documented API endpoints**. It never reimplements sentiment scoring, aggregation, or business rules in JS.

---

## 4. Repository Structure

```
brandguard/
├── README.md
├── MOCKS.md                  # every active mock, tagged with which phase removes it
├── CHANGELOG.md
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── Makefile
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/
│   │   ├── core/             # config, logging, security
│   │   ├── models/           # SQLModel ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # business logic, orchestration
│   │   ├── ml/
│   │   │   ├── absa/         # aspect-based sentiment model code
│   │   │   ├── embeddings/
│   │   │   ├── rag/
│   │   │   └── eval/         # eval scripts + checked-in metrics.json / eval_report.md
│   │   ├── ingestion/connectors/
│   │   └── db/migrations/
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── fixtures/         # small REAL data samples, checked into repo
├── frontend/                 # agent's choice — Streamlit app or Next.js project
├── data/
│   ├── raw/                  # gitignored, real datasets
│   └── processed/
├── scripts/                  # dataset downloaders, one-off loaders
└── docs/
    ├── vision.md             # the full 13-section product teardown — backlog source only
    ├── architecture.md
    └── phase-logs/
```

---

## 5. Build Phases — Actions & Definition of Done

Each phase has a hard gate: don't move on until the DoD is demonstrably true, not "probably fine."

### Phase 0 — Foundation
**Actions:** repo scaffold; `pyproject.toml`; pre-commit hooks (`black`, `ruff`, `isort`); pytest scaffold; `docker-compose.yml` for Postgres + Redis; `.env.example`; GitHub Actions CI running lint + tests; README skeleton.
**DoD:** `docker-compose up` produces a healthy Postgres; `pytest` runs clean (even with a trivial placeholder test); CI is green on push.

### Phase 1 — Data Foundation
**Actions:** pick real dataset(s) — see Section 6 — instead of building a live scraper first (scraping is a legal/ToS problem before it's an engineering one, and it's the lowest-ML-value part of the whole system). Define `SQLModel` schemas for `Review`, `Product`, `Aspect`, `SentimentResult`. Write a loader script (CSV → Postgres) with Pydantic validation. Check a small (20–50 row) real fixture sample into `tests/fixtures/`.
**DoD:** `python scripts/load_reviews.py sample.csv` loads rows you can query; Alembic migration exists and is applied; tests pass against the fixture, not synthetic Faker data.

### Phase 2 — ABSA / NLP Core (the heart of the product — invest the most here)
**Actions:** build/fine-tune the DistilBERT ABSA classifier (hybrid with keyword heuristics as your v1 baseline, per your existing hackathon build). Build an eval harness against a labeled hold-out set (public ABSA dataset like SemEval restaurants/laptops, or your own hand-labeled sample). Add the embeddings + clustering pipeline for theme extraction.
**DoD:** running the pipeline on Phase 1's fixture data produces stored `SentimentResult` rows with aspect + polarity + confidence; `eval_report.md` shows real precision/recall/F1 numbers; clustering output is human-readable and you've manually sanity-checked at least one cluster.

### Phase 3 — API Layer
**Actions:** FastAPI endpoints: ingest review(s); sentiment summary per product/time-window; theme clusters; anomaly alerts. Pydantic schemas on every request/response.
**DoD:** `/docs` (FastAPI's auto OpenAPI page) shows working, callable endpoints; integration tests hit a real test database (not mocked) and assert on structured output.

### Phase 4 — RAG / "Ask BrandGuard"
**Actions:** embed the review corpus into `pgvector`; hand-rolled RAG — retrieve top-k relevant review chunks → construct a grounded prompt → call the LLM → return the answer **with the specific review IDs it drew from**.
**DoD:** a natural-language query returns an answer plus traceable citations; an answer with no matching source reviews is treated as a bug (hallucination), not shipped as a feature.

### Phase 5 — Alerts & Anomaly Detection
**Actions:** simple z-score/EWMA anomaly detection on theme-level negative-sentiment volume over time; a scheduled job (APScheduler) checks thresholds and fires an alert (start with log/email/webhook — Slack is a stretch).
**DoD:** injecting a synthetic-but-realistic spike into fixture data triggers an alert; ordinary fluctuation doesn't (you can point to a false-positive check, not just "it alerted once").

### Phase 6 — Dashboard
**Actions:** agent's chosen stack (Streamlit fast-path or Next.js polish-path, per Section 3) — executive summary view, product→aspect drill-down, time-series chart, "Ask BrandGuard" chat UI, alerts list. Calls only Phase 3–5 APIs.
**DoD:** someone unfamiliar with the code can open the app and answer "what's the #1 complaint about Product X this month" without reading source.

### Phase 7 — Polish & Deployment (stretch)
**Actions:** containerize the full stack; deploy (Render/Railway/Fly.io free tier or similar); basic auth; rate limiting; error monitoring (Sentry free tier).
**DoD:** a public URL works end-to-end for a stranger with no setup on their end.

---

## 6. Data & Evaluation Requirements

This is your strongest area — don't shortcut it just because it's "just data prep."

- **Seed datasets** (real, downloadable, no scraping needed for v1): Amazon Reviews (McAuley/UCSD dataset, on Hugging Face), Yelp Open Dataset, SemEval ABSA restaurant/laptop datasets (for aspect-level ground truth to actually evaluate against).
- **Every ML claim needs a number attached.** Not "the sentiment model works" — "F1 0.81 on aspect polarity, evaluated on N=300 held-out labeled reviews, dated in `metrics.json`."
- **Track experiments minimally.** A solo project doesn't need full MLflow, but it needs more than "trust me" — a `metrics.json` or `experiments.md` per model version, checked into `ml/eval/`.
- **Descriptive vs. predictive stays labeled.** If a number is "observed" (from real ingested reviews) vs. "projected" (a what-if estimate), the UI and the code must never blend the two without saying which is which.

---

## 7. Testing & Quality Gates

- pytest required for: ML pipeline functions, API endpoints, data validation schemas.
- Tests for ML-relevant code use small **real** data fixtures, not synthetic Faker text — synthetic data hides exactly the failure modes (sarcasm, slang, mixed sentiment) that make ABSA hard in the first place.
- CI runs lint + tests on every push. A phase is not done while CI is red.

---

## 8. Forbidden Anti-Patterns (reject these if the agent proposes them)

- A single `app.py`/`main.py` that does ingestion, ML, API, and business logic all in one file.
- An endpoint that returns hardcoded example JSON "for now" without a `# MOCK` tag and a `MOCKS.md` entry.
- An LLM call used to fabricate a plausible-sounding metric instead of computing one from real data.
- Hand-edited database schema instead of a tracked Alembic migration.
- A frontend that recomputes sentiment/aggregation logic in JS instead of calling the API.
- Silent `except: pass` blocks anywhere in the codebase.
- Declaring a phase "done" because it compiles or renders, without a demo run against real data.
- Adding a dependency (message queue, vector DB service, LangChain, Kubernetes) because it sounds impressive, without a concrete reason the simpler option in Section 3 fails.

---

## 9. Session Operating Procedure for the Agent

- **Start of session:** state which phase is being resumed and restate that phase's Definition of Done before writing any code.
- **During the session:** don't start Phase N+1 work while Phase N's DoD is unmet or its tests are failing.
- **When a mock is added:** immediately log it in `MOCKS.md` with the phase that will remove it.
- **End of session:** update `CHANGELOG.md` and `docs/phase-logs/phase-N.md` with what was actually verified — the exact command run and the output seen — not just a description of what was written.
- **When in doubt between "build it properly" and "build it fast":** default to properly for anything in the ML/eval path (Section 6) — that's the part a demo audience can't fake their way past. Fast-path shortcuts belong in the frontend, and only after Phase 3 is real.

---

## 10. Reference Doc

The original BrandGuard product-vision teardown (ingestion from 9+ platforms, competitive benchmarking, white-label reporting, browser extension, multi-tenant SSO, video/image analysis, and the rest of the 13-section spec) is the long-term north star — store it as `docs/vision.md`. Treat it as a **backlog source for post-v1 roadmap ideas**, never as literal build instructions for this solo build. Every feature pulled from it into an active phase has to go through Section 2's scope discipline first.
