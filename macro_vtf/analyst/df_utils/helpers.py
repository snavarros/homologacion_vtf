import pandas as pd


def permite_vacio(columnas_vacias: dict, col: str) -> bool:
    return bool(columnas_vacias.get(col, False))


def es_numero(valor) -> bool:
    try:
        float(valor)
        return True
    except Exception:
        return False


def es_fecha(valor) -> bool:
    try:
        pd.to_datetime(valor, dayfirst=True)
        return True
    except Exception:
        return False
