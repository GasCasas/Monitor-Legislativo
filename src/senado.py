# -*- coding: utf-8 -*-
"""
Módulo de integração com a API de Dados Abertos do Senado Federal.
"""

import requests

BASE_URL = "https://legis.senado.leg.br/dadosabertos"

TIPOS_PROPOSICAO = [
    "PL", "PLC", "PLS", "PEC", "PLP", "PDL", "PDS", "PRS",
    "REQ", "RQS", "RQE", "MSF", "MSC", "MPV",
    "INC", "EMC", "SCD", "SCS", "DVS", "CAP",
]

ALIASES = {
    "PL":  ["PL", "PLC", "PLS"],
    "PEC": ["PEC"],
    "PLP": ["PLP"],
    "PDL": ["PDL"],
    "REQ": ["REQ", "RQS", "RQE"],
    "MPV": ["MPV"],
}


def _get_json(url, params=None):
    for _url in [url + ".json" if not url.endswith(".json") else url, url]:
        try:
            resp = requests.get(_url, params=params,
                                headers={"Accept": "application/json"}, timeout=15)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            continue
    return None


def buscar_proposicao(numero: str, ano: str, tipo: str = None) -> dict:
    tipos_busca = ALIASES.get(tipo, [tipo]) if tipo and tipo != "Todos" else TIPOS_PROPOSICAO

    for t in tipos_busca:
        try:
            data = _get_json(f"{BASE_URL}/materia/pesquisa/lista",
                             params={"sigla": t, "numero": numero, "ano": ano})
            if not data:
                continue

            materias = (
                data.get("PesquisaBasicaMateria", {})
                    .get("Materias", {})
                    .get("Materia")
            )
            if not materias:
                continue
            if isinstance(materias, dict):
                materias = [materias]

            mat = materias[0]
            codigo = mat.get("Codigo")
            if not codigo:
                continue

            # Busca detalhes completos
            detalhe = _buscar_detalhe(str(codigo))

            ementa = mat.get("Ementa") or detalhe.get("IdentificacaoMateria", {}).get("EmentaMateria", "N/D")
            autor  = mat.get("Autor") or _extrair_autor(detalhe)

            # Situação: busca último estado e último local
            ultimo_local, ultimo_estado = _extrair_situacao_atual(detalhe)
            situacao = ultimo_estado or mat.get("DescricaoIdentificacao", "N/D")

            return {
                "id": str(codigo),
                "tipo": mat.get("Sigla", t),
                "numero": str(int(mat.get("Numero", numero))),
                "ano": mat.get("Ano", ano),
                "ementa": ementa,
                "autor": autor,
                "situacao": situacao,
                "ultimo_local": ultimo_local,
                "casa": "Senado",
            }

        except Exception as e:
            print(f"[Senado] Erro ao buscar {t} {numero}/{ano}: {e}")
            continue

    return None


def _buscar_detalhe(codigo: str) -> dict:
    try:
        data = _get_json(f"{BASE_URL}/materia/{codigo}", params={"v": "7"})
        if data:
            return data.get("DetalheMateria", {}).get("Materia", {})
    except Exception as e:
        print(f"[Senado] Erro detalhe {codigo}: {e}")
    return {}


def _extrair_autor(detalhe: dict) -> str:
    autoria = detalhe.get("AutoriaMateria", {})
    autor_obj = autoria.get("Autor") or autoria.get("Autores", {}).get("Autor")
    if isinstance(autor_obj, list):
        autor_obj = autor_obj[0]
    if isinstance(autor_obj, dict):
        return autor_obj.get("NomeAutor", "N/D")
    return "N/D"


def _extrair_situacao_atual(detalhe: dict) -> tuple:
    """Retorna (ultimo_local, ultimo_estado) da matéria."""
    sit = detalhe.get("SituacaoAtual", {})
    if not isinstance(sit, dict):
        return ("", "")

    # Estrutura: SituacaoAtual > Autuacoes > Autuacao (pode ser lista)
    autuacoes = sit.get("Autuacoes", {})
    if autuacoes:
        aut = autuacoes.get("Autuacao", {})
        if isinstance(aut, list):
            aut = aut[-1]  # pega o mais recente
        if isinstance(aut, dict):
            local = aut.get("Local", {})
            nome_local = local.get("NomeLocal", "") if isinstance(local, dict) else str(local)
            data_local = aut.get("DataLocal", "")
            descricao  = aut.get("DescricaoSituacao", "")
            data_sit   = aut.get("DataSituacao", "")

            ultimo_local  = f"{data_local[:10]} - {nome_local}" if data_local else nome_local
            ultimo_estado = f"{data_sit[:10]} - {descricao}" if data_sit else descricao
            return (ultimo_local, ultimo_estado)

    return ("", sit.get("DescricaoSituacao", ""))


