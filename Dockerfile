# --- Etapa 1: Constructor ---
FROM python:3.13.9-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /install

# Copiamos solo los requisitos para aprovechar el cache de capas
COPY zgestion_files/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Etapa 2: Imagen Final ---
FROM python:3.13.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copiamos las librerías ya instaladas del builder
COPY --from=builder /install /usr/local

# Copiamos el código fuente (el .dockerignore evitará la basura)
COPY . .

# Limpieza radical de restos de desarrollo
RUN rm -rf Datasets MLOPS_Simulado zgestion_files/requirements* \
    && find . -name "__pycache__" -type d -exec rm -rf {} +

EXPOSE 8050

# Uso threads=4 para que Dash no se bloquee con un solo usuario, 
# pero mantengo workers=1 para no duplicar la RAM.
CMD ["gunicorn", "-b", "0.0.0.0:8050", "app:server", "--workers=1", "--threads=4", "--timeout=120"]