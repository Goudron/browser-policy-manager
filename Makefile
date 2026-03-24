.PHONY: run dev test coverage fmt lint

PYTEST ?= $(if $(wildcard .venv/bin/pytest),.venv/bin/pytest,pytest)

run:
	uvicorn app.main:app --reload --port 8000

dev:
	uvicorn app.main:app --reload --port 8000

test:
	$(PYTEST)

coverage:
	$(PYTEST) --cov=app --cov-branch --cov-report=term-missing --cov-report=xml --cov-report=html
	@echo "HTML coverage report: file://$$(pwd)/htmlcov/index.html"

fmt:
	ruff check --select I --fix .
	ruff format .

lint:
	ruff check .
