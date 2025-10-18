.PHONY: lint format test typecheck all

lint:
	ruff check .

format:
	ruff check . --fix
	ruff format .

typecheck:
	mypy app

test:
	pytest -q

all: format lint typecheck test
