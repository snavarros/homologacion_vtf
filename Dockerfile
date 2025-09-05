# Stage 2: production
FROM python:3.13-slim

# Crear usuario y app
RUN useradd -m -r appuser && mkdir -p /app/macro_vtf/db && chown -R appuser /app

WORKDIR /app

# Copiar dependencias de builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copiar la app
COPY --chown=appuser:appuser . .

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cambiar a usuario no root
USER appuser

EXPOSE 8000

# Comando: collectstatic + gunicorn
CMD ["sh", "-c", "mkdir -p /app/macro_vtf/db && python manage.py collectstatic --noinput && gunicorn macro_vtf.wsgi:application --bind 0.0.0.0:8000 --workers=3"]

