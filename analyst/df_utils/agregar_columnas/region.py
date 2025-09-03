def agregar_columna_region(df):
    """
    Agrega la columna REGION a partir del código del establecimiento.
    """
    df = df.copy()
    df["COD_REGION"] = None

    for idx, row in df.iterrows():
        try:
            codigo = str(row["CODIGO_ESTABLECIMIENTO"]).strip()
            if not codigo.isdigit():
                raise ValueError(f"Código no numérico: {codigo}")

            if len(codigo) == 7:
                region = int(codigo[0])
            elif len(codigo) == 8:
                region = int(codigo[:2])
            else:
                raise ValueError(f"Longitud inválida: {codigo}")

            df.at[idx, "COD_REGION"] = region

        except Exception as e:
            df.at[idx, "TIENE_ERRORES"] = True
            df.at[idx, "LOG_ERRORES"] += f"Error calculando región; {e}"

    return df
