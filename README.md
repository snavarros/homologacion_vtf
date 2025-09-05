

## SQLITE
Se espera solo almacenar usuarios y no tener una base de datos en si momentaneamente, ya que se retornaran archivos xlsx o csv para ser respaldados en sharepoint.

## DOCKER

```
docker-compose up --build -d
```

Siempre migrar si lo montas con docker (/analyst)
```
docker exec -it django_vtf python macro_vtf/manage.py migrate

docker exec -it django_vtf python manage.py createsuperuser
```
```
docker exec -it django_vtf bash
> chown appuser:appuser /app/db/db.sqlite3
```
