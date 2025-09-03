import pandas as pd


def limpiar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia un DataFrame: quita espacios, normaliza vacíos, elimina filas vacías.
    """
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace(r"^\s*$", pd.NA, regex=True)
    df.dropna(how="all", inplace=True)
    return df


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza nombres de columnas: mayúsculas, sin espacios al inicio/fin.
    """
    df.columns = df.columns.str.strip().str.upper()
    return df


def reemplazar_nulos(df: pd.DataFrame, valor=0) -> pd.DataFrame:
    """
    Reemplaza valores nulos por el valor especificado.
    """
    return df.fillna(valor)
