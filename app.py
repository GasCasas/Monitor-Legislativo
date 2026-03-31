# -*- coding: utf-8 -*-
import streamlit as st
from src import camara, senado, ai_analysis, exporter
from src.monitor import carregar_monitorados, salvar_monitorados, checar_atualizacoes
from src.agendador import carregar_config, salvar_config, iniciar_agendador
from src.notificador import testar_email
from src.historico import carregar_historico, registrar_mudancas, limpar_historico
from src.whatsapp import TEMPLATE_PADRAO
from src import congresso
import pandas as pd

st.set_page_config(
    page_title="Monitor Legislativo",
    page_icon="🏛️",
    layout="wide",
)

# Agendador desativado na nuvem (use localmente)
try:
    iniciar_agendador()
except Exception:
    pass

st.markdown("""
<link rel="manifest" href="/app/static/manifest.json">
<meta name="theme-color" content="#1a3a5c">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Monitor PL">
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/app/static/sw.js');
  }
</script>
""", unsafe_allow_html=True)

st.title("🏛️ Monitor Legislativo")
st.caption("Acompanhe proposições da Câmara dos Deputados e do Senado Federal")

aba = st.tabs([
    "🔍 Buscar",
    "📋 Monitorados",
    "📊 Dashboard",
    "🤖 Análise IA",
    "📥 Exportar",
    "⚙️ Configurações",
])

