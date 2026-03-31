# -*- coding: utf-8 -*-
"""
Módulo de histórico de mudanças detectadas.
Usa arquivo local ou session_state na nuvem.
"""

import json
import os
from datetime import datetime

ARQUIVO = "data/historico.json"
_SS_KEY = "_historico_cache"


def carregar_historico() -> list:
    try:
        if os.path.exists(ARQUIVO):
            with open(ARQUIVO, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    try:
        import streamlit as st
        return st.session_state.get(_SS_KEY, [])
    except Exception:
        return []


def salvar_historico(historico: list):
    try:
        os.makedirs("data", exist_ok=True)
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)
        return
    except Exception:
        pass
    try:
        import streamlit as st
        st.session_state[_SS_KEY] = historico
    except Exception:
        pass


def registrar_mudancas(atualizacoes: list):
    if not atualizacoes:
        return
    historico = carregar_historico()
    for upd in atualizacoes:
        partes = upd["chave"].split(":")
        casa = partes[0] if partes else ""
        numero = partes[1] if len(partes) > 1 else ""
        ano = partes[2] if len(partes) > 2 else ""
        historico.append({
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "casa": casa,
            "proposicao": f"{upd.get('tipo', '')} {numero}/{ano}".strip(),
            "mensagem": upd["mensagem"],
        })
    salvar_historico(historico[-500:])


def limpar_historico():
    salvar_historico([])
