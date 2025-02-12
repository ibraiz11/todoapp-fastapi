.PHONY: install install-dev run build up down test lint format clean

install:
	uv pip install -r requirements.txt

install-dev:
	uv pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete