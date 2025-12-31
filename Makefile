.PHONY: help install install-dev test coverage lint format type-check check clean run-search run-filter

# Default target - show help
help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install all dependencies including dev tools"
	@echo "  make test          - Run tests with coverage report"
	@echo "  make coverage      - Run tests and open HTML coverage report"
	@echo "  make lint          - Run flake8 linter"
	@echo "  make format        - Format code with black"
	@echo "  make format-check  - Check code formatting without modifying"
	@echo "  make type-check    - Run mypy type checker"
	@echo "  make check         - Run all quality checks (format, lint, type-check, test)"
	@echo "  make clean         - Remove cache files and build artifacts"
	@echo "  make run-search    - Run search_sra.py (set ARGS='...' for arguments)"
	@echo "  make run-filter    - Run filter_metadata.py (set ARGS='...' for arguments)"

# Installation targets
install:
	pip install -r requirements.txt

install-dev: install
	pip install pre-commit
	pre-commit install

# Testing targets
test:
	pytest tests/ --cov=scripts --cov-report=term-missing --cov-report=html

coverage: test
	@echo "Opening coverage report..."
	@which xdg-open > /dev/null && xdg-open htmlcov/index.html || \
	which open > /dev/null && open htmlcov/index.html || \
	echo "Coverage report generated in htmlcov/index.html"

# Code quality targets
lint:
	flake8 scripts/ tests/

format:
	black scripts/ tests/

format-check:
	black --check --diff scripts/ tests/

type-check:
	mypy scripts/

# Run all quality checks
check: format-check lint type-check test
	@echo "✅ All quality checks passed!"

# Cleanup targets
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Run scripts (examples)
run-search:
	python scripts/search_sra.py $(ARGS)

run-filter:
	python scripts/filter_metadata.py $(ARGS)
