# -*- coding: utf-8 -*-
"""
Módulo de monitoramento: salva proposições acompanhadas e detecta atualizações.
Usa arquivo local quando disponível, e st.session_state como fallback na nuvem.
"""

import json
import os
from src import camara, senado, congresso

ARQUIVO = "data/monitorados.json"
ARQUIVO_CONFIG = "data/agendador.json"
ARQUIVO_HIST = "data/historico.json"

# Chave usada no session_state para persistência na nuvem
_SS_KEY = "_monitorados_cache"


def _em_nuvem() -> bool:
    """Detecta se está rodando no Streamlit Cloud (filesystem read-only)."""
    return not os.access(".", os.W_OK) or os.path.abspath(".") == "/mount/src/monitor-legislativo"


def carregar_monitorados() -> dict:
    """Carrega proposições monitoradas — arquivo local ou session_state na nuvem."""
    # Tenta arquivo local primeiro
    try:
        if os.path.exists(ARQUIVO):
            with open(ARQUIVO, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass

    # Fallback: session_state (nuvem)
    try:
        import streamlit as st
        return st.session_state.get(_SS_KEY, {})
    except Exception:
        return {}


def salvar_monitorados(monitorados: dict):
    """Salva proposições — arquivo local ou session_state na nuvem."""
    # Tenta salvar em arquivo
    try:
        os.makedirs("data", exist_ok=True)
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(monitorados, f, ensure_ascii=False, indent=2)
        return
    except Exception:
        pass

    # Fallback: session_state (nuvem)
    try:
        import streamlit as st
        st.session_state[_SS_KEY] = monitorados
    except Exception:
        pass


def checar_atualizacoes(monitorados: dict) -> list:
    """Verifica mudanças de situação nas proposições monitoradas."""
    atualizacoes = []

    for chave, dados_antigos in monitorados.items():
        partes = chave.split(":")
        if len(partes) < 3:
            continue
        casa, numero, ano = partes[0], partes[1], partes[2]

        try:
            if casa == "Câmara":
                dados_novos = camara.buscar_proposicao(numero, ano)
            elif casa == "Senado":
                dados_novos = senado.buscar_proposicao(numero, ano)
            elif casa == "Congresso Nacional":
                dados_novos = congresso.buscar_proposicao(numero, ano)
            else:
                continue

            if not dados_novos:
                continue

            situacao_antiga = dados_antigos.get("situacao", "")
            situacao_nova = dados_novos.get("situacao", "")

            if situacao_nova and situacao_nova != situacao_antiga:
                atualizacoes.append({
                    "chave": chave,
                    "mensagem": f"Situação alterada: '{situacao_antiga}' → '{situacao_nova}'",
                    "dados": dados_novos,
                })
                monitorados[chave] = dados_novos

        except Exception as e:
            print(f"[Monitor] Erro ao checar {chave}: {e}")
            continue

    if atualizacoes:
        salvar_monitorados(monitorados)

    return atualizacoes
