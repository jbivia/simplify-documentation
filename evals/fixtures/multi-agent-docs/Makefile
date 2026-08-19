.PHONY: install test lint fmt scan

install:   ## Sync the locked environment
	uv sync

test:      ## Unit tests
	uv run pytest

lint:      ## Ruff check
	uv run ruff check src tests

fmt:       ## Ruff format
	uv run ruff format src tests

scan:      ## Poll every feed once
	uv run feedscan scan
