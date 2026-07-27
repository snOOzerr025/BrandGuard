.PHONY: install lint format test up down dev clean

install:
	pip install -e ".[dev,ml]"

lint:
	ruff check backend/
	black --check backend/
	isort --check backend/

format:
	black backend/
	isort backend/
	ruff check backend/ --fix

test:
	pytest backend/tests/ -v

up:
	docker-compose up -d

down:
	docker-compose down

dev:
	uvicorn backend.app.main:app --reload --port 8000

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "build" -exec rm -r {} +
	find . -type d -name "dist" -exec rm -r {} +
