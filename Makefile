.PHONY: up down test logs

up:
	docker compose up -d --build

down:
	docker compose down

test:
	docker compose up -d postgres
	sleep 3
	docker compose run --rm creative-api python -m pytest tests/ -v

logs:
	docker compose logs -f creative-api

rebuild:
	docker compose up -d --build creative-api