# ── ABA 1: BUSCA ──────────────────────────────────────────────────────────────
with aba[0]:
    busca_tipo = st.radio("Tipo de busca", ["Por número", "Por tema/palavra-chave"],
                          horizontal=True)

    if busca_tipo == "Por número":
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        with col1:
            numero = st.text_input("Número", placeholder="Ex: 2531")
        with col2:
            ano = st.text_input("Ano", placeholder="Ex: 2021")
        with col3:
            tipo = st.selectbox("Tipo", [
                "Todos (busca automática)",
                "PL", "PEC", "PLP", "PDL", "PDC", "PRS", "PDS",
                "REQ", "RQS", "RIC", "MSC", "MSF", "MPV",
                "INC", "EMC", "SCD", "DVS",
                "── Congresso Nacional ──",
                "VET", "MSG", "PLV", "RCN", "DCN",
            ])
        with col4:
            casa = st.selectbox("Casa", ["Câmara", "Senado", "Congresso Nacional"])

        tipo_busca = None if tipo in ["Todos (busca automática)", "── Congresso Nacional ──"] else tipo

        if st.button("🔍 Buscar", use_container_width=True):
            if not numero or not ano:
                st.warning("Preencha o número e o ano.")
            else:
                msg = (f"Buscando {tipo} {numero}/{ano} na {casa}..."
                       if tipo_busca
                       else f"Buscando {numero}/{ano} na {casa} em todos os tipos...")
                with st.spinner(msg):
                    if casa == "Câmara":
                        dados = camara.buscar_proposicao(numero, ano, tipo_busca)
                    elif casa == "Senado":
                        dados = senado.buscar_proposicao(numero, ano, tipo_busca)
                    else:
                        dados = congresso.buscar_proposicao(numero, ano, tipo_busca)
                if not dados:
                    st.error(f"Proposição {numero}/{ano} não encontrada na {casa}. "
                             "Verifique o número, ano e tipo.")
                else:
                    st.session_state["prop_atual"] = dados
                    st.session_state["casa_atual"] = casa

    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            tema = st.text_input("Palavra-chave ou tema", placeholder="Ex: educação, meio ambiente, saúde...")
        with col2:
            casa_tema = st.selectbox("Casa", ["Câmara", "Senado", "Congresso Nacional"], key="casa_tema")

        if st.button("🔍 Buscar por tema", use_container_width=True):
            if not tema:
                st.warning("Digite uma palavra-chave.")
            else:
                with st.spinner(f"Buscando proposições sobre '{tema}'..."):
                    if casa_tema == "Câmara":
                        resultados = camara.buscar_por_tema(tema, itens=50)
                    elif casa_tema == "Senado":
                        resultados = senado.buscar_por_tema(tema, itens=50)
                    else:
                        resultados = congresso.buscar_por_tema(tema, itens=50)

                if not resultados:
                    st.info(f"Nenhuma proposição encontrada para '{tema}'.")
                else:
                    st.success(f"{len(resultados)} proposição(ões) encontrada(s):")
                    df_tema = pd.DataFrame(resultados)
                    st.dataframe(df_tema, use_container_width=True, hide_index=True)

    if "prop_atual" in st.session_state and busca_tipo == "Por número":
        dados = st.session_state["prop_atual"]
        casa_atual = st.session_state["casa_atual"]

        st.divider()
        col_a, col_b = st.columns([3, 1])
        with col_a:
            tipo_exib = dados.get("tipo", "PL")
            tipo_desc = dados.get("tipo_descricao", "")
            header = f"{tipo_exib} {dados.get('numero')}/{dados.get('ano')}"
            if tipo_desc and tipo_desc != tipo_exib:
                header += f" — {tipo_desc}"
            st.subheader(header)
            st.write(f"**Ementa:** {dados.get('ementa', 'N/D')}")
            st.write(f"**Autor:** {dados.get('autor', 'N/D')}")
            st.write(f"**Situação:** {dados.get('situacao', 'N/D')}")
        with col_b:
            monitorados = carregar_monitorados()
            chave = f"{casa_atual}:{dados.get('numero')}:{dados.get('ano')}"
            if chave not in monitorados:
                if st.button("➕ Monitorar", use_container_width=True):
                    monitorados[chave] = dados
                    salvar_monitorados(monitorados)
                    st.success("Adicionado ao monitoramento!")
                    st.rerun()
            else:
                st.success("✅ Monitorado")

        if casa_atual == "Senado" and dados.get("ultimo_local"):
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.write(f"**Último local:** {dados.get('ultimo_local', 'N/D')}")
            with col_s2:
                st.write(f"**Último estado:** {dados.get('situacao', 'N/D')}")

        det_tabs = st.tabs(["📜 Tramitação", "📄 Documentos", "ℹ️ Info Complementar"])

        with det_tabs[0]:
            with st.spinner("Carregando tramitação..."):
                if casa_atual == "Câmara":
                    tramitacao = camara.buscar_tramitacao(dados.get("id"))
                elif casa_atual == "Senado":
                    tramitacao = senado.buscar_tramitacao(dados.get("id"))
                else:
                    tramitacao = congresso.buscar_tramitacao(dados.get("id"))
            if tramitacao:
                df = pd.DataFrame(tramitacao)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma tramitação encontrada.")

        with det_tabs[1]:
            if casa_atual in ["Senado", "Congresso Nacional"]:
                mod_docs = senado if casa_atual == "Senado" else congresso
                with st.spinner("Carregando documentos..."):
                    docs = mod_docs.buscar_documentos(dados.get("id"))
                if docs:
                    for doc in docs:
                        link = doc.get("Link", "")
                        label = f"{doc.get('Descrição', 'Documento')} — {doc.get('Data', '')}"
                        if link:
                            st.markdown(f"📄 [{label}]({link})")
                        else:
                            st.write(f"📄 {label}")
                else:
                    st.info("Nenhum documento encontrado.")
            else:
                st.info("Documentos disponíveis apenas para matérias do Senado.")

        with det_tabs[2]:
            if casa_atual in ["Senado", "Congresso Nacional"]:
                with st.spinner("Carregando informações..."):
                    info = senado.buscar_info_complementar(dados.get("id"))
                # Prazo de vigência para MPV
                if casa_atual == "Congresso Nacional" and dados.get("prazo_vigencia"):
                    st.info(f"⏳ **Prazo de vigência:** {dados.get('prazo_vigencia')}")
                    info = info or {}
                if info:
                    for chave_i, valor in info.items():
                        if valor:
                            if chave_i == "URL Senado":
                                st.markdown(f"**{chave_i}:** [{valor}]({valor})")
                            else:
                                st.write(f"**{chave_i}:** {valor}")
            else:
                st.info("Informações complementares disponíveis apenas para o Senado.")

# ── ABA 2: MONITORADOS ────────────────────────────────────────────────────────
with aba[1]:
    monitorados = carregar_monitorados()

    if not monitorados:
        st.info("Nenhuma proposição monitorada ainda. Use a aba 'Buscar' para adicionar.")
    else:
        st.subheader(f"{len(monitorados)} proposição(ões) monitorada(s)")

        if st.button("🔄 Verificar atualizações agora"):
            with st.spinner("Verificando..."):
                atualizacoes = checar_atualizacoes(monitorados)
            if atualizacoes:
                registrar_mudancas(atualizacoes)
                for upd in atualizacoes:
                    st.warning(f"**{upd['chave']}** — {upd['mensagem']}")
            else:
                st.success("Nenhuma atualização encontrada.")

        st.divider()
        for chave, dados in monitorados.items():
            casa_m, num_m, ano_m = chave.split(":")
            with st.expander(f"{'🏛️'} {casa_m} · {dados.get('tipo','PL')} {num_m}/{ano_m}"):
                st.write(f"**Ementa:** {dados.get('ementa', 'N/D')}")
                st.write(f"**Situação:** {dados.get('situacao', 'N/D')}")
                if st.button("🗑️ Remover", key=f"rm_{chave}"):
                    del monitorados[chave]
                    salvar_monitorados(monitorados)
                    st.rerun()

