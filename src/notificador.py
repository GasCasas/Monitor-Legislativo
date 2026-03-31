# -*- coding: utf-8 -*-
"""
Módulo de notificação por e-mail.
Usa o servidor SMTP do Gmail para enviar alertas de atualização.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def enviar_email(destinatario: str, remetente: str, senha_app: str, atualizacoes: list[dict]):
    """
    Envia um e-mail com as atualizações detectadas nas proposições monitoradas.

    Args:
        destinatario: E-mail de quem vai receber.
        remetente: Seu e-mail Gmail.
        senha_app: Senha de app gerada no Google (não é a senha normal).
        atualizacoes: Lista de dicts com 'chave' e 'mensagem'.
    """
    if not atualizacoes:
        return

    assunto = f"[Monitor Legislativo] {len(atualizacoes)} atualização(ões) detectada(s)"

    # Monta o corpo do e-mail em HTML
    itens_html = ""
    for upd in atualizacoes:
        casa, numero, ano = upd["chave"].split(":")
        itens_html += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #eee;">
            <strong>{casa} · PL {numero}/{ano}</strong><br>
            <span style="color:#555;">{upd['mensagem']}</span>
          </td>
        </tr>
        """

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
      <div style="max-width:600px;margin:auto;border:1px solid #ddd;border-radius:8px;overflow:hidden;">
        <div style="background:#1a3a5c;padding:20px;">
          <h2 style="color:white;margin:0;">🏛️ Monitor Legislativo</h2>
          <p style="color:#aac4e0;margin:4px 0 0;">Atualização automática · {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
        </div>
        <div style="padding:20px;">
          <p>As seguintes proposições tiveram mudanças de situação:</p>
          <table width="100%" cellspacing="0" cellpadding="0">
            {itens_html}
          </table>
          <p style="margin-top:20px;font-size:13px;color:#888;">
            Acesse o Monitor Legislativo para mais detalhes.
          </p>
        </div>
      </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = destinatario
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(remetente, senha_app)
        servidor.sendmail(remetente, destinatario, msg.as_string())


def testar_email(destinatario: str, remetente: str, senha_app: str) -> bool:
    """Envia um e-mail de teste para verificar se as configurações estão corretas."""
    try:
        enviar_email(
            destinatario=destinatario,
            remetente=remetente,
            senha_app=senha_app,
            atualizacoes=[{
                "chave": "Câmara:2531:2021",
                "mensagem": "Este é um e-mail de teste. Configuração funcionando! ✅"
            }]
        )
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False
