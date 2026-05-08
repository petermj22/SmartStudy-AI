# ============================================================
# SmartStudy — Makefile
# ============================================================

.PHONY: install dev test lint format run clean help

PYTHON := python
PIP := pip
STREAMLIT := streamlit

help:  ## Show available commands
	@echo SmartStudy Development Commands
	@echo ================================
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install production dependencies
	$(PIP) install -r requirements.txt

dev:  ## Install development dependencies
	$(PIP) install -r requirements-dev.txt

run:  ## Run the Streamlit application
	$(STREAMLIT) run frontend/app.py \
		--theme.base=dark \
		--theme.primaryColor="#6C63FF" \
		--theme.backgroundColor="#0F0F1A" \
		--theme.secondaryBackgroundColor="#1A1A2E" \
		--theme.textColor="#EAEAEA"

test:  ## Run all tests
	$(PYTHON) -m pytest tests/ -v --tb=short

test-cov:  ## Run tests with coverage
	$(PYTHON) -m pytest tests/ -v --cov=backend --cov-report=html --cov-report=term

lint:  ## Run linter (ruff)
	$(PYTHON) -m ruff check backend/ frontend/ ml_training/ tests/

format:  ## Format code (black)
	$(PYTHON) -m black backend/ frontend/ ml_training/ tests/

typecheck:  ## Run type checker (mypy)
	$(PYTHON) -m mypy backend/ --ignore-missing-imports

train-ensemble:  ## Train ensemble classifier
	$(PYTHON) ml_training/train_ensemble.py

train-lstm:  ## Train LSTM fatigue predictor
	$(PYTHON) ml_training/train_lstm.py

clean:  ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage dist build *.egg-info
	rm -rf logs/*.log
