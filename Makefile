.PHONY: test lint fmt check install dev clean

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --tb=short --cov=augent --cov-report=term-missing

lint:
	ruff check .
	black --check .

fmt:
	ruff check . --fix
	black .

check: lint test

install:
	pip install -e .

dev:
	pip install -e .[dev]

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
