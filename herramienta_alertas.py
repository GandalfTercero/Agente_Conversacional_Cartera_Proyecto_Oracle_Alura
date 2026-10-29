"""
Herramienta de alertas: genera un resumen de clientes en mora,
clasificados por nivel de riesgo, útil para revisiones rápidas
de cartera.
"""

import pandas as pd

NIVELES_RIESGO = [
    ("CRÍTICO", "mas_180", 1),
    ("ALTO", "d90_120", 1),
    ("MEDIO", "d60_90", 1),
    ("BAJO", "d30_60", 1),
]


def clasificar_riesgo(fila: pd.Series) -> str:
    """Clasifica un cliente según el rango de mora más alto en el que tenga saldo."""
    for nivel, columna, minimo in NIVELES_RIESGO:
        if fila.get(columna, 0) >= minimo:
            return nivel
    return "SIN MORA"


def generar_alertas(df_clientes: pd.DataFrame) -> list:
    """
    Devuelve la lista de clientes con algún nivel de mora (excluye
    'SIN MORA'), ordenados del riesgo más crítico al más bajo.
    """
    df = df_clientes.copy()
    df["nivel_riesgo"] = df.apply(clasificar_riesgo, axis=1)

    orden_riesgo = {"CRÍTICO": 0, "ALTO": 1, "MEDIO": 2, "BAJO": 3, "SIN MORA": 4}
    df["_orden"] = df["nivel_riesgo"].map(orden_riesgo)

    en_mora = df[df["nivel_riesgo"] != "SIN MORA"].sort_values(["_orden", "saldo"], ascending=[True, False])

    return en_mora[["nit", "cliente", "nivel_riesgo", "saldo"]].to_dict(orient="records")


def resumen_alertas(df_clientes: pd.DataFrame) -> dict:
    alertas = generar_alertas(df_clientes)
    conteo_por_nivel = {}
    for a in alertas:
        conteo_por_nivel[a["nivel_riesgo"]] = conteo_por_nivel.get(a["nivel_riesgo"], 0) + 1

    return {
        "total_clientes_en_mora": len(alertas),
        "conteo_por_nivel": conteo_por_nivel,
        "detalle": alertas,
    }

"""
python -c "from herramienta_extraer_cartera import extraer_cartera; 
from herramienta_alertas import resumen_alertas; 
df_c, df_d = extraer_cartera('datos/reporte_cartera_erp_v2.pdf'); 
r = resumen_alertas(df_c); print('Total en mora:', r['total_clientes_en_mora']); 
print('Conteo por nivel:', r['conteo_por_nivel']); print('Primeros 3:', r['detalle'][:3])"
"""