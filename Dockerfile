# ----------------------------
# Stage 2: Production
# ----------------------------
FROM python:3.13-slim

# Crear usuario no root
RUN useradd -m -r appuser

WORKDIR /app

# Copiar dependencias del builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copiar la app con estáticos ya recolectados
COPY --from=builder /app /app

# Copiar entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cambiar a usuario no root
USER appuser

EXPOSE 8000

# Usar entrypoint
ENTRYPOINT ["/entrypoint.sh"]
