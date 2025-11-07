#!/bin/bash
set -e  # Detener si hay error

# Verificar que el archivo existe
if [ ! -f "gunicorn.service" ]; then
    echo "❌ Error: gunicorn.service no encontrado en el directorio actual"
    exit 1
fi

echo "📋 Copiando gunicorn.service a /etc/systemd/system/"
sudo cp gunicorn.service /etc/systemd/system/gunicorn.service

echo "🔄 Recargando daemon de systemd..."
sudo systemctl daemon-reload

echo "🚀 Iniciando servicio gunicorn..."
sudo systemctl start gunicorn

echo "✅ Habilitando gunicorn para inicio automático..."
sudo systemctl enable gunicorn

echo "📊 Estado del servicio:"
sudo systemctl status gunicorn --no-pager

echo ""
echo "✅ Instalación completada!"
echo "Para ver logs: sudo journalctl -u gunicorn -f"
echo "Para parar: sudo systemctl stop gunicorn"
echo "Para reiniciar: sudo systemctl restart gunicorn"
