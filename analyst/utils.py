import re


def calcular_dv(rut_num):
    reversed_digits = list(map(int, reversed(str(rut_num))))
    factors = [2, 3, 4, 5, 6, 7]
    total = sum(d * factors[i % 6] for i, d in enumerate(reversed_digits))
    remainder = 11 - (total % 11)
    if remainder == 11:
        return "0"
    elif remainder == 10:
        return "K"
    return str(remainder)


def normalizar_y_validar_rut(rut_str):
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

    if dv_esperado != dv_ingresado:
        return None

    return f"{int(rut_num)}-{dv_esperado}"


MESES_CHOICES = [
    (1, "Enero"),
    (2, "Febrero"),
    (3, "Marzo"),
    (4, "Abril"),
    (5, "Mayo"),
    (6, "Junio"),
    (7, "Julio"),
    (8, "Agosto"),
    (9, "Septiembre"),
    (10, "Octubre"),
    (11, "Noviembre"),
    (12, "Diciembre"),
]
