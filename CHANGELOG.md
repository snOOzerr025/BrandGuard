# Changelog

All notable changes to this project will be documented in this file.

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
