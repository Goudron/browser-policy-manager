.PHONY: run dev test coverage fmt lint

run:
	uvicorn app.main:app --reload --port 8000

dev:
	uvicorn app.main:app --reload --port 8000

test:
	pytest

coverage:
	pytest --cov=app --cov=tests --cov-report=html
	@echo "HTML coverage report: file://$$(pwd)/htmlcov/index.html"

fmt:
	ruff check --select I --fix .
	ruff format .

lint:
	ruff check .
