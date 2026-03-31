# -*- coding: utf-8 -*-
"""
Módulo de monitoramento: salva proposições acompanhadas e detecta atualizações.
"""

import json
import os
from src import camara, senado

ARQUIVO = "data/monitorados.json"


def carregar_monitorados() -> dict:
    """Carrega a lista de proposições monitoradas do arquivo local."""
    if not os.path.exists(ARQUIVO):
        return {}
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_monitorados(monitorados: dict):
    """Salva a lista de proposições monitoradas no arquivo local."""
    os.makedirs("data", exist_ok=True)
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(monitorados, f, ensure_ascii=False, indent=2)


def checar_atualizacoes(monitorados: dict) -> list[dict]:
    """
    Verifica se alguma proposição monitorada teve mudança de situação.
    Retorna lista de atualizações detectadas.
    """
    atualizacoes = []

    for chave, dados_antigos in monitorados.items():
        casa, numero, ano = chave.split(":")

        if casa == "Câmara":
            dados_novos = camara.buscar_proposicao(numero, ano)
        else:
            dados_novos = senado.buscar_proposicao(numero, ano)

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
            # Atualiza o registro local
            monitorados[chave] = dados_novos

    if atualizacoes:
        salvar_monitorados(monitorados)

    return atualizacoes
