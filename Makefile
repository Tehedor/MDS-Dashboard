# python -m gunicorn -b 0.0.0.0:8050 app:server --timeout 120
# nice -n 19 python -m gunicorn -b 0.0.0.0:8050 app:server --timeout 120


# Variables
COMPOSE_FILE = docker-compose.yml
CONTAINER_NAME = mi_app_dash
PORT = 8050

.PHONY: run_dev run_server build up down restart logs clean make_tar_datasets help

## Desarrollo local
run_dev:
	@echo "🚀 Iniciando en modo desarrollo..."
	@nice -n 19 python3 app.py

run_server:
	@echo "🚀 Iniciando con Gunicorn (producción local)..."
	@nice -n 19 python -m gunicorn -b 0.0.0.0:$(PORT) app:server --workers=1 --threads=4 --timeout=120

make_tar_datasets:
	@echo "📦 Creando archivo comprimido de Datasets..."
	@tar -czvf Datasets.tar.gz Datasets/

extract_tar_datasets:
	@echo "📂 Extrayendo Datasets.tar.gz..."
	@tar -xzvf Datasets.tar.gz
	@echo "✅ Datasets extraídos correctamente"



run:
	@echo "🚀 Iniciando contenedor Docker..."
	@docker compose up --build 