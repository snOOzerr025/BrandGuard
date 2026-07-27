# Changelog

All notable changes to this project will be documented in this file.

## [0.5.0] - 2026-07-27

### Phase 4 — Ask BrandGuard (RAG)

#### Added
- `backend/app/rag/schemas.py` — Strict Pydantic types: `QueryType` enum (PURE_VECTOR / SQL_AGGREGATE / HYBRID), `RouteDecision`, `ReviewChunk`, `Citation`, `ChatResponse`, `ChatRequest`
- `backend/app/rag/gemini_client.py` — Google GenAI SDK (`google-genai`, not the deprecated package). Two structured-output calls: `classify_query()` → `RouteDecision`, `generate_answer()` → `ChatResponse`. Safe fallback when `GEMINI_API_KEY` is absent.
- `backend/app/rag/retriever.py` — `PgVectorRetriever` (production, pgvector cosine with hard `WHERE user_id + product_id`), `FallbackRetriever` (SQLite / tests, recent reviews by date). Auto-detected via engine dialect.
- `backend/app/rag/context_builder.py` — Markdown context assembler: product header, pre-computed aspect summary, SQL metrics block, retrieved review chunks with review_id + similarity score
- `backend/app/services/chat_service.py` — Full RAG orchestrator: classify → embed → retrieve → aggregate → build context → Gemini answer → async QueryLog insert
- `backend/app/api/routes/chat.py` — `POST /api/v1/products/{id}/chat` auth-gated endpoint. Returns `ChatResponse` with answer, citations (real review UUIDs), confidence, query_type_used.
- `backend/tests/integration/test_chat_api.py` — 8 integration tests: auth, 404 isolation, cross-user protection, schema validation, QueryLog persistence, empty product graceful handling

#### Architecture Invariants
- Vector search is NEVER used for time-series trend queries — SQL aggregation on stored SentimentResult rows only
- Every retrieval call has a hard `WHERE user_id AND product_id` clause at the SQL level
- Gemini uses structured output schema (`response_schema` + `application/json`) — no text-parsing of citations
- QueryLog DB insert runs in a BackgroundTask — response never blocks on the write

#### Verified
- Command: `python -m pytest backend/tests/integration/test_chat_api.py -v -W error::FutureWarning` → `8 passed, 0 warnings`
- SDK: migrated from deprecated `google-generativeai` → `google-genai`
- Total test count: **82 tests passing** (60 non-ML + 22 ABSA)

---

## [0.4.0] - 2026-07-27


### Phase 2 — ABSA / NLP Core

#### Added
- `backend/app/ml/absa/sentiment_analyzer.py` — Upgraded DistilBERT 3-class analyzer (confidence threshold 0.90 → neutral), batch_size=64, max_length=256 (~2x throughput)
- `backend/app/ml/absa/aspect_extractor.py` — Upgraded AspectExtractor: 8 aspects (was 4), 3x keyword expansion, sentence-level isolation (polarity scored on matching sentence, not full review)
- `backend/app/ml/embeddings/encoder.py` — `ReviewEncoder` using `all-MiniLM-L6-v2` (384-dim, L2-normalized, ~2000 texts/sec CPU)
- `backend/app/ml/embeddings/cluster.py` — `ReviewClusterer` KMeans + TF-IDF auto-labeling for theme discovery
- `backend/app/ml/eval/evaluator.py` — Eval harness: 300-row stratified hold-out, classification report, writes metrics.json + eval_report.md
- `backend/app/ml/eval/metrics.json` — **Real F1 numbers** on 300 held-out reviews
- `backend/app/ml/eval/eval_report.md` — Human-readable eval report
- `backend/app/services/absa_service.py` — Pipeline orchestrator: lazy model loading, runs sentiment + aspects + embeddings + clusters, writes insert-only SentimentResult rows
- `backend/tests/unit/test_absa.py` — 22 unit tests across all 4 ML modules using real fixture data

