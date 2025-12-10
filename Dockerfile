# Dockerfile
FROM python:3.13.9-slim

# Evita que Python genere archivos .pyc y fuerza salida no bufferizada (para ver logs en tiempo real)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias
COPY zgestion_files/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Exponer el puerto
EXPOSE 8050

# COMANDO DE ARRANQUE (Crucial)
# Usamos Gunicorn.
# IMPORTANTE: --workers 1. 
# Como usas una variable global (MAPA_DF) para guardar datos en memoria, 
# NO puedes usar múltiples workers (procesos), porque no comparten memoria.
# Usamos --threads 4 para manejar concurrencia compartiendo la RAM.
# CMD ["gunicorn", "-b", "0.0.0.0:8050", "app:server", "--workers=1", "--threads=4", "--timeout=120"]
CMD ["gunicorn", "-b", "0.0.0.0:8050", "app:server", "--workers=1", "--threads=1"]  