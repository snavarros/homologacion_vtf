import pandas as pd


class CalculoHomologacion:
    def __init__(
        self,
        df: pd.DataFrame,
        df_param: pd.DataFrame,
        anio_referencia: int,
        mes_referencia: int,
    ):
        self.df_original = df.copy()
        self.df_original.columns = [col.upper() for col in self.df_original.columns]

        self.df_param = df_param.copy()
        self.df_param.columns = [col.upper() for col in self.df_param.columns]

        self.anio_referencia = anio_referencia
        self.mes_referencia = mes_referencia
        self.fecha_referencia = pd.to_datetime(
            f"{anio_referencia}-{mes_referencia:02d}-01"
        )

        # Filtro base: sólo registros del mes y año de referencia
        self.df_base = self.df_original[
            (self.df_original["ANIO"] == self.anio_referencia)
            & (self.df_original["MES"] == self.mes_referencia)
        ].copy()
        print(self.df_base)

        # Iniciar columnas auxiliares
        self.df_base["TIENE_ERRORES"] = False
        self.df_base["LOG_ERRORES"] = ""

    def _log(self, idx, mensaje):
        self.df_base.at[idx, "TIENE_ERRORES"] = True
        self.df_base.at[idx, "LOG_ERRORES"] += mensaje

    def agregar_columna_region(self):
        for idx, row in self.df_base.iterrows():
            try:
                codigo = str(row["CODIGO_ESTABLECIMIENTO"]).strip()

                if not codigo.isdigit():
                    raise ValueError(f"Código no numérico: {codigo}")

                if len(codigo) == 7:
                    region = int(codigo[0])  # Primer dígito
                elif len(codigo) == 8:
                    region = int(codigo[:2])  # Primeros dos dígitos
                else:
                    raise ValueError(f"Longitud inválida: {codigo}")

                self.df_base.at[idx, "REGION"] = region

            except Exception as e:
                self._log(idx, f"Error calculando región; {e}")

    def agregar_fecha(self):
        self.df_base["FECHA"] = self.fecha_referencia

    def agregar_antiguedad_dias(self):
        for idx, row in self.df_base.iterrows():
            if self.df_base.at[idx, "TIENE_ERRORES"]:
                continue
            try:
                fecha_contrato = pd.to_datetime(
                    row["FECHA_ESTABLECIDA_CONTRATO"], errors="coerce"
                )
                if pd.isna(fecha_contrato):
                    self._log(idx, "FECHA_ESTABLECIDA_CONTRATO inválida;")
                    continue
                dias = (self.fecha_referencia - fecha_contrato).days
                self.df_base.at[idx, "ANTIGUEDAD_DIAS"] = dias
            except Exception:
                self._log(idx, "Error calculando antigüedad;")

    def execute(self):
        """Ejecuta todos los cálculos y devuelve el DataFrame final."""
        self.agregar_columna_region()
        self.agregar_fecha()
        self.agregar_antiguedad_dias()

        return self.df_base.copy()
