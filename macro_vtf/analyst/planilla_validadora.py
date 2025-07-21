import pandas as pd
import re
from collections import defaultdict
from .validaciones_config import (
    VALID_COLUMNS,
    VALID_TYPES,
    VALID_RANGES,
    VALID_VALUES,
    COLUMNS_ALLOW_EMPTY,
)


class PlanillaValidadora:
    def __init__(self, tipo: str):
        self.tipo = tipo
        self.columnas = VALID_COLUMNS.get(tipo, [])
        self.tipos = VALID_TYPES.get(tipo, {})
        self.rangos = VALID_RANGES.get(tipo, {})
        self.valores = VALID_VALUES.get(tipo, {})
        self.columnas_vacias = COLUMNS_ALLOW_EMPTY.get(tipo, {})
        self.errores = []

    def cargar_archivo(self, archivo):
        ext = archivo.name.split(".")[-1].lower()
        try:
            if ext in ["xls", "xlsx"]:
                df = pd.read_excel(archivo)
            elif ext == "csv":
                df = pd.read_csv(archivo)
            else:
                return f"Formato de archivo no soportado: {ext}"

            df = self._limpiar_dataframe(df)
            return df
        except Exception as e:
            return f"Error al leer archivo: {str(e)}"

    def _limpiar_dataframe(self, df):
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(r"^\s*$", pd.NA, regex=True)
        df.dropna(how="all", inplace=True)
        return df

    def validar(self, df: pd.DataFrame):
        self._validar_columnas(df)
        self._validar_tipos(df)
        self._validar_rangos(df)
        self._validar_valores_permitidos(df)
        return len(self.errores) == 0, self._formatear_errores()

    def _validar_columnas(self, df):
        faltantes = [col for col in self.columnas if col not in df.columns]
        if faltantes:
            self.errores.append(f"Faltan columnas: {', '.join(faltantes)}")

        extras = [col for col in df.columns if col not in self.columnas]
        if extras:
            self.errores.append(f"Columnas no reconocidas: {', '.join(extras)}")

    def _validar_tipos(self, df):
        for col, tipo in self.tipos.items():
            if col not in df.columns:
                continue
            allow_empty = self._permite_vacio(col)
            for i, valor in enumerate(df[col]):
                fila = i + 2
                if pd.isna(valor) or str(valor).strip() == "":
                    if not allow_empty:
                        self.errores.append(
                            f"Fila {fila}, columna '{col}': vacío no permitido."
                        )
                    continue

                if tipo == "numerico":
                    if not self._es_numero(valor):
                        self.errores.append(
                            f"Fila {fila}, columna '{col}': '{valor}' no es numérico."
                        )
                elif tipo == "fecha":
                    if not self._es_fecha(valor):
                        self.errores.append(
                            f"Fila {fila}, columna '{col}': '{valor}' no es fecha válida."
                        )
                elif tipo == "texto":
                    if not isinstance(valor, str):
                        self.errores.append(
                            f"Fila {fila}, columna '{col}': no es texto."
                        )

    def _validar_rangos(self, df):
        for col, (min_val, max_val) in self.rangos.items():
            if col not in df.columns:
                continue
            fila_base = 2

            if "FECHA" in col.upper():
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
                for i, valor in df[col].items():
                    if pd.isna(valor):
                        continue
                    if not (
                        pd.to_datetime(min_val) <= valor <= pd.to_datetime(max_val)
                    ):
                        self.errores.append(
                            f"Fila {i + fila_base}, columna '{col}': fecha fuera de rango."
                        )
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                for i, valor in df[col].items():
                    if pd.isna(valor):
                        continue
                    if not (min_val <= valor <= max_val):
                        self.errores.append(
                            f"Fila {i + fila_base}, columna '{col}': valor {valor} fuera de rango."
                        )

    def _validar_valores_permitidos(self, df):
        for col, reglas in self.valores.items():
            if col not in df.columns:
                continue
            valores_permitidos = {v.strip().lower() for v in reglas.get("allowed", [])}
            allow_empty = self._permite_vacio(col)
            df[col] = df[col].astype(str).str.strip().str.lower()

            for i, val in df[col].items():
                fila = i + 2
                if not val and not allow_empty:
                    self.errores.append(
                        f"Fila {fila}, columna '{col}': vacío no permitido."
                    )
                elif val not in valores_permitidos and val:
                    self.errores.append(
                        f"Fila {fila}, columna '{col}': '{val}' no permitido."
                    )

    def _permite_vacio(self, col):
        return self.columnas_vacias.get(col, False)

    def _es_numero(self, valor):
        try:
            float(valor)
            return True
        except:
            return False

    def _es_fecha(self, valor):
        try:
            pd.to_datetime(valor, dayfirst=True)
            return True
        except:
            return False

    def _formatear_errores(self):
        agrupados = defaultdict(list)
        for err in self.errores:
            match = re.search(r"columna '([^']+)'", err)
            if match:
                agrupados[match.group(1)].append(err)
            else:
                agrupados["Otros"].append(err)

        salida = []
        for col, msgs in agrupados.items():
            salida.append(
                f'<p class="font-semibold text-orange-600">ⓘ Errores en columna <code>{col}</code>:</p>'
            )
            for msg in msgs:
                salida.append(f'<p class="pl-4 text-sm text-gray-700">• {msg}</p>')
        return salida
