# -*- coding: utf-8 -*-
import streamlit as st

st.title("Teste")
st.write("App funcionando!")

try:
    from src import camara, senado, ai_analysis, exporter
    st.success("src imports OK")
except Exception as e:
    st.error(f"Erro src: {e}")

try:
    from src import congresso
    st.success("congresso OK")
except Exception as e:
    st.error(f"Erro congresso: {e}")

try:
    from src.agendador import carregar_config, salvar_config, iniciar_agendador
    st.success("agendador OK")
except Exception as e:
    st.error(f"Erro agendador: {e}")