#### Eval Results (threshold=0.90, N=300 held-out)
- Positive F1: 0.76 | Negative F1: 0.68 | Neutral F1: 0.18 | **Macro F1: 0.54**
- Negative recall: 0.91 — catches 91% of real negative reviews (critical for brand monitoring)

#### Verified
- Command: `python -m pytest backend/tests/unit/test_absa.py -v` → `22 passed in 150s`
- Command: `python -m pytest backend/tests/ -v` (non-ML) → `37 passed in 7.73s`
- Command: `python -m backend.app.ml.eval.evaluator` → metrics.json + eval_report.md written
- Total test count across all phases: **59 tests passing**

---

## [0.3.0] - 2026-07-27


### Phase 1.5 — Auth

#### Added
- `backend/app/auth/security.py` — bcrypt password hashing (direct `bcrypt` lib, Python 3.13 compatible) + JWT access/refresh token creation and decode
- `backend/app/auth/schemas.py` — `SignupRequest`, `LoginRequest`, `TokenResponse`, `UserRead` Pydantic schemas
- `backend/app/auth/dependencies.py` — `get_current_user` FastAPI dependency (validates Bearer JWT, returns User or 401)
- `backend/app/auth/router.py` — `POST /auth/signup`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` endpoints
- `backend/tests/conftest.py` — shared pytest fixtures with in-memory SQLite + TestClient (no Docker required for tests)
- `backend/tests/unit/test_auth.py` — 11 unit tests: bcrypt hashing, JWT round-trips, token type enforcement, schema validation
- `backend/tests/integration/test_auth_integration.py` — 12 integration tests hitting real HTTP endpoints

#### Verified
- Command: `python -m pytest backend/tests/ -v`
- Output: `37 passed in 6.26s`
- **Authorization test explicitly verified**: user A's valid token returns only user A's profile, not user B's
- Passwords never returned in any API response; generic error messages prevent email enumeration

---

## [0.2.0] - 2026-07-27


### Phase 1 — Data Foundation

#### Added
- `backend/app/models/` — SQLModel ORM models: `User`, `Product`, `Review`, `SentimentResult`, `Alert`, `QueryLog`
  - Every model is `user_id`-scoped from day one (no retrofit needed for auth)
  - `SentimentResult` is insert-only (timestamped) to power real trend history
- `backend/app/db/session.py` — DB engine, session factory, `create_db_and_tables()`
- `backend/app/schemas/review.py` — Pydantic `ReviewIngest` schema with rating + sentiment validators
- `backend/app/schemas/product.py` — Pydantic Product schemas
- `scripts/load_reviews.py` — CSV → Postgres loader with Pydantic row validation, batch commits, product upsert
- `scripts/inspect_dataset.py` — quick dataset stats utility
- `backend/tests/fixtures/sample_reviews.csv` — 50 real Amazon review rows (checked in as test fixture)
- `backend/tests/unit/test_data_models.py` — 9 unit tests on real fixture data (no Faker)
- `data/raw/amazon_reviews_nlp_ready-1.csv` — 28,332 Amazon reviews copied from Electrohack_nlp baseline (gitignored)

#### Verified
- Command: `python -m pytest backend/tests/unit/test_data_models.py -v`
- Output: `9 passed in 0.50s`
- All 50 fixture rows pass Pydantic validation including rating range and sentiment label checks

---

## [0.1.0] - 2026-07-17


### Added
- Initial directory structure configuration.
- `pyproject.toml` packaging template and dependency definitions.
- `.gitignore` rule declarations.
- Local configuration template `.env.example` and `.env` template copies.
- `Makefile` automating task execution (install, test, lint, database).
- Quality check configuration `.pre-commit-config.yaml`.
- FastAPI application instance, health route, structlog configuration, and unit tests.
- Pytest testing framework setup and unit test execution client.
- Docker-compose definition for Postgres (with pgvector support) and Redis.
- Automated CI pipeline run on push/pull requests in `.github/workflows/ci.yml`.
- Migrated aspect extractor, keyword extractor, overall sentiment calculator, and review summarizer from baseline hackathon repository.
- Blueprint docs: vision, master build prompt, architecture layout, and Phase 0 log.
