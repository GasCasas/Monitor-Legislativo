# -*- coding: utf-8 -*-
"""
Módulo de notificação via WhatsApp usando o CallMeBot.
"""

import urllib.request
import urllib.parse
from datetime import datetime

TEMPLATE_PADRAO = """🏛️ *Monitor Legislativo*
📅 {data}

Atualização detectada:
{itens}

Acesse o Monitor para mais detalhes."""


def enviar_whatsapp(numero: str, api_key: str, atualizacoes: list[dict],
                    template: str = None) -> bool:
    if not atualizacoes:
        return True

    itens = ""
    for upd in atualizacoes:
        casa, numero_pl, ano = upd["chave"].split(":")
        itens += f"• *{casa} · PL {numero_pl}/{ano}*\n  {upd['mensagem']}\n"

    tpl = template or TEMPLATE_PADRAO
    mensagem = tpl.format(
        data=datetime.now().strftime("%d/%m/%Y às %H:%M"),
        itens=itens.strip(),
        total=len(atualizacoes),
    )

    try:
        params = urllib.parse.urlencode({
            "phone": numero,
            "text": mensagem,
            "apikey": api_key,
        })
        url = f"https://api.callmebot.com/whatsapp.php?{params}"
        with urllib.request.urlopen(url, timeout=15) as resp:
            resposta = resp.read().decode()
            return "Message queued" in resposta or resp.status == 200
    except Exception as e:
        print(f"[WhatsApp] Erro: {e}")
        return False


def testar_whatsapp(numero: str, api_key: str, template: str = None) -> bool:
    return enviar_whatsapp(
        numero=numero,
        api_key=api_key,
        template=template,
        atualizacoes=[{
            "chave": "Câmara:2531:2021",
            "mensagem": "✅ Teste de configuração bem-sucedido!"
        }]
    )
