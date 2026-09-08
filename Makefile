.PHONY: setup test test-unit test-integration test-coverage lint format run

setup:
	python -m venv .venv
	.venv/Scripts/python -m pip install -r requirements.txt
	.venv/Scripts/python -m playwright install chromium

test:
	.venv/Scripts/python -m pytest -q

test-unit:
	.venv/Scripts/python -m pytest tests/unit -q

test-integration:
	.venv/Scripts/python -m pytest tests/integration -q

test-coverage:
	.venv/Scripts/python -m pytest --cov=app --cov-report=term-missing -q

lint:
	.venv/Scripts/python -m flake8 src tests

format:
	.venv/Scripts/python -m black --line-length 100 src tests
	.venv/Scripts/python -m isort src tests

run:
	cd src && ../.venv/Scripts/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
