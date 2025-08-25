import re
from collections import defaultdict


def formatear_errores(errores: list) -> list:
    """
    Agrupa errores por columna y devuelve mensajes HTML listos para mostrar.
    """
    agrupados = defaultdict(list)
    for err in errores:
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
