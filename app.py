"""
Punto de entrada para Streamlit Cloud.
Sube el PDF de cartera desde el navegador y chatea con el agente.
"""

import tempfile
import streamlit as st

from orquestador import cargar_datos, crear_agente

st.set_page_config(page_title="Agente de Cartera", page_icon="📊")
st.title("📊 Agente de Cartera")

# --- Estado de sesión: agente, datos cargados, historial de chat ---------
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "agente" not in st.session_state:
    st.session_state.agente = None
if "datos_cargados" not in st.session_state:
    st.session_state.datos_cargados = False

# --- Carga del PDF ---------------------------------------------------------
pdf_subido = st.file_uploader("Sube el reporte de cartera (PDF)", type="pdf")

if pdf_subido is not None and not st.session_state.datos_cargados:
    with st.spinner("Extrayendo datos del PDF..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_subido.read())
            ruta_temporal = tmp.name

        cargar_datos(ruta_temporal)
        st.session_state.agente = crear_agente()
        st.session_state.datos_cargados = True
    st.success("Datos cargados. Ya puedes preguntar sobre la cartera.")

# --- Historial de chat -------------------------------------------------------
for msg in st.session_state.mensajes:
    with st.chat_message(msg["rol"]):
        st.write(msg["contenido"])

# --- Entrada de chat ---------------------------------------------------------
if st.session_state.datos_cargados:
    pregunta = st.chat_input("Pregunta algo sobre la cartera...")
    if pregunta:
        st.session_state.mensajes.append({"rol": "user", "contenido": pregunta})
        with st.chat_message("user"):
            st.write(pregunta)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                respuesta = st.session_state.agente.invoke({"entrada": pregunta})
                st.write(respuesta["output"])

        st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta["output"]})
else:
    st.info("Sube un PDF de cartera para empezar.")