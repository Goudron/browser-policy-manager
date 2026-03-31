.PHONY: run dev test test-firefox-live setup-firefox-live-browsers coverage fmt lint

PYTEST ?= $(if $(wildcard .venv/bin/pytest),.venv/bin/pytest,pytest)

run:
	uvicorn app.main:app --reload --port 8000

dev:
	uvicorn app.main:app --reload --port 8000

test:
	$(PYTEST)

test-firefox-live:
	$(PYTEST) -m firefox_live -q

setup-firefox-live-browsers:
	bash tools/setup_firefox_live_browsers.sh release

coverage:
	$(PYTEST) --cov=app --cov-branch --cov-report=term-missing --cov-report=xml --cov-report=html
	@echo "HTML coverage report: file://$$(pwd)/htmlcov/index.html"

fmt:
	ruff check --select I --fix .
	ruff format .

lint:
	ruff check .
