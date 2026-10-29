"""
Orquestador: define las "tools" (herramientas) que el agente puede
invocar y arma el agente de LangChain usando Gemini como modelo.

Las tools son wrappers delgados sobre las funciones de:
  - herramienta_consultas.py
  - herramienta_estadisticas.py
  - herramienta_alertas.py
que ya trabajan sobre los DataFrames extraídos del PDF.
"""

import json

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from my_models import GEMINI_FLASH
from my_keys import GEMINI_API_KEY
from herramienta_extraer_cartera import extraer_cartera
from herramienta_estadisticas import resumen_general
from herramienta_consultas import buscar_cliente, clientes_por_rango_mora, clientes_en_mora_mayor_a
from herramienta_alertas import resumen_alertas


# --- Estado global de los datos de cartera ya extraídos -----------------
# Se cargan una sola vez al iniciar el orquestador (ver cargar_datos).
_df_clientes = None
_df_detalles = None


def cargar_datos(ruta_pdf: str):
    global _df_clientes, _df_detalles
    _df_clientes, _df_detalles = extraer_cartera(ruta_pdf)


# --- Tools que el agente puede invocar ------------------------------------

@tool
def herramienta_resumen_cartera() -> str:
    """Devuelve el resumen general de la cartera: saldo total, totales por
    rango de mora (al día, 0-30, 30-60, 60-90, 90-120, más de 180 días)
    y el top 5 de clientes con mayor saldo."""
    return json.dumps(resumen_general(_df_clientes), ensure_ascii=False)


@tool
def herramienta_buscar_cliente(nombre_o_nit: str) -> str:
    """Busca un cliente por nombre (parcial) o por NIT y devuelve su
    saldo total y el detalle de sus documentos/facturas."""
    return json.dumps(buscar_cliente(_df_clientes, _df_detalles, nombre_o_nit), ensure_ascii=False)


@tool
def herramienta_clientes_en_mora(dias: int) -> str:
    """Devuelve los clientes cuyos documentos tienen una mora (edad)
    mayor a la cantidad de días indicada, con el saldo vencido agrupado
    por cliente."""
    return json.dumps(clientes_en_mora_mayor_a(_df_detalles, dias), ensure_ascii=False)


@tool
def herramienta_alertas_riesgo() -> str:
    """Genera un resumen de alertas de cartera, clasificando cada cliente
    en mora en un nivel de riesgo: CRÍTICO (>180 días), ALTO (90-120),
    MEDIO (60-90) o BAJO (30-60)."""
    return json.dumps(resumen_alertas(_df_clientes), ensure_ascii=False)


HERRAMIENTAS = [
    herramienta_resumen_cartera,
    herramienta_buscar_cliente,
    herramienta_clientes_en_mora,
    herramienta_alertas_riesgo,
]


def crear_agente() -> AgentExecutor:
    modelo = ChatGoogleGenerativeAI(
        model=GEMINI_FLASH,
        google_api_key=GEMINI_API_KEY,
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "Eres un asistente experto en análisis de cartera (cuentas por "
            "cobrar). Respondes en español, de forma clara y concreta, "
            "usando las herramientas disponibles para consultar los datos "
            "reales de la cartera antes de responder. Cuando menciones "
            "cifras de dinero, sepáralas con comas (ej: 123,000). Si el "
            "usuario pregunta algo que no se puede responder con las "
            "herramientas disponibles, dilo con honestidad."
        )),
        ("human", "{entrada}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agente = create_tool_calling_agent(modelo, HERRAMIENTAS, prompt)
    return AgentExecutor(agent=agente, tools=HERRAMIENTAS, verbose=False, max_iterations=5)