# ── ABA 3: DASHBOARD ──────────────────────────────────────────────────────────
with aba[2]:
    st.subheader("📊 Dashboard")
    monitorados = carregar_monitorados()
    historico = carregar_historico()

    col1, col2, col3, col4 = st.columns(4)
    total = len(monitorados)
    camara_count = sum(1 for k in monitorados if k.startswith("Câmara"))
    senado_count = sum(1 for k in monitorados if k.startswith("Senado"))
    historico_count = len(historico)

    col1.metric("Total monitorado", total)
    col2.metric("Câmara", camara_count)
    col3.metric("Senado", senado_count)
    col4.metric("Mudanças detectadas", historico_count)

    if monitorados:
        st.divider()
        st.markdown("#### Distribuição por tipo de proposição")
        tipos = {}
        for dados in monitorados.values():
            t = dados.get("tipo", "PL")
            tipos[t] = tipos.get(t, 0) + 1
        df_tipos = pd.DataFrame(list(tipos.items()), columns=["Tipo", "Quantidade"])
        st.bar_chart(df_tipos.set_index("Tipo"))

    if historico:
        st.divider()
        st.markdown("#### Histórico de mudanças detectadas")
        df_hist = pd.DataFrame(historico)
        df_hist = df_hist.sort_values("data", ascending=False)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)

        if st.button("🗑️ Limpar histórico"):
            limpar_historico()
            st.success("Histórico limpo!")
            st.rerun()
    else:
        st.info("Nenhuma mudança detectada ainda. O histórico será preenchido automaticamente quando o agendador detectar atualizações.")

# ── ABA 4: ANÁLISE IA ─────────────────────────────────────────────────────────
with aba[3]:
    st.subheader("🤖 Análise com Inteligência Artificial")
    st.caption("Cole o texto de uma ementa ou tramitação para obter análise automática.")

    api_key = st.text_input("Chave de API da Anthropic (Claude)", type="password",
                            help="Obtenha em https://console.anthropic.com")
    texto = st.text_area("Texto para análise", height=200,
                         placeholder="Cole aqui a ementa, o texto do PL ou o histórico de tramitação...")

    tipo_analise = st.selectbox("Tipo de análise", [
        "Resumo executivo",
        "Impacto social e econômico",
        "Pontos polêmicos ou riscos jurídicos",
        "Linha do tempo resumida",
    ])

    if st.button("🤖 Analisar com IA", use_container_width=True):
        if not api_key:
            st.warning("Informe sua chave de API.")
        elif not texto:
            st.warning("Cole um texto para análise.")
        else:
            with st.spinner("Analisando..."):
                resultado = ai_analysis.analisar(texto, tipo_analise, api_key)
            st.markdown("### Resultado")
            st.markdown(resultado)

# ── ABA 5: EXPORTAR ───────────────────────────────────────────────────────────
with aba[4]:
    st.subheader("📥 Exportar Dados")
    monitorados = carregar_monitorados()

    if not monitorados:
        st.info("Nenhuma proposição monitorada para exportar.")
    else:
        formato = st.selectbox("Formato", ["Excel (.xlsx)", "PDF (.pdf)", "CSV (.csv)"])

        if st.button("📥 Gerar relatório", use_container_width=True):
            with st.spinner("Gerando..."):
                if formato == "Excel (.xlsx)":
                    caminho = exporter.exportar_excel(monitorados)
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                elif formato == "PDF (.pdf)":
                    caminho = exporter.exportar_pdf(monitorados)
                    mime = "application/pdf"
                else:
                    caminho = exporter.exportar_csv(monitorados)
                    mime = "text/csv"

            with open(caminho, "rb") as f:
                st.download_button(
                    label=f"⬇️ Baixar {formato}",
                    data=f,
                    file_name=caminho.split("/")[-1],
                    mime=mime,
                    use_container_width=True,
                )

