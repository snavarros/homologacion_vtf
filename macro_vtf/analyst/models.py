from django.db import models
from django.contrib.auth.models import User


class Region(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return self.usuario.username


def user_file_path(instance, filename):
    # ext = filename.split(".")[-1]
    process = instance.proceso
    mes = instance.mes
    anio = instance.anio
    region = instance.region
    username = instance.usuario.username
    filename = f"{process}_{mes}_{anio}_{username}.csv"
    return f"region_{region}/{anio}/{mes}/{filename}"


class ArchivoSubido(models.Model):
    PROCESOS = [
        ("planilla_validadora", "Planilla Validadora"),
        ("macro", "Macro"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    region = models.IntegerField()
    anio = models.IntegerField()
    mes = models.IntegerField()
    archivo = models.FileField(upload_to=user_file_path)
    proceso = models.CharField(max_length=30, choices=PROCESOS)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "region", "anio", "mes", "proceso")
