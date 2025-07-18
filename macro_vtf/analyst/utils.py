from collections import defaultdict
import re
import pandas as pd


VALID_COLUMNS = {
    "planilla_validadora": [
        "CODIGO_ESTABLECIMIENTO",
        "NOMBRE_ESTABLECIMIENTO",
        "ANIO",
        "MES",
        "RUT",
        "NOMBRE",
        "APELLIDO_PATERNO",
        "APELLIDO_MATERNO",
        "FECHA_NACIMIENTO",
        "CARGO",
        "FUNCION",
        "GRUPO",
        "NIVEL_ATENCION",
        "FECHA_INGRESO_SISTEMA_ESCOLAR",
        "ANIOS_SERVICIO_CON_EMPLEADOR",
        "FECHA_ESTABLECIDA_CONTRATO",
        "JORNADA_HORAS",
        "PLAZO_CONTRATO",
        "TIPO_CONTRATO",
        "NIVEL_EDUCACIONAL",
        "TITULO",
        "INSTITUCION_ACADEMICA",
        "DIAS_LICENCIA_MEDICA",
        "DIAS_SIN_GOCE_SUELDO",
        "TOTAL_DIAS_TRABAJADOS",
        "TOTAL_DIAS_PAGADOS",
        "REMUNERACIONES_INCLUYE_BONOS_Y_ASIGNACIONES_PACTADAS",
        "MOVILIZACION_MAS_COLACION",
        "MES_Y_ANIO_INICIO_PAGO",
        "ASIGNACION_MENSUAL_SOLICITADA_DE_CD",
        "SUELDO_BASE",
        "HORAS_EXTRAS",
        "ANTIGUEDAD_BIENIOS",
        "INCENTIVO",
        "ASIGNACION_RESPONSABILIDAD",
        "RELIQUIDACIONES",
        "INCREMENTOS_JUNJI",
        "AGUINALDO",
        "ASIGNACION_ZONA_EXTREMA",
        "BONO",
        "OTROS_AJUSTES",
        "ESPECIFIQUE",
        "BONO_VACACIONES_FISCAL",
        "BONO_TERMINO_CONFLICTO_FISCAL",
        "AGUINALDO_2",
        "BONO_ESCOLAR",
        "MOVILIZACION",
        "BONO_2",
        "COLACION",
        "ASIGNACIONES_FAMILIARES",
        "ASIGNACION_LEY_20905",
        "OTROS_AJUSTES_2",
        "ESPECIFIQUE_2",
        "ASIGNACION_CARRERA_DOCENTE_PAGADA",
        "SUELDO_BRUTO_O_TOTAL_HABERES",
        "OBSERVACIONES",
    ],
    "macro": ["region", "codigo", "tipo", "cantidad"],
}

VALID_TYPES = {
    "planilla_validadora": {
        "CODIGO_ESTABLECIMIENTO": "numerico",
        "ANIO": "numerico",
        "MES": "numerico",
        "RUT": "texto",
        "NOMBRE": "texto",
        "APELLIDO_PATERNO": "texto",
        "APELLIDO_MATERNO": "texto",
        "FECHA_NACIMIENTO": "fecha",
    },
}

VALID_RANGES = {
    "planilla_validadora": {
        "CODIGO_ESTABLECIMIENTO": (1_000_000, 16_999_999),
        "ANIO": (2013, 2030),
        "MES": (1, 12),
        "FECHA_NACIMIENTO": ("1940-01-01", "2010-12-31"),
    }
}

VALID_VALUES = {
    "NIVEL_ATENCION": {
        "allowed": ["sala cuna", "medio menor", "medio mayor", "transicion"],
        "allow_empty": False,
    },
    "APELLIDO_MATERNO": {
        "allowed": None,  # Puede tener cualquier texto o estar vacío
        "allow_empty": True,
    },
    "NOMBRE": {
        "allowed": None,
        "allow_empty": False,
    },
}


def agrupar_errores_por_columna(lista_errores):
    agrupados = defaultdict(list)
    for err in lista_errores:
        match = re.search(r"columna '([^']+)'", err)
        if match:
            col = match.group(1)
            agrupados[col].append(err)
        else:
            agrupados["Otros"].append(err)
    return agrupados


def cargar_archivo(archivo):
    ext = archivo.name.split(".")[-1].lower()
    try:
        if ext in ["xls", "xlsx"]:
            df = pd.read_excel(archivo)
        elif ext == "csv":
            df = pd.read_csv(archivo)
        else:
            return "Formato de archivo no soportado. Debe ser .xls, .xlsx o .csv"

        # Limpiar espacios en celdas tipo texto
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()

        # Eliminar filas completamente vacías
        df.dropna(how="all", inplace=True)

        return df

    except Exception as e:
        return f"Error al leer el archivo: {str(e)}"


def validar_columnas_requeridas(df, columnas_requeridas, errores):
    faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if faltantes:
        errores.append(f"Faltan columnas requeridas: {', '.join(faltantes)}")
        return False
    return True


def validar_columnas_extra(df, columnas_requeridas, errores):
    extras = [col for col in df.columns if col not in columnas_requeridas]
    if extras:
        errores.append(f"Columnas no reconocidas: {', '.join(extras)}")
        return False
    return True


