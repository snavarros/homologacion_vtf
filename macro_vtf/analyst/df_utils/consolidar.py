import pandas as pd


def consolidar_sueldos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Consolida los sueldos en un DataFrame.

    Args:
        df (pd.DataFrame): DataFrame con los datos de sueldos.

    Returns:
        pd.DataFrame: DataFrame consolidado.
    """

    df = df.copy()
    df_consolidado = df.pivot_table(
        index=["CODIGO_ESTABLECIMIENTO", "RUT"],
        columns=["ANIO", "MES"],
        values="SUELDO_BRUTO_O_TOTAL_HABERES",
        aggfunc="first",
    ).reset_index()

    df_consolidado.columns = [
        "_".join([str(c) for c in col if c != ""]) if isinstance(col, tuple) else col
        for col in df_consolidado.columns
    ]

    # 🚀 Eliminar duplicados por claves principales
    df_consolidado = df_consolidado.drop_duplicates(
        subset=["CODIGO_ESTABLECIMIENTO", "RUT"]
    )

    return df_consolidado
