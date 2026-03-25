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