# Cache de situações carregado da API oficial do Senado
_cache_situacoes: dict = {}


def _carregar_situacoes() -> dict:
    """Carrega a lista oficial de situações da API do Senado e monta o dicionário."""
    global _cache_situacoes
    if _cache_situacoes:
        return _cache_situacoes

    # Situações base (fallback se a API falhar)
    base = {
        "AGDESP": "Aguardando Despacho",
        "AGDDO": "Agendada para Ordem do Dia",
        "AGDDO(RQ)": "Agendada para Ordem do Dia (Requerimento)",
        "APROV": "Aprovada",
        "APROVPLEN": "Aprovada em Plenário",
        "APROVCOM": "Aprovada em Comissão",
        "REPROV": "Rejeitada",
        "REPROVCOM": "Rejeitada em Comissão",
        "ARQUIV": "Arquivada",
        "RETIRAD": "Retirada",
        "TRANSF": "Transformada em Norma",
        "DEVOL": "Devolvida",
        "DEVOLVIDA": "Devolvida à Câmara",
        "LEITURA": "Em Leitura",
        "ENCAM": "Encaminhada",
        "PUBSF": "Publicada no Senado",
        "PUBDOU": "Publicada no DOU",
        "DISTRIB": "Distribuída",
        "RELATOR": "Com Relator",
        "AGDREL": "Aguardando Relator",
        "PARECER": "Com Parecer",
        "VOTACAO": "Em Votação",
        "VOTNOMINAL": "Votação Nominal",
        "EMPAT": "Empatada",
        "RECON": "Reconvocada",
        "SUBST": "Substituída",
        "PAUTAD": "Pautada",
        "RETIPAUTA": "Retirada de Pauta",
        "ADIADO": "Adiado",
        "PREJUDIC": "Prejudicada",
        "TRAMIT": "Em Tramitação",
        "MATDESP": "Matéria Despachada",
        "INCLOD": "Incluída em Ordem do Dia",
        "RETIOD": "Retirada da Ordem do Dia",
        "SANCIONADA": "Sancionada",
        "VETADA": "Vetada",
        "PROMULGADA": "Promulgada",
        "VIGENTE": "Lei em Vigor",
        "AGUARDPUB": "Aguardando Publicação",
        "LIDO": "Lido em Plenário",
        "DESPACHADA": "Despachada",
        "COMISSOES": "Em Comissões",
        "RECEBIDA": "Recebida neste Órgão",
        "TRANSFPDL": "Transformada em Proj. de Dec. Legislativo",
    }

    try:
        # Tenta buscar lista oficial da API
        resp = requests.get(
            "https://legis.senado.leg.br/dadosabertos/processo/tipos-situacao.json",
            headers={"Accept": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            dados = resp.json()
            tipos = dados.get("TiposSituacao", {}).get("TipoSituacao", [])
            if isinstance(tipos, dict):
                tipos = [tipos]
            for t in tipos:
                sigla = t.get("SiglaSituacao", "").strip()
                descricao = t.get("DescricaoSituacao", "").strip().title()
                if sigla:
                    base[sigla.upper()] = descricao
    except Exception:
        pass  # Usa apenas o dicionário base

    _cache_situacoes = base
    return _cache_situacoes


def _traduzir_situacao(sigla: str) -> str:
    """Traduz sigla de situação para descrição completa."""
    if not sigla:
        return ""
    situacoes = _carregar_situacoes()
    return situacoes.get(sigla.upper().strip(), sigla)


def buscar_tramitacao(codigo: str) -> list:
    """Retorna tramitação completa do Senado.
    
    Estrutura correta da API:
    MovimentacaoMateria > Materia > Autuacoes > Autuacao > InformesLegislativos > InformeLegislativo
    """
    resultado = []
    try:
        data = _get_json(f"{BASE_URL}/materia/movimentacoes/{codigo}")
        if not data:
            return []

        materia = data.get("MovimentacaoMateria", {}).get("Materia", {})
        autuacoes = materia.get("Autuacoes", {}).get("Autuacao", [])
        
        if isinstance(autuacoes, dict):
            autuacoes = [autuacoes]

        for autuacao in autuacoes:
            informes = autuacao.get("InformesLegislativos", {}).get("InformeLegislativo", [])
            if isinstance(informes, dict):
                informes = [informes]

            for inf in informes:
                local = inf.get("Local", {})
                nome_local = local.get("NomeLocal", "") if isinstance(local, dict) else ""
                sigla_local = local.get("SiglaLocal", "") if isinstance(local, dict) else ""

                sit = inf.get("SituacaoIniciada", {})
                situacao = sit.get("SiglaSituacao", "") if isinstance(sit, dict) else ""

                data_str = inf.get("Data", "")[:10]
                descricao = inf.get("Descricao", "")

                resultado.append({
                    "Data": data_str,
                    "Órgão": f"{sigla_local} — {nome_local}" if sigla_local else nome_local,
                    "Situação": _traduzir_situacao(situacao),
                    "Descrição": descricao,
                })

        # Ordena por data decrescente (mais recente primeiro)
        resultado.sort(key=lambda x: x.get('Data', ''), reverse=True)
        return resultado

    except Exception as e:
        print(f"[Senado] Erro tramitação {codigo}: {e}")
        return []


def buscar_documentos(codigo: str) -> list:
    """Retorna os documentos (textos) da matéria."""
    try:
        data = _get_json(f"{BASE_URL}/materia/textos/{codigo}")
        if not data:
            return []
        textos = (
            data.get("TextoMateria", {})
                .get("Materia", {})
                .get("Textos", {})
                .get("Texto", [])
        )
        if isinstance(textos, dict):
            textos = [textos]
        resultado = []
        for t in textos:
            resultado.append({
                "Descrição": t.get("DescricaoTexto", ""),
                "Data": t.get("DataTexto", "")[:10],
                "Autor": t.get("AutoriaTexto", ""),
                "Link": t.get("UrlTexto", ""),
            })
        return resultado
    except Exception as e:
        print(f"[Senado] Erro documentos {codigo}: {e}")
        return []


def buscar_info_complementar(codigo: str) -> dict:
    """Retorna informações complementares da matéria."""
    detalhe = _buscar_detalhe(codigo)
    if not detalhe:
        return {}

    ident = detalhe.get("IdentificacaoMateria", {})
    assuntos = detalhe.get("AssuntosMateria", {}).get("Assunto", [])
    if isinstance(assuntos, dict):
        assuntos = [assuntos]

    return {
        "Assunto": ", ".join(
            a.get("AssuntoEspecifico", "") for a in assuntos
            if isinstance(a, dict) and a.get("AssuntoEspecifico")
        ),
        "Norma gerada": ident.get("NormaGerada", "Não"),
        "Bicameral": ident.get("IndicadorTramitando", ""),
        "Regime": ident.get("DescricaoIdentificacao", ""),
        "URL Senado": f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{codigo}",
    }


def buscar_por_tema(tema: str, itens: int = 20) -> list:
    """Busca proposições por palavra-chave na ementa."""
    try:
        data = _get_json(f"{BASE_URL}/materia/pesquisa/lista",
                         params={"ementa": tema, "tramitando": "S"})
        if not data:
            return []

        materias = (
            data.get("PesquisaBasicaMateria", {})
                .get("Materias", {})
                .get("Materia", [])
        )
        if isinstance(materias, dict):
            materias = [materias]

        resultado = []
        for mat in materias[:itens]:
            resultado.append({
                "Tipo": mat.get("Sigla", ""),
                "Número": str(int(mat.get("Numero", "0"))),
                "Ano": mat.get("Ano", ""),
                "Ementa": mat.get("Ementa", "N/D")[:120] + "...",
                "Autor": mat.get("Autor", "N/D"),
            })
        return resultado
    except Exception as e:
        print(f"[Senado] Erro busca por tema: {e}")
        return []
