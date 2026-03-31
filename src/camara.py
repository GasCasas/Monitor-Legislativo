# -*- coding: utf-8 -*-
"""
Módulo de integração com a API de Dados Abertos da Câmara dos Deputados.
Documentação: https://dadosabertos.camara.leg.br/swagger/openapi.html
"""

import requests

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}

# Todos os tipos de proposição disponíveis na Câmara
TIPOS_PROPOSICAO = [
    "PL", "PEC", "PLP", "PLV", "PDC", "PRC", "PRN", "RCP",
    "REQ", "RIC", "RFR", "MSC", "MPV", "INC", "EMC", "EMR",
    "SBT", "DVS", "DCR", "PDL", "PRS",
]


def buscar_proposicao(numero: str, ano: str, tipo: str = None) -> dict | None:
    """
    Busca uma proposição pelo número, ano e opcionalmente tipo.
    Se tipo não for informado, tenta todos os tipos até encontrar.
    """
    tipos_busca = [tipo] if tipo and tipo != "Todos" else TIPOS_PROPOSICAO

    for t in tipos_busca:
        params = {
            "numero": numero,
            "ano": ano,
            "siglaTipo": t,
            "itens": 5,
        }
        try:
            resp = requests.get(
                f"{BASE_URL}/proposicoes",
                params=params,
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            dados = resp.json().get("dados", [])
            if not dados:
                continue

            prop = dados[0]

            # Busca detalhes completos da proposição
            detalhe = _buscar_detalhe(prop.get("id"))

            return {
                "id": prop.get("id"),
                "tipo": t,
                "numero": prop.get("numero"),
                "ano": prop.get("ano"),
                "ementa": detalhe.get("ementa") or prop.get("ementa", "N/D"),
                "autor": _buscar_autor(prop.get("id")),
                "situacao": (
                    detalhe.get("statusProposicao", {}).get("descricaoSituacao")
                    or prop.get("statusProposicao", {}).get("descricaoSituacao", "N/D")
                ),
                "casa": "Câmara",
            }
        except requests.RequestException:
            continue

    return None


def _buscar_detalhe(prop_id: int) -> dict:
    """Busca os detalhes completos de uma proposição pelo ID."""
    try:
        resp = requests.get(
            f"{BASE_URL}/proposicoes/{prop_id}",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("dados", {})
    except requests.RequestException:
        return {}


def _buscar_autor(prop_id: int) -> str:
    """Busca o nome do primeiro autor de uma proposição."""
    try:
        resp = requests.get(
            f"{BASE_URL}/proposicoes/{prop_id}/autores",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        autores = resp.json().get("dados", [])
        if autores:
            return autores[0].get("nome", "N/D")
    except requests.RequestException:
        pass
    return "N/D"


def buscar_tramitacao(prop_id: int) -> list[dict]:
    """Retorna o histórico de tramitação de uma proposição."""
    try:
        resp = requests.get(
            f"{BASE_URL}/proposicoes/{prop_id}/tramitacoes",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        tramitacoes = resp.json().get("dados", [])

        resultado = []
        for t in tramitacoes:
            resultado.append({
                "Data": t.get("dataHora", "")[:10],
                "Sequência": t.get("sequencia"),
                "Órgão": t.get("siglaOrgao", ""),
                "Situação": t.get("descricaoSituacao", ""),
                "Despacho": t.get("descricaoTramitacao", ""),
            })

        return list(reversed(resultado))

    except requests.RequestException as e:
        print(f"Erro ao buscar tramitação na Câmara: {e}")
        return []
