# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(page_title="Teste", layout="wide")
st.title("Monitor Legislativo - Teste")

try:
    import sys, os
    sys.path.insert(0, '/mount/src/monitor-legislativo')
    st.write(f"Python: {sys.version}")
    st.write(f"Diretório: {os.getcwd()}")
    st.write(f"Arquivos: {os.listdir('.')}")
    st.success("OK básico!")
except Exception as e:
    st.error(f"Erro: {e}")

try:
    from src import camara
    st.success("camara OK")
except Exception as e:
    st.error(f"camara ERRO: {e}")

try:
    from src import senado
    st.success("senado OK")
except Exception as e:
    st.error(f"senado ERRO: {e}")

try:
    from src import congresso
    st.success("congresso OK")
except Exception as e:
    st.error(f"congresso ERRO: {e}")

try:
    from src.agendador import iniciar_agendador
    st.success("agendador OK")
except Exception as e:
    st.error(f"agendador ERRO: {e}")
