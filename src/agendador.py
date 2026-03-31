# -*- coding: utf-8 -*-
"""
Módulo de agendamento automático de verificações.
Usa arquivo local ou session_state na nuvem.
"""

import threading
import time
import json
import os
from datetime import datetime

CONFIG_FILE = "data/agendador.json"
_SS_KEY = "_agendador_config"

_DEFAULTS = {
    "ativo": False,
    "intervalo_horas": 1,
    "email_destinatario": "",
    "email_remetente": "",
    "email_senha_app": "",
    "whatsapp_numero": "",
    "whatsapp_api_key": "",
    "whatsapp_template": "",
    "notif_email": False,
    "notif_whatsapp": False,
    "ultima_verificacao": None,
}


def carregar_config() -> dict:
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                # Garante que todos os campos existam
                return {**_DEFAULTS, **dados}
    except Exception:
        pass
    try:
        import streamlit as st
        return {**_DEFAULTS, **st.session_state.get(_SS_KEY, {})}
    except Exception:
        return dict(_DEFAULTS)


def salvar_config(config: dict):
    try:
        os.makedirs("data", exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return
    except Exception:
        pass
    try:
        import streamlit as st
        st.session_state[_SS_KEY] = config
    except Exception:
        pass


def _loop_agendador():
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
                try:
                    ultima_dt = datetime.strptime(ultima_str, "%Y-%m-%d %H:%M")
                    horas_passadas = (agora - ultima_dt).total_seconds() / 3600
                    deve_verificar = horas_passadas >= intervalo_horas
                except Exception:
                    pass

            if deve_verificar:
                monitorados = carregar_monitorados()
                atualizacoes = checar_atualizacoes(monitorados)

                if atualizacoes:
                    from src.historico import registrar_mudancas
                    registrar_mudancas(atualizacoes)

                    if config.get("notif_email") and config.get("email_destinatario"):
                        try:
                            enviar_email(
                                destinatario=config["email_destinatario"],
                                remetente=config["email_remetente"],
                                senha_app=config["email_senha_app"],
                                atualizacoes=atualizacoes,
                            )
                        except Exception as e:
                            print(f"[Agendador] Erro email: {e}")

                    if config.get("notif_whatsapp") and config.get("whatsapp_numero"):
                        try:
                            enviar_whatsapp(
                                numero=config["whatsapp_numero"],
                                api_key=config["whatsapp_api_key"],
                                atualizacoes=atualizacoes,
                                template=config.get("whatsapp_template"),
                            )
                        except Exception as e:
                            print(f"[Agendador] Erro whatsapp: {e}")

                config["ultima_verificacao"] = agora.strftime("%Y-%m-%d %H:%M")
                salvar_config(config)

        except Exception as e:
            print(f"[Agendador] Erro: {e}")

        time.sleep(60)


_thread_agendador = None


def iniciar_agendador():
    global _thread_agendador
    if _thread_agendador is None or not _thread_agendador.is_alive():
        _thread_agendador = threading.Thread(target=_loop_agendador, daemon=True)
        _thread_agendador.start()
