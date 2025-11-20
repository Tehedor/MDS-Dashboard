#!/bin/bash
set -e  # Detener si hay error

# Verificar que el archivo existe
if [ ! -f "gunicorn.service" ]; then
    echo "❌ Error: gunicorn.service no encontrado en el directorio actual"
    exit 1
fi

echo "📋 Copiando gunicorn.service a /etc/systemd/system/"
cp gunicorn.service /etc/systemd/system/gunicorn.service

echo "🔄 Recargando daemon de systemd..."
systemctl daemon-reload

echo "🚀 Iniciando servicio gunicorn..."
systemctl start gunicorn

echo "✅ Habilitando gunicorn para inicio automático..."
systemctl enable gunicorn

echo "📊 Estado del servicio:"
systemctl status gunicorn --no-pager

echo ""
echo "✅ Instalación completada!"
echo "Para ver logs: journalctl -u gunicorn -f"
echo "Para parar: systemctl stop gunicorn"
echo "Para reiniciar: systemctl restart gunicorn"
