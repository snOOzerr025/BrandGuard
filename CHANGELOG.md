# Changelog

All notable changes to this project will be documented in this file.

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
