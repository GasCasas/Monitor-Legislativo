# -*- coding: utf-8 -*-
"""
Módulo de agendamento automático de verificações.
Roda em background e verifica atualizações a cada X horas configuradas.
Só envia notificações se houver mudança detectada.
"""

import threading
import time
import json
import os
from datetime import datetime

CONFIG_FILE = "data/agendador.json"


def carregar_config() -> dict:
    """Carrega a configuração do agendador."""
    if not os.path.exists(CONFIG_FILE):
        return {
            "ativo": False,
            "intervalo_horas": 1,
            "email_destinatario": "",
            "email_remetente": "",
            "email_senha_app": "",
            "whatsapp_numero": "",
            "whatsapp_api_key": "",
            "notif_email": False,
            "notif_whatsapp": False,
            "ultima_verificacao": None,
        }
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_config(config: dict):
    """Salva a configuração do agendador."""
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _loop_agendador():
    """Loop que roda em background e verifica atualizações a cada X horas."""
    from src.monitor import carregar_monitorados, checar_atualizacoes
    from src.notificador import enviar_email
    from src.whatsapp import enviar_whatsapp

    while True:
        try:
            config = carregar_config()

            if not config.get("ativo"):
                time.sleep(60)
                continue

            intervalo_horas = config.get("intervalo_horas", 1)
            ultima_str = config.get("ultima_verificacao")
            agora = datetime.now()

            deve_verificar = True
            if ultima_str:
                ultima_dt = datetime.strptime(ultima_str, "%Y-%m-%d %H:%M")
                horas_passadas = (agora - ultima_dt).total_seconds() / 3600
                deve_verificar = horas_passadas >= intervalo_horas

            if deve_verificar:
                print(f"[Agendador] Verificando às {agora.strftime('%H:%M')}...")

                monitorados = carregar_monitorados()
                atualizacoes = checar_atualizacoes(monitorados)

                if atualizacoes:
                    from src.historico import registrar_mudancas
                    registrar_mudancas(atualizacoes)
                    print(f"[Agendador] {len(atualizacoes)} mudança(s) detectada(s).")

                    if config.get("notif_email") and config.get("email_destinatario"):
                        enviar_email(
                            destinatario=config["email_destinatario"],
                            remetente=config["email_remetente"],
                            senha_app=config["email_senha_app"],
                            atualizacoes=atualizacoes,
                        )
                        print("[Agendador] E-mail enviado.")

                    if config.get("notif_whatsapp") and config.get("whatsapp_numero"):
                        enviar_whatsapp(
                            numero=config["whatsapp_numero"],
                            api_key=config["whatsapp_api_key"],
                            atualizacoes=atualizacoes,
                        )
                        print("[Agendador] WhatsApp enviado.")
                else:
                    print("[Agendador] Nenhuma mudança. Nenhuma notificação enviada.")

                config["ultima_verificacao"] = agora.strftime("%Y-%m-%d %H:%M")
                salvar_config(config)

        except Exception as e:
            print(f"[Agendador] Erro: {e}")

        time.sleep(60)


_thread_agendador = None


def iniciar_agendador():
    """Inicia o agendador em background."""
    global _thread_agendador
    if _thread_agendador is None or not _thread_agendador.is_alive():
        _thread_agendador = threading.Thread(target=_loop_agendador, daemon=True)
        _thread_agendador.start()
        print("[Agendador] Iniciado em background.")