def validar_formato_columnas(df, tipo, errores):
    reglas = VALID_TYPES.get(tipo, {})
    for col, tipo_dato in reglas.items():
        if col not in df.columns:
            continue
        if tipo_dato == "numerico":
            if not pd.api.types.is_numeric_dtype(df[col]):
                errores.append(f"La columna '{col}' debe ser numérica.")
        elif tipo_dato == "fecha":
            try:
                pd.to_datetime(df[col])
            except Exception:
                errores.append(f"La columna '{col}' debe tener formato de fecha.")
        elif tipo_dato == "texto":
            if not pd.api.types.is_string_dtype(df[col]):
                errores.append(f"La columna '{col}' debe ser texto.")
    return not errores


def validar_rango_valores(df, tipo, errores):
    reglas = VALID_RANGES.get(tipo, {})

    for col, (min_val, max_val) in reglas.items():
        if col not in df.columns:
            continue

        if "FECHA" in col.upper():
            try:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
                min_date = pd.to_datetime(min_val)
                max_date = pd.to_datetime(max_val)

                fechas_invalidas = df[df[col].isna()]
                if not fechas_invalidas.empty:
                    for i, row in fechas_invalidas.iterrows():
                        errores.append(
                            f"Fila {i + 2}, columna '{col}': fecha inválida o mal formateada."
                        )

                fuera_rango = df[~df[col].between(min_date, max_date, inclusive="both")]
                if not fuera_rango.empty:
                    for i, row in fuera_rango.iterrows():
                        fecha = (
                            row[col].strftime("%d-%m-%Y")
                            if pd.notnull(row[col])
                            else "fecha vacía"
                        )
                        errores.append(
                            f"Fila {i + 2}, columna '{col}': '{fecha}' está fuera del rango permitido "
                            f"({min_date.strftime('%d-%m-%Y')} a {max_date.strftime('%d-%m-%Y')})."
                        )
            except Exception as e:
                errores.append(f"Error al convertir '{col}' a fecha: {e}")

        else:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            fuera_rango = df[~df[col].between(min_val, max_val)]
            if not fuera_rango.empty:
                for i, row in fuera_rango.iterrows():
                    errores.append(
                        f"Fila {i + 2}, columna '{col}': valor {row[col]} fuera del rango permitido "
                        f"({min_val} a {max_val})."
                    )

    return not errores


def validar_valores_permitidos(df, tipo, errores):
    reglas_tipo = VALID_VALUES.get(tipo, {})

    for col, reglas in reglas_tipo.items():
        if col not in df.columns:
            continue

        valores_validos = reglas.get("allowed", set())
        allow_empty = reglas.get("allow_empty", True)

        # Verificamos vacíos si no se permiten — ANTES de transformar
        if not allow_empty:
            vacios = df[col].isna() | df[col].isin(
                ["", "Nan", "NaN", "None", "NoneType"]
            )
            if vacios.any():
                errores.append(
                    f"La columna '{col}' contiene valores vacíos no permitidos."
                )

        # Normalizamos la columna (después de revisar vacíos)
        df[col] = df[col].astype(str).str.strip().str.title()

        # Validamos valores permitidos si corresponde
        if valores_validos:
            valores_validos_normalizados = {v.strip().title() for v in valores_validos}
            valores_encontrados = set(df[col].dropna().unique())
            valores_invalidos = valores_encontrados - valores_validos_normalizados

            if valores_invalidos:
                errores.append(
                    f"La columna '{col}' contiene valores no permitidos: {', '.join(sorted(valores_invalidos))}. "
                    f"Los valores válidos son: {', '.join(sorted(valores_validos_normalizados))}."
                )

    return not errores


def agrupar_y_formatear_errores(errores):
    agrupados = agrupar_errores_por_columna(errores)
    salida = []
    for col, msgs in agrupados.items():
        # Título con icono elegante
        salida.append(
            f'<p class="font-semibold text-orange-600 mb-1">ⓘ Errores en la columna <code>{col}</code>:</p>'
        )
        # Lista con bullets simples y espacio
        for msg in msgs:
            salida.append(f'<p class="pl-4 text-gray-700 text-sm">• {msg}</p>')
    return salida


def validar_columnas_y_convertir(archivo, tipo):
    errores = []

    df = cargar_archivo(archivo)
    if isinstance(df, str):
        return False, [df]  # Error de carga

    columnas_requeridas = VALID_COLUMNS.get(tipo, [])
    if not validar_columnas_requeridas(df, columnas_requeridas, errores):
        return False, agrupar_y_formatear_errores(errores)

    if not validar_columnas_extra(df, columnas_requeridas, errores):
        return False, agrupar_y_formatear_errores(errores)

    if not validar_formato_columnas(df, tipo, errores):
        return False, agrupar_y_formatear_errores(errores)

    if not validar_rango_valores(df, tipo, errores):
        return False, agrupar_y_formatear_errores(errores)

    if not validar_valores_permitidos(df, tipo, errores):
        return False, agrupar_y_formatear_errores(errores)

    return True, df
