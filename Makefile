# python -m gunicorn -b 0.0.0.0:8050 app:server --timeout 120
# nice -n 19 python -m gunicorn -b 0.0.0.0:8050 app:server --timeout 120


# Variables
COMPOSE_FILE = docker-compose.yml
CONTAINER_NAME = mi_app_dash
PORT = 8050

.PHONY: run_dev run_dev_c run_dev_build run_server build up down restart logs clean make_tar_datasets help

## Desarrollo local
run_dev:
	@echo "🚀 Iniciando en modo desarrollo..."
	@nice -n 19 python3 app.py

run_dev_c:
	@echo "🚀 Iniciando en modo desarrollo con Docker Compose y límites de recursos..."
	@docker compose -f docker-compose.dev.yml --compatibility up --build

run_dev_build:
	@echo "🚀 Rebuilding imagen de desarrollo sin cache y levantando el servicio..."
	@docker compose -f docker-compose.dev.yml build --no-cache dash-dev
	@docker compose -f docker-compose.dev.yml --compatibility up

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


##################################################################
##### Test
##################################################################
python = .venv/bin/python
# shell := /bin/bash
test_control_yml:
	@$(python) generate_control_yml.py
	@echo "✅ Archivo test_control.yml generado correctamente"

