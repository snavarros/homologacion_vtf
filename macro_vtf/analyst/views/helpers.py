import os

from django.http import FileResponse, Http404
from analyst.services.planilla_validadora import PlanillaValidadora
from macro_vtf import settings


def validar_perfil(perfil):
    if not perfil or not perfil.region:
        return False, ["No tiene una región asignada. No puede subir archivos."]
    return True, []


def validar_archivo(nombre_archivo):
    if not nombre_archivo.endswith((".xls", ".xlsx", ".csv")):
        return False, [
            "Formato de archivo no permitido. Solo se permiten .xls, .xlsx o .csv."
        ]
    return True, []


def validar_columnas_y_convertir(archivo, tipo):
    validador = PlanillaValidadora(tipo)
    df = validador.cargar_archivo(archivo)

    if isinstance(df, str):
        return False, [df]  # error de carga

    valido, errores = validador.validar(df)
    if not valido:
        return False, errores

    return True, df


def descargar_plantilla_excel(request):
    file_path = os.path.join(
        settings.BASE_DIR,
        "analyst",
        "static",
        "plantillas",
        "plantilla_validadora.xlsx",
    )
    if os.path.exists(file_path):
        return FileResponse(
            open(file_path, "rb"),
            as_attachment=True,
            filename="plantilla_validadora.xlsx",
        )
    else:
        raise Http404("El archivo no existe.")
