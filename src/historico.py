# -*- coding: utf-8 -*-
"""
Módulo de histórico de mudanças detectadas.
Salva e recupera todas as atualizações encontradas pelo agendador.
"""

import json
import os
from datetime import datetime

ARQUIVO = "data/historico.json"


def carregar_historico() -> list:
    if not os.path.exists(ARQUIVO):
        return []
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_historico(historico: list):
    os.makedirs("data", exist_ok=True)
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def registrar_mudancas(atualizacoes: list[dict]):
    """Adiciona novas mudanças ao histórico."""
    if not atualizacoes:
        return
    historico = carregar_historico()
    for upd in atualizacoes:
        casa, numero, ano = upd["chave"].split(":")
        historico.append({
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "casa": casa,
            "proposicao": f"{upd.get('tipo', '')} {numero}/{ano}".strip(),
            "mensagem": upd["mensagem"],
        })
    # Mantém apenas os últimos 500 registros
    salvar_historico(historico[-500:])


def limpar_historico():
    salvar_historico([])