# ── ABA 6: CONFIGURAÇÕES ──────────────────────────────────────────────────────
with aba[5]:
    from src.whatsapp import testar_whatsapp
    st.subheader("⚙️ Configurações de notificação")
    config = carregar_config()

    # E-MAIL
    st.markdown("### 📧 E-mail")
    notif_email = st.toggle("Ativar notificação por e-mail", value=config.get("notif_email", False))

    if notif_email:
        st.caption("Usamos o Gmail. Você precisa de uma **senha de app** — não a senha normal. "
                   "[Como gerar](https://support.google.com/accounts/answer/185833).")
        col1, col2 = st.columns(2)
        with col1:
            email_remetente = st.text_input("Seu Gmail (remetente)",
                                            value=config.get("email_remetente", ""),
                                            placeholder="seuemail@gmail.com")
        with col2:
            email_destinatario = st.text_input("E-mail de destino",
                                               value=config.get("email_destinatario", ""),
                                               placeholder="destino@email.com")
        senha_app = st.text_input("Senha de app do Gmail",
                                  value=config.get("email_senha_app", ""),
                                  type="password", placeholder="xxxx xxxx xxxx xxxx")
        if st.button("📨 Testar e-mail"):
            with st.spinner("Enviando..."):
                ok = testar_email(email_destinatario, email_remetente, senha_app)
            st.success("E-mail enviado!") if ok else st.error("Erro ao enviar.")
    else:
        email_remetente = config.get("email_remetente", "")
        email_destinatario = config.get("email_destinatario", "")
        senha_app = config.get("email_senha_app", "")

    st.divider()

    # WHATSAPP
    st.markdown("### 💬 WhatsApp (CallMeBot — gratuito)")
    notif_whatsapp = st.toggle("Ativar notificação por WhatsApp",
                               value=config.get("notif_whatsapp", False))

    if notif_whatsapp:
        st.info("**Como ativar (uma vez só):**\n"
                "1. Salve **+34 644 59 91 90** como *CallMeBot*\n"
                "2. Envie: `I allow callmebot to send me messages`\n"
                "3. Cole a API key recebida abaixo", icon="📱")
        col1, col2 = st.columns(2)
        with col1:
            whatsapp_numero = st.text_input("Seu número",
                                            value=config.get("whatsapp_numero", ""),
                                            placeholder="5561999999999")
        with col2:
            whatsapp_api_key = st.text_input("API Key do CallMeBot",
                                             value=config.get("whatsapp_api_key", ""),
                                             type="password")

        st.markdown("#### ✏️ Personalizar mensagem")
        st.caption("Use `{data}`, `{itens}` e `{total}` como variáveis na mensagem.")
        whatsapp_template = st.text_area(
            "Template da mensagem",
            value=config.get("whatsapp_template", TEMPLATE_PADRAO),
            height=180,
        )

        col_prev, col_test = st.columns(2)
        with col_prev:
            if st.button("👁️ Pré-visualizar"):
                from src.whatsapp import TEMPLATE_PADRAO as TPL
                from datetime import datetime
                exemplo = whatsapp_template.format(
                    data=datetime.now().strftime("%d/%m/%Y às %H:%M"),
                    itens="• *Câmara · PL 2531/2021*\n  Situação alterada: exemplo",
                    total=1,
                )
                st.code(exemplo)
        with col_test:
            if st.button("💬 Testar WhatsApp"):
                if not whatsapp_numero or not whatsapp_api_key:
                    st.warning("Preencha o número e a API key.")
                else:
                    with st.spinner("Enviando..."):
                        ok = testar_whatsapp(whatsapp_numero, whatsapp_api_key, whatsapp_template)
                    st.success("Mensagem enviada!") if ok else st.error("Erro ao enviar.")
    else:
        whatsapp_numero = config.get("whatsapp_numero", "")
        whatsapp_api_key = config.get("whatsapp_api_key", "")
        whatsapp_template = config.get("whatsapp_template", TEMPLATE_PADRAO)

    st.divider()

    # AGENDADOR
    st.markdown("### 🕐 Verificação automática")
    ativo = st.toggle("Ativar verificação automática", value=config.get("ativo", False))
    intervalo_horas = st.selectbox(
        "Verificar a cada",
        options=[1, 2, 3, 6, 12, 24],
        index=[1, 2, 3, 6, 12, 24].index(config.get("intervalo_horas", 1)),
        format_func=lambda x: f"{x} hora" if x == 1 else f"{x} horas",
    )

    ultima = config.get("ultima_verificacao")
    if ultima:
        st.caption(f"Última verificação: {ultima}")

    if st.button("💾 Salvar configurações", use_container_width=True):
        config.update({
            "ativo": ativo,
            "intervalo_horas": intervalo_horas,
            "notif_email": notif_email,
            "email_destinatario": email_destinatario,
            "email_remetente": email_remetente,
            "email_senha_app": senha_app,
            "notif_whatsapp": notif_whatsapp,
            "whatsapp_numero": whatsapp_numero,
            "whatsapp_api_key": whatsapp_api_key,
            "whatsapp_template": whatsapp_template,
        })
        salvar_config(config)
        st.success("Configurações salvas!")

    if ativo:
        canais = []
        if notif_email: canais.append("e-mail")
        if notif_whatsapp: canais.append("WhatsApp")
        freq = "1 hora" if intervalo_horas == 1 else f"{intervalo_horas} horas"
        canais_str = " e ".join(canais) if canais else "nenhum canal configurado"
        st.info(f"✅ Verificando a cada **{freq}** via **{canais_str}**. "
                "Notifica apenas quando houver mudança.")
