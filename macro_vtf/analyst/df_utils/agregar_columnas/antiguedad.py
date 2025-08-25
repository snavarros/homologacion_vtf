import pandas as pd


def agregar_antiguedad_dias(
    df, fecha_referencia, col_fecha="FECHA_ESTABLECIDA_CONTRATO"
):
    """
    Calcula la antigüedad en días desde la fecha de contrato hasta la fecha de referencia.
    """
    df = df.copy()
    for idx, row in df.iterrows():
        if df.at[idx, "TIENE_ERRORES"]:
            continue
        try:
            fecha_contrato = pd.to_datetime(row[col_fecha], errors="coerce")
            if pd.isna(fecha_contrato):
                df.at[idx, "TIENE_ERRORES"] = True
                df.at[idx, "LOG_ERRORES"] += f"{col_fecha} inválida;"
                continue
            dias = (fecha_referencia - fecha_contrato).days
            df.at[idx, "ANTIGUEDAD_DIAS"] = dias
        except Exception:
            df.at[idx, "TIENE_ERRORES"] = True
            df.at[idx, "LOG_ERRORES"] += "Error calculando antigüedad;"
    return df
