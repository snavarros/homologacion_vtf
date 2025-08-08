from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from analyst.views.dashboard import dashboard
from analyst.views.uploads import (
    subir_planilla_validadora,
    listar_archivos_subidos,
    eliminar_archivo_subido,
)

from analyst.views.parametros import (
    subir_parametro_remuneracional,
    eliminar_parametro_remuneracional,
)

from analyst.views.consolidar import (
    consolidar_archivos,
    consolidar_semestre_anterior,
)
from analyst.views.diccionarios import diccionario_planilla_validadora
from analyst.views.helpers import descargar_plantilla_excel

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
    path("dashboard/", dashboard, name="dashboard"),
    path(
        "subir/planilla_validadora/",
        subir_planilla_validadora,
        name="subir_planilla_validadora",
    ),
    path("consolidar/", consolidar_archivos, name="consolidar_archivos"),
    path(
        "descargar/plantilla_excel/",
        descargar_plantilla_excel,
        name="descargar_plantilla_excel",
    ),
    path("mis-archivos/", listar_archivos_subidos, name="listar_archivos_subidos"),
    path(
        "eliminar_archivo/<int:archivo_id>/",
        eliminar_archivo_subido,
        name="eliminar_archivo_subido",
    ),
    path(
        "consolidar/semestre-anterior/",
        consolidar_semestre_anterior,
        name="consolidar_semestre_anterior",
    ),
    path(
        "subir-parametro-remuneracional/",
        subir_parametro_remuneracional,
        name="subir_parametro_remuneracional",
    ),
    path(
        "parametro_remuneracional/eliminar/<int:pk>/",
        eliminar_parametro_remuneracional,
        name="eliminar_parametro_remuneracional",
    ),
    path(
        "diccionario-planilla-validadora/",
        diccionario_planilla_validadora,
        name="diccionario_planilla_validadora",
    ),
]
