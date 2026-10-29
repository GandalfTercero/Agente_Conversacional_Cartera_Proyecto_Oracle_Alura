"""
Lee la clave de Gemini. Funciona en dos entornos:
  - Local (VS Code): la toma del archivo .env
  - Streamlit Cloud: la toma de st.secrets (configurado en la web)
"""

import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))