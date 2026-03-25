"""
Script de verificação autônoma para o GitHub Actions.
Lê proposições monitoradas do Supabase, verifica atualizações
e envia notificações se houver mudanças.
"""

import os
import sys

# Garante que o diretório raiz do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.monitor import carregar_monitorados, checar_atualizacoes
from src.database import registrar_mudancas, carregar_config, usando_supabase


def main():
    print("=" * 50)
    print("Monitor Legislativo — Verificação automática")
    print("=" * 50)

    if not usando_supabase():
        print("❌ Supabase não configurado. Defina SUPABASE_URL e SUPABASE_KEY.")
        print("   Este script requer Supabase para funcionar no GitHub Actions.")
        sys.exit(1)

    print("✅ Supabase conectado.")

    monitorados = carregar_monitorados()
    if not monitorados:
        print("ℹ️  Nenhuma proposição monitorada. Nada a verificar.")
        return

    print(f"🔍 Verificando {len(monitorados)} proposição(ões)...")

    atualizacoes = checar_atualizacoes(monitorados)

    if not atualizacoes:
        print("✅ Nenhuma mudança detectada.")
        return

    print(f"🔔 {len(atualizacoes)} mudança(s) detectada(s)!")
    for upd in atualizacoes:
        print(f"   → {upd['chave']}: {upd['mensagem']}")

    registrar_mudancas(atualizacoes)
    print("📝 Histórico atualizado no Supabase.")

    # Lê configurações de notificação das variáveis de ambiente
    notif_email    = os.getenv("NOTIF_EMAIL", "false").lower() == "true"
    notif_whatsapp = os.getenv("NOTIF_WHATSAPP", "false").lower() == "true"

    # Notificação por e-mail
    if notif_email:
        remetente    = os.getenv("EMAIL_REMETENTE", "")
        destinatario = os.getenv("EMAIL_DESTINATARIO", "")
        senha_app    = os.getenv("EMAIL_SENHA_APP", "")
        if remetente and destinatario and senha_app:
            try:
                from src.notificador import enviar_email
                enviar_email(destinatario, remetente, senha_app, atualizacoes)
                print("📧 E-mail enviado com sucesso.")
            except Exception as e:
                print(f"❌ Erro ao enviar e-mail: {e}")
        else:
            print("⚠️  Credenciais de e-mail incompletas (EMAIL_REMETENTE, EMAIL_DESTINATARIO, EMAIL_SENHA_APP).")

    # Notificação por WhatsApp
    if notif_whatsapp:
        numero  = os.getenv("WHATSAPP_NUMERO", "")
        api_key = os.getenv("WHATSAPP_API_KEY", "")
        if numero and api_key:
            try:
                from src.whatsapp import enviar_whatsapp
                enviar_whatsapp(numero, api_key, atualizacoes)
                print("💬 WhatsApp enviado com sucesso.")
            except Exception as e:
                print(f"❌ Erro ao enviar WhatsApp: {e}")
        else:
            print("⚠️  Credenciais de WhatsApp incompletas (WHATSAPP_NUMERO, WHATSAPP_API_KEY).")

    print("=" * 50)
    print("Verificação concluída.")


if __name__ == "__main__":
    main()
