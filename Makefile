.PHONY: run seed test lint format

run:
	uv run uvicorn app.main:app --reload

seed:
	uv run python -m scripts.seed

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .
