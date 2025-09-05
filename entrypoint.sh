#!/bin/sh

set -e

echo "📦 Ejecutando makemigrations..."
python manage.py makemigrations --noinput

echo "📦 Ejecutando migrate..."
python manage.py migrate --noinput

echo "👤 Creando superusuario si no existe..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="junjivtf").exists():
    User.objects.create_superuser("junjivtf", "snavarro@junji.cl", "Perro1313")
    print("✅ Superusuario creado: junjivtf")
else:
    print("ℹ️ Superusuario 'junjivtf' ya existe")
EOF

echo "🚀 Iniciando Gunicorn..."
exec gunicorn macro_vtf.wsgi:application --bind 0.0.0.0:8000 --workers=3
