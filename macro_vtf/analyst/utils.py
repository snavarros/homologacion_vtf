import pandas as pd


VALID_COLUMNS = {
    "planilla_validadora": [
        "CODIGO_ESTABLECIMIENTO",
        "NOMBRE_ESTABLECIMIENTO",
        "ANIO",
        "MES",
        "RUT",
    ],
    "macro": ["region", "codigo", "tipo", "cantidad"],
}


def validar_columnas_y_convertir(archivo, tipo):
    try:
        ext = archivo.name.split(".")[-1].lower()
        if ext in ["xls", "xlsx"]:
            df = pd.read_excel(archivo)
        elif ext == "csv":
            df = pd.read_csv(archivo)
        else:
            return False, [
                "Formato de archivo no soportado. Debe ser .xls, .xlsx o .csv"
            ]

        columnas_requeridas = VALID_COLUMNS[tipo]
        faltantes = [col for col in columnas_requeridas if col not in df.columns]
        if faltantes:
            return False, [f"Faltan columnas requeridas: {', '.join(faltantes)}"]

        # Si está todo bien
        return True, df

    except Exception as e:
        # Retornar el error para que se muestre
        return False, [f"Error procesando archivo: {str(e)}"]
