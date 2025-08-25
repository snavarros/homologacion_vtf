import os
import re
import pandas as pd
from django.http import FileResponse, Http404
from analyst.services.planilla_validadora import PlanillaValidadora
from macro_vtf import settings

from analyst.df_utils.agregar_columnas import (
    agregar_columna_region,
    agregar_fecha,
    agregar_antiguedad_dias,
)
from analyst.df_utils.calculos import (
    calcular_brecha,
    calcular_promedio_semestre_anterior,
    obtener_parametro_remuneracional_df,
    obtener_valores_por_region_cargo,
)
from analyst.df_utils.consolidar import consolidar_sueldos


columnas = [
    "COD_REGION",
    "CODIGO_ESTABLECIMIENTO",
    "NOMBRE_ESTABLECIMIENTO",
    "RUT",
    "NOMBRE",
    "APELLIDO_PATERNO",
    "APELLIDO_MATERNO",
    "FECHA_NACIMIENTO",
    "CARGO",
    "FUNCION",
    "GRUPO",
    "NIVEL_ATENCION",
    "FECHA_INGRESO_SISTEMA_ESCOLAR",
    "ANIOS_SERVICIO_CON_EMPLEADOR",
    "FECHA_ESTABLECIDA_CONTRATO",
    "JORNADA_HORAS",
    "PLAZO_CONTRATO",
    "TIPO_CONTRATO",
    "NIVEL_EDUCACIONAL",
    "TITULO",
    "INSTITUCION_ACADEMICA",
    "ANTIGUEDAD_DIAS",
    "VALOR_PR",
    "PROMEDIO_SUELDO",
    "BRECHA",
    "DETALLE_MESES",
]


def calcular_homologacion(
    df: pd.DataFrame,
    anio_consultado: int,
    mes_consultado: int,
) -> pd.DataFrame:
    """
    Retorna df con los calculos de la homologacion

    Args:
        df (pd.DataFrame): DataFrame de entrada
        anio_consultado (int): Año de referencia
        mes_consultado (int): Mes de referencia

    Returns:
        pd.DataFrame: DataFrame con cálculos de homologación
    """

    # Crear una copia y normalizar cabeceras
    df_original = df.copy()
    df_original.columns = [col.upper() for col in df_original.columns]

    fecha_referencia = pd.to_datetime(f"{anio_consultado}-{mes_consultado:02d}-01")

    # Crear DataFrame BASE (MES, ANIO consultado)
    df_base = df_original[
        (df_original["ANIO"] == anio_consultado)
        & (df_original["MES"] == mes_consultado)
    ].copy()

    df_base = df_base.drop_duplicates(subset=["CODIGO_ESTABLECIMIENTO", "RUT"])

    df_base["TIENE_ERRORES"] = False
    df_original["TIENE_ERRORES"] = False
    df_base["LOG_ERRORES"] = ""
    df_original["LOG_ERRORES"] = ""

    # Agregar REGION
    df_original = agregar_columna_region(df_original)
    df_base = agregar_columna_region(df_base)

    # Agregar FECHA_REFERENCIA
    df_base = agregar_fecha(df_base, anio_consultado, mes_consultado)
    df_original = agregar_fecha(df_original, anio_consultado, mes_consultado)

    # Calcular ANTIGUEDAD_DIAS
    df_base = agregar_antiguedad_dias(df_base, fecha_referencia)
    df_original = agregar_antiguedad_dias(df_original, fecha_referencia)

    # Obtener parámetros remuneracionales
    if mes_consultado > 6:
        anio_param = anio_consultado + 1
    else:
        anio_param = anio_consultado
    df_param = obtener_parametro_remuneracional_df(anio_param)
    df_param.columns = [col.upper() for col in df_param.columns]

    # Agregar valores remuneracionales
    df_base = obtener_valores_por_region_cargo(df_base, df_param)

    df_consolidado = consolidar_sueldos(df_original)

    # 2. Recuperar la columna ANTIGUEDAD_DIAS
    df_antiguedad = df_base[
        ["CODIGO_ESTABLECIMIENTO", "RUT", "ANTIGUEDAD_DIAS"]
    ].drop_duplicates()

    # 3. Merge para agregar la columna
    df_consolidado = df_consolidado.merge(
        df_antiguedad, on=["CODIGO_ESTABLECIMIENTO", "RUT"], how="left"
    )

    # --- Detectar columnas de sueldos (las que tienen guión o formato YYYY_MM)
    col_sueldos = [
        c for c in df_consolidado.columns if re.fullmatch(r"\d{4}_\d{1,2}", str(c))
    ]

    # --- Aplicar la función para calcular promedio semestre anterior
    df_consolidado[["PROMEDIO_SUELDO", "DETALLE_MESES"]] = df_consolidado.apply(
        lambda row: calcular_promedio_semestre_anterior(
            row,
            mes_consultado=mes_consultado,
            anio_consultado=anio_consultado,
            col_sueldos=col_sueldos,
        ),
        axis=1,
    )

    df_merge = df_base.merge(
        df_consolidado,
        on=["CODIGO_ESTABLECIMIENTO", "RUT", "ANTIGUEDAD_DIAS"],
        how="left",
    )

    df_merge = calcular_brecha(df_merge)

    # Seleccionar las columans que se necesitan
    df_merge = df_merge[columnas]

    return df_merge


def validar_planilla_mensual(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Validar Extension del archivo xlsx, xls, csv.

    # 2. Limpiar dataframe eliminando espacios y columnas vacias.

    # 3. Validar que el archivo subido tenga el mes y anio correspondiente.

    # 4. Validar que existan todas las columnas solicitadas.

    # 5. Validar columna RUT

    # 6. Validar que las columnas sean del tipo correcto (Numerico, String)

    # 7. Validar que las columnas tengan valores dentro de los rangos permitidos (MES: 1 al 12)

    # 8. Validar que ciertas columnas solo tengan ciertos  valores (CARGO: Administrativo, Auxiliar ...)

    pass


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
