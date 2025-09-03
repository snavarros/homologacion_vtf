import pandas as pd


def validar_columnas_obligatorias(df: pd.DataFrame, columnas: list) -> list:
    """
    Retorna lista de columnas faltantes.
    """
    return [col for col in columnas if col not in df.columns]


def validar_tipos(df: pd.DataFrame, tipos: dict) -> dict:
    """
    Verifica que las columnas tengan los tipos esperados.
    tipos = {"EDAD": "int64", "NOMBRE": "object"}
    """
    errores = {}
    for col, tipo in tipos.items():
        if col in df.columns and df[col].dtype != tipo:
            errores[col] = str(df[col].dtype)
    return errores


def validar_archivo(nombre_archivo):
    if not nombre_archivo.endswith((".xls", ".xlsx", ".csv")):
        return False, [
            "Formato de archivo no permitido. Solo se permiten .xls, .xlsx o .csv."
        ]
    return True, []
