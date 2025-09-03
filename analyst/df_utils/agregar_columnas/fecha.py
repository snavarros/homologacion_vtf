import pandas as pd


def agregar_fecha(df, anio, mes):
    """
    Agrega la columna FECHA con base en el año y mes de referencia.
    """
    df = df.copy()
    fecha_referencia = pd.to_datetime(f"{anio}-{mes:02d}-01")
    df["FECHA"] = fecha_referencia
    return df


# mover a la carpeta correspondiente
def agregar_sueldo_promedio(self, meses=3):
    try:
        df = self.df_original.copy()
        df["FECHA"] = pd.to_datetime(
            df["ANIO"].astype(str) + "-" + df["MES"].astype(str) + "-01"
        )
        df.sort_values(["RUT", "FECHA"], ascending=[True, False], inplace=True)
        df["RANK"] = df.groupby("RUT")["FECHA"].rank(method="first", ascending=False)
        df_filtrado = df[df["RANK"] <= meses]
        promedio = df_filtrado.groupby("RUT")["SUELDO_BASE"].mean().reset_index()
        promedio.rename(
            columns={"SUELDO_BASE": f"SUELDO_BASE_PROM_{meses}_MESES"}, inplace=True
        )

        self.df_base = self.df_base.merge(promedio, on="RUT", how="left")
    except Exception as e:
        print(f"Error calculando sueldo promedio: {e}")
