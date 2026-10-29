"""
Herramienta de extracción: convierte el reporte de cartera en PDF
(formato ERP, tipo "reporte_cartera_erp_v2.pdf") en datos estructurados.

Genera dos tablas:
  - clientes: un renglón por cliente con sus totales por rango de mora.
  - detalles: un renglón por documento/factura, ligado al NIT del cliente.
"""

import re
import os
import json
import pdfplumber
import sys
import pandas as pd

from my_helper import limpiar_numero

# --- Patrones de las dos clases de renglón del reporte -----------------

NUM = r"(-?[\d,]+)"

# TR  DOCUMENTO  FECHA  VENCE  EDAD  DOC_REF  AL_DIA 0A30 30A60 60A90 90A120 >180 SALDO
DETALLE_RE = re.compile(
    r"^(\d{2})\s+(\d+)\s+(\d{2}-\d{2}-\d{2})\s+(\d{2}-\d{2}-\d{2})\s+(\d+)\s+"
    r"(SALDO A FAV|\d+)\s+" + r"\s+".join([NUM] * 7) + r"\s*$"
)

# NIT  NOMBRE...  AL_DIA 0A30 30A60 60A90 90A120 >180 SALDO  (fila de totales del cliente)
CLIENTE_RE = re.compile(
    r"^(\d{6,12})\s+(.+?)\s+" + r"\s+".join([NUM] * 7) + r"\s*$"
)

COLUMNAS_RANGO = ["al_dia", "d0_30", "d30_60", "d60_90", "d90_120", "mas_180", "saldo"]

HEADER_RE = re.compile(
    r"TR\s+DOCUMEN\s+FECHA\s+VENCE\s+EDAD\s+DOC\s+REF\s+AL\s+DIA\s+"
    r"0\s+A\s+30\s+30\s+A\s+60\s+60\s+A\s+90\s+90\s+A\s+120\s+>\s*180\s+SALDO"
)
PERIODO_RE = re.compile(r"PERIODO\s+\d+\s+DE\s+\d{4}\s+FECHA DE CORTE\s+\d{4}-\d{2}-\d{2}")


def _extraer_texto(pdf_path: str) -> str:
    partes = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            partes.append(page.extract_text() or "")
    texto = "\n".join(partes)

    # 1) Quita encabezados aunque estén pegados a la línea anterior
    texto = HEADER_RE.sub("\n", texto)
    texto = PERIODO_RE.sub("\n", texto)

    # 2) Separa NIT+NOMBRE solo al inicio de línea
    texto = re.sub(r"(?m)^(\d{6,12})(?=[A-ZÁÉÍÓÚÑ])", r"\1 ", texto)
    return texto


def extraer_cartera(pdf_path: str):
    """
    Parsea el PDF y devuelve (df_clientes, df_detalles) como DataFrames
    de pandas, con las columnas de saldo ya convertidas a números.
    """
    texto = _extraer_texto(pdf_path)

    clientes = []
    detalles = []
    no_reconocidas = []   
    nit_actual = None
    nombre_actual = None

    for linea in texto.split("\n"):
        linea = linea.strip()
        if not linea or linea.startswith("PERIODO") or linea.startswith("TR ") or linea.startswith("Página"):
            continue

        m = DETALLE_RE.match(linea)
        if m:
            detalles.append({
                "nit": nit_actual,
                "cliente": nombre_actual,
                "tr": m.group(1),
                "documento": m.group(2),
                "fecha": m.group(3),
                "vence": m.group(4),
                "edad": int(m.group(5)),
                "doc_ref": m.group(6),
                "al_dia": limpiar_numero(m.group(7)),
                "d0_30": limpiar_numero(m.group(8)),
                "d30_60": limpiar_numero(m.group(9)),
                "d60_90": limpiar_numero(m.group(10)),
                "d90_120": limpiar_numero(m.group(11)),
                "mas_180": limpiar_numero(m.group(12)),
                "saldo": limpiar_numero(m.group(13)),
            })
            continue

        m = CLIENTE_RE.match(linea)
        if m:
            nit_actual = m.group(1)
            nombre_actual = m.group(2).strip()
            clientes.append({
                "nit": nit_actual,
                "cliente": nombre_actual,
                "al_dia": limpiar_numero(m.group(3)),
                "d0_30": limpiar_numero(m.group(4)),
                "d30_60": limpiar_numero(m.group(5)),
                "d60_90": limpiar_numero(m.group(6)),
                "d90_120": limpiar_numero(m.group(7)),
                "mas_180": limpiar_numero(m.group(8)),
                "saldo": limpiar_numero(m.group(9)),
            })
            continue

        no_reconocidas.append(linea)
        
    if no_reconocidas:
        print(f"⚠ {len(no_reconocidas)} líneas no reconocidas:")
        for l in no_reconocidas[:10]:
            print("   ", l)

    df_clientes = pd.DataFrame(clientes)
    df_detalles = pd.DataFrame(detalles)
    return df_clientes, df_detalles

def validar_extraccion(df_clientes, df_detalles):
    """Devuelve los clientes cuyos totales no coinciden con la suma de sus documentos."""
    suma = df_detalles.groupby("nit")[COLUMNAS_RANGO].sum()
    base = df_clientes.set_index("nit")[COLUMNAS_RANGO]
    diff = (base - suma.reindex(base.index).fillna(0)).abs()
    return diff[(diff > 0.01).any(axis=1)]


# Definir la carpeta de salida y ejecutar el script principal al correrlo
carpeta_salida = "salida"

if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "datos/reporte_cartera_erp_v2.pdf"  
    
    # 1. Extraer los DataFrames
    df_clientes, df_detalles = extraer_cartera(ruta)
    
    # 2. Asegurarse de que la carpeta de salida exista y guardar los CSVs
    os.makedirs(carpeta_salida, exist_ok=True)
    df_clientes.to_csv(f"{carpeta_salida}/clientes.csv", index=False, encoding="utf-8-sig")
    df_detalles.to_csv(f"{carpeta_salida}/detalles.csv", index=False, encoding="utf-8-sig")
    
    # 3. Mostrar resultados en la terminal
    print(f"Clientes: {len(df_clientes)} | Documentos: {len(df_detalles)}")
    print(f"Archivos guardados en {carpeta_salida}/")