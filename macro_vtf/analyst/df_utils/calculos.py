import pandas as pd
import numpy as np

from analyst.models import ParametroRemuneracional


# Diccionario de meses abreviados en español
MESES = {
    1: "ENE",
    2: "FEB",
    3: "MAR",
    4: "ABR",
    5: "MAY",
    6: "JUN",
    7: "JUL",
    8: "AGO",
    9: "SEP",
    10: "OCT",
    11: "NOV",
    12: "DIC",
}


def calcular_antiguedad(df: pd.DataFrame, col_inicio: str, col_fin: str) -> pd.Series:
    """
    Calcula antigüedad en años entre dos columnas de fechas.
    """
    return (pd.to_datetime(df[col_fin]) - pd.to_datetime(df[col_inicio])).dt.days / 365


def obtener_parametro_remuneracional_df(anio: int) -> pd.DataFrame:
    try:
        # Busca el registro por año
        parametro = ParametroRemuneracional.objects.get(anio=anio)

        # Ruta completa del archivo
        archivo_path = parametro.archivo.path

        # Detectar formato y cargar en DataFrame
        if archivo_path.endswith(".xlsx") or archivo_path.endswith(".xls"):
            df = pd.read_excel(archivo_path)
        elif archivo_path.endswith(".csv"):
            df = pd.read_csv(archivo_path)
        else:
            raise ValueError("Formato de archivo no soportado")

        return df

    except ParametroRemuneracional.DoesNotExist:
        raise ValueError(f"No existe parámetro remuneracional para el año {anio}")


def obtener_valores_por_region_cargo(
    df_personas: pd.DataFrame,
    df_valores: pd.DataFrame,
    col_region: str = "COD_REGION",
    col_cargo: str = "CARGO",
    nombre_col_valor: str = "VALOR_PR",
) -> pd.DataFrame:
    """
    Asigna a cada persona el valor correspondiente según su región y cargo.

    Parámetros
    ----------
    df_personas : DataFrame
        Debe contener al menos las columnas [col_region, col_cargo].
    df_valores : DataFrame
        Debe contener la columna [col_region] y varias columnas de cargos
        (una columna por cada tipo de cargo con su valor).
    col_region : str
        Nombre de la columna de región (por defecto 'REGION').
    col_cargo : str
        Nombre de la columna de cargo (por defecto 'CARGO').
    nombre_col_valor : str
        Nombre de la nueva columna donde se pondrá el valor encontrado.

    Retorna
    -------
    DataFrame
        df_personas con una columna extra [nombre_col_valor] que contiene
        el valor correspondiente según región y cargo.
    """

    # Normalizar a mayúsculas para evitar problemas de matching
    df_personas[col_cargo] = df_personas[col_cargo].str.upper()
    df_valores = df_valores.rename(
        columns={c: c.upper() for c in df_valores.columns}
    )  # asegurar columnas en mayúscula también

    # Paso 1: convertir df_valores a formato largo
    df_valores_melt = df_valores.melt(
        id_vars=col_region, var_name=col_cargo, value_name=nombre_col_valor
    )

    # Normalizar también la columna de cargos del melt
    df_valores_melt[col_cargo] = df_valores_melt[col_cargo].str.upper()

    # Paso 2: unir con df_personas
    df_resultado = df_personas.merge(
        df_valores_melt, on=[col_region, col_cargo], how="left"
    )

    return df_resultado


def calcular_promedio_semestre_anterior(
    row, mes_consultado, anio_consultado, col_sueldos, antiguedad_col="ANTIGUEDAD_DIAS"
):
    """
    Calcula el promedio de sueldos del semestre anterior en base a antigüedad.
    Devuelve también el detalle de los meses y sueldos utilizados.
    """

    # Antigüedad expresada en meses y días
    antiguedad_total_dias = int(row[antiguedad_col])
    antiguedad_meses = antiguedad_total_dias // 30
    dias_restantes = antiguedad_total_dias % 30

    # Determinar semestre anterior
    if mes_consultado >= 7:
        anio_semestre = anio_consultado
        meses_objetivo = list(range(1, 7))  # enero–junio
    else:
        anio_semestre = anio_consultado - 1
        meses_objetivo = list(range(7, 13))  # julio–diciembre

    # Determinar cuántos meses usar
    meses_a_considerar = min(6, max(1, int(antiguedad_meses)))

    # Seleccionar últimos N meses del semestre anterior
    meses_finales = meses_objetivo[-meses_a_considerar:]

    # Seleccionar columnas de sueldo correspondientes
    cols_objetivo = [
        f"{anio_semestre}_{m}"
        for m in meses_finales
        if f"{anio_semestre}_{m}" in col_sueldos
    ]

    # Extraer sueldos
    sueldos = row[cols_objetivo]

    # Validación: si debería haber sueldo en esos meses y no está → error
    if sueldos.isna().any() or sueldos.empty:
        return pd.Series(
            {
                "PROMEDIO_SUELDO": np.nan,
                "DETALLE_MESES": "ERROR: falta sueldo en meses requeridos",
            }
        )

    # Crear detalle con formato ENE_2025
    detalle = [
        (f"{MESES[int(col.split('_')[1])]}_{col.split('_')[0]}", row[col])
        for col in cols_objetivo
    ]

    if antiguedad_meses < 4:
        return pd.Series(
            {
                "PROMEDIO_SUELDO": np.nan,
                "DETALLE_MESES": "ERROR: menos de 4 meses de antigüedad",
            }
        )
    elif antiguedad_meses == 4 and dias_restantes == 0:
        # ✅ Caso exacto 4 meses
        promedio = sueldos.mean()
    elif antiguedad_meses == 4 and dias_restantes > 0:
        # ⚡ regla especial: proporcional
        promedio = sueldos.mean() * (antiguedad_total_dias / (4 * 30))
    elif antiguedad_meses < 6:
        # 5 meses (con o sin días)
        promedio = sueldos.mean()
    else:
        # 6 o más meses
        # promedio de hasta 6 últimos meses
        promedio = sueldos.mean()

    return pd.Series({"PROMEDIO_SUELDO": promedio, "DETALLE_MESES": detalle})


def calcular_brecha(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la columna BRM = VALOR_PR - PROMEDIO_SUELDO
    Solo se calcula si VALOR_PR y PROMEDIO_SUELDO no son NaN.

    Args:
        df (pd.DataFrame): DataFrame con columnas VALOR_PR y PROMEDIO_SUELDO.

    Returns:
        pd.DataFrame: DataFrame con la columna BRM agregada.
    """
    df = df.copy()

    # Condición: ambos no NaN
    condicion = df["VALOR_PR"].notna() & df["PROMEDIO_SUELDO"].notna()

    df["BRECHA"] = np.where(condicion, df["VALOR_PR"] - df["PROMEDIO_SUELDO"], np.nan)

    return df
