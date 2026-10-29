"""
Funciones de apoyo reutilizables en todo el proyecto.
"""

def limpiar_numero(valor: str) -> float:
    if valor is None:
        return 0.0
    valor = str(valor).replace(",", "").strip()
    if valor == "" or valor.upper() == "SALDO A FAV":
        return 0.0
    try:
        return float(valor)
    except ValueError:
        return 0.0
    