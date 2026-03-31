# -*- coding: utf-8 -*-
"""
Módulo de análise com IA usando a API da Anthropic (Claude).
"""

import anthropic

PROMPTS = {
    "Resumo executivo": (
        "Faça um resumo executivo claro e objetivo desta proposição legislativa, "
        "destacando: o que ela propõe, a quem impacta e qual o estágio atual. "
        "Use linguagem acessível, sem jargões jurídicos."
    ),
    "Impacto social e econômico": (
        "Analise os possíveis impactos sociais e econômicos desta proposição legislativa. "
        "Aponte grupos beneficiados, possíveis custos ao erário e consequências práticas "
        "se o projeto for aprovado."
    ),
    "Pontos polêmicos ou riscos jurídicos": (
        "Identifique os principais pontos polêmicos, controvérsias e possíveis riscos "
        "jurídicos ou constitucionais desta proposição legislativa. "
        "Seja objetivo e imparcial."
    ),
    "Linha do tempo resumida": (
        "Com base no texto fornecido, construa uma linha do tempo resumida da tramitação "
        "desta proposição, destacando os marcos mais importantes em ordem cronológica."
    ),
}


def analisar(texto: str, tipo: str, api_key: str) -> str:
    """
    Analisa um texto legislativo usando Claude.

    Args:
        texto: Texto da ementa, PL ou tramitação.
        tipo: Tipo de análise desejada.
        api_key: Chave da API Anthropic.

    Returns:
        Texto com a análise gerada.
    """
    instrucao = PROMPTS.get(tipo, PROMPTS["Resumo executivo"])

    client = anthropic.Anthropic(api_key=api_key)

    mensagem = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=(
            "Você é um especialista em direito legislativo e políticas públicas do Brasil. "
            "Analise as proposições legislativas com clareza, precisão e imparcialidade. "
            "Responda sempre em português brasileiro."
        ),
        messages=[
            {
                "role": "user",
                "content": f"{instrucao}\n\n---\n\nTexto para análise:\n{texto}",
            }
        ],
    )

    return mensagem.content[0].text
