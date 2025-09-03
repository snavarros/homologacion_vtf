import re
import pandas as pd


def calcular_dv(rut_num: str) -> str:
    reversed_digits = list(map(int, reversed(str(rut_num))))
    factors = [2, 3, 4, 5, 6, 7]
    total = sum(d * factors[i % 6] for i, d in enumerate(reversed_digits))
    remainder = 11 - (total % 11)
    return "0" if remainder == 11 else "K" if remainder == 10 else str(remainder)


def normalizar_y_validar_rut(rut_str: str):
    if not isinstance(rut_str, str):
        return None
    rut_clean = re.sub(r"[^0-9kK]", "", rut_str)
    if len(rut_clean) < 2:
        return None
    rut_num = rut_clean[:-1]
    dv_ingresado = rut_clean[-1].upper()
    if not rut_num.isdigit():
        return None
    dv_esperado = calcular_dv(rut_num)
    return f"{int(rut_num)}-{dv_esperado}" if dv_esperado == dv_ingresado else None


def validar_rut(df: pd.DataFrame, col="RUT"):
    errores = []
    if col not in df.columns:
        errores.append("Falta la columna 'RUT' para validación de RUTs.")
        return errores

    for i, val in df[col].items():
        fila = i + 2
        if pd.isna(val) or str(val).strip() == "":
            errores.append(f"Fila {fila}, columna 'RUT': vacío no permitido.")
            continue

        rut_validado = normalizar_y_validar_rut(str(val))
        if not rut_validado:
            errores.append(f"Fila {fila}, columna 'RUT': '{val}' no es un RUT válido.")
        else:
            df.at[i, col] = rut_validado  # Normaliza el RUT
    return errores
