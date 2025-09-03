



##DOCKER

docker-compose up --build -d

Siempre migrar si lo montas con docker (/analyst)
docker exec -it django_web python macro_vtf/manage.py migrate

docker exec -it macro_vtf_web python manage.py createsuperuser

docker exec -it macro_vtf_web bash
chown appuser:appuser /app/db/db.sqlite3

