from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="analyst/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page=reverse_lazy("login")),
        name="logout",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "subir/planilla_validadora/",
        views.subir_planilla_validadora,
        name="subir_planilla_validadora",
    ),
    path("consolidar/", views.consolidar_archivos, name="consolidar_archivos"),
    path(
        "descargar/plantilla_excel/",
        views.descargar_plantilla_excel,
        name="descargar_plantilla_excel",
    ),
    path(
        "mis-archivos/", views.listar_archivos_subidos, name="listar_archivos_subidos"
    ),
    path(
        "eliminar_archivo/<int:archivo_id>/",
        views.eliminar_archivo_subido,
        name="eliminar_archivo_subido",
    ),
]
