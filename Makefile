.PHONY: up down test logs rebuild generate

# Subir tudo
up:
	docker compose up -d --build

# Parar tudo
down:
	docker compose down

# Testes
test:
	docker compose up -d postgres
	sleep 3
	docker compose run --rm api python -m pytest tests/ -v

# Logs da API
logs:
	docker compose logs -f api

# Rebuild da API
rebuild:
	docker compose up -d --build api

# Gerar 1 vídeo (produto automático)
generate:
	curl -s -X POST http://localhost:8090/pipeline/full | python3 -m json.tool

# Gerar N vídeos
batch:
	curl -s -X POST "http://localhost:8090/pipeline/batch?count=3" | python3 -m json.tool

# Health check
health:
	curl -s http://localhost:8090/health | python3 -m json.tool
