import pandas as pd


def cargar_archivo(archivo):
    """
    Carga un archivo Excel o CSV en un DataFrame limpio.
    """
    ext = archivo.name.split(".")[-1].lower()
    try:
        if ext in ["xls", "xlsx"]:
            df = pd.read_excel(archivo)
        elif ext == "csv":
            df = pd.read_csv(archivo)
        else:
            raise ValueError(f"Formato de archivo no soportado: {ext}")

        from .limpieza import limpiar_dataframe

        return limpiar_dataframe(df)

    except Exception as e:
        raise RuntimeError(f"Error al leer archivo: {str(e)}")
