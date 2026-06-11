.PHONY: up down build logs migrate test clean

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

migrate:
	docker-compose exec postgres psql -U invoices_user -d invoices_db -f /docker-entrypoint-initdb.d/001_initial_schema.sql
	docker-compose exec postgres psql -U invoices_user -d invoices_db -f /docker-entrypoint-initdb.d/002_materialized_views.sql

test:
	docker-compose run --rm auth_service pytest tests/ -v
	docker-compose run --rm document_service pytest tests/ -v
	docker-compose run --rm materials_service pytest tests/ -v

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Development
dev-backend:
	cd backend && uvicorn auth_service.main:app --reload --port 8001 &

# Testing
test-unit:
	pytest backend/ -v --tb=short -x

test-coverage:
	pytest backend/ --cov=backend --cov-report=html --cov-report=term-missing

# Docker helpers
ps:
	docker-compose ps

restart:
	docker-compose restart $(service)

scale-workers:
	docker-compose up -d --scale segmentation_worker=2 --scale ocr_worker=3

# Utilities
shell-db:
	docker-compose exec postgres psql -U invoices_user -d invoices_db

shell-redis:
	docker-compose exec redis redis-cli

minio-init:
	docker-compose run --rm minio_init

flower:
	docker-compose exec segmentation_worker celery -A workers.segmentation_worker.celery_app flower --port=5555
