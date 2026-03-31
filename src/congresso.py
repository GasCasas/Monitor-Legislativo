# -*- coding: utf-8 -*-
"""
Módulo de integração com matérias do Congresso Nacional.
MPV, VET, MSG, PLV e outras matérias que tramitam no CN.
Usa a mesma API do Senado Federal (legis.senado.leg.br/dadosabertos).
"""

import requests

BASE_URL = "https://legis.senado.leg.br/dadosabertos"

# Tipos de proposição exclusivos ou principais do Congresso Nacional
TIPOS_CN = {
    "MPV": "Medida Provisória",
    "VET": "Veto Presidencial",
    "MSG": "Mensagem do Executivo",
    "PLV": "Projeto de Lei de Conversão",
    "PDC": "Projeto de Decreto Legislativo do CN",
    "PRC": "Projeto de Resolução do CN",
    "RCN": "Resolução do Congresso Nacional",
    "DCN": "Decreto Legislativo do CN",
    "INC": "Indicação",
}


def _get_json(url, params=None):
    """Faz GET e retorna JSON."""
    for _url in [url + ".json" if not url.endswith(".json") else url, url]:
        try:
            resp = requests.get(_url, params=params,
                                headers={"Accept": "application/json"}, timeout=15)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            continue
    return None


def buscar_proposicao(numero: str, ano: str, tipo: str = None) -> dict | None:
    """
    Busca uma proposição do Congresso Nacional pelo número, ano e tipo.
    Se tipo não informado, tenta todos os tipos CN.
    """
    tipos_busca = [tipo] if tipo and tipo != "Todos" else list(TIPOS_CN.keys())

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

            detalhe = _buscar_detalhe(str(codigo))
            ident = detalhe.get("IdentificacaoMateria", {})

            ementa = mat.get("Ementa") or ident.get("EmentaMateria", "N/D")
            autor = mat.get("Autor") or _extrair_autor(detalhe)
            situacao = _extrair_situacao(detalhe) or "N/D"

            # Identifica se é MPV para mostrar prazo de vigência
            extra = {}
            if t == "MPV":
                extra = _buscar_info_mpv(detalhe)

            return {
                "id": str(codigo),
                "tipo": t,
                "tipo_descricao": TIPOS_CN.get(t, t),
                "numero": str(int(mat.get("Numero", numero))),
                "ano": mat.get("Ano", ano),
                "ementa": ementa,
                "autor": autor,
                "situacao": situacao,
                "casa": "Congresso Nacional",
                **extra,
            }

        except Exception as e:
            print(f"[CN] Erro ao buscar {t} {numero}/{ano}: {e}")
            continue

    return None


def _buscar_detalhe(codigo: str) -> dict:
    try:
        data = _get_json(f"{BASE_URL}/materia/{codigo}", params={"v": "7"})
        if data:
            return data.get("DetalheMateria", {}).get("Materia", {})
    except Exception as e:
        print(f"[CN] Erro detalhe {codigo}: {e}")
    return {}


def _extrair_autor(detalhe: dict) -> str:
    autoria = detalhe.get("AutoriaMateria", {})
    autor_obj = autoria.get("Autor") or autoria.get("Autores", {}).get("Autor")
    if isinstance(autor_obj, list):
        autor_obj = autor_obj[0]
    if isinstance(autor_obj, dict):
        return autor_obj.get("NomeAutor", "N/D")
    return "Presidência da República"


def _extrair_situacao(detalhe: dict) -> str:
    sit = detalhe.get("SituacaoAtual", {})
    if not isinstance(sit, dict):
        return ""
    autuacoes = sit.get("Autuacoes", {})
    if autuacoes:
        aut = autuacoes.get("Autuacao", {})
        if isinstance(aut, list):
            aut = aut[-1]
        if isinstance(aut, dict):
            return aut.get("DescricaoSituacao", "")
    return sit.get("DescricaoSituacao", "")


def _buscar_info_mpv(detalhe: dict) -> dict:
    """Extrai informações específicas de Medidas Provisórias (prazo de vigência)."""
    ident = detalhe.get("IdentificacaoMateria", {})
    prazo = ident.get("DataLimiteVigencia", "")
    return {
        "prazo_vigencia": prazo[:10] if prazo else "",
    }


def buscar_tramitacao(codigo: str) -> list[dict]:
    """Retorna tramitação completa de uma matéria do CN."""
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
                resultado.append({
                    "Data": inf.get("Data", "")[:10],
                    "Órgão": f"{sigla_local} — {nome_local}" if sigla_local else nome_local,
                    "Situação": situacao,
                    "Descrição": inf.get("Descricao", ""),
                })

        resultado.sort(key=lambda x: x.get("Data", ""), reverse=True)
        return resultado

    except Exception as e:
        print(f"[CN] Erro tramitação {codigo}: {e}")
        return []


def buscar_documentos(codigo: str) -> list[dict]:
    """Retorna documentos da matéria."""
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
        return [{
            "Descrição": t.get("DescricaoTexto", ""),
            "Data": t.get("DataTexto", "")[:10],
            "Autor": t.get("AutoriaTexto", ""),
            "Link": t.get("UrlTexto", ""),
        } for t in textos]
    except Exception:
        return []


def buscar_por_tema(tema: str, itens: int = 20) -> list[dict]:
    """Busca proposições do CN por palavra-chave na ementa."""
    resultado = []
    for t in list(TIPOS_CN.keys()):
        try:
            data = _get_json(f"{BASE_URL}/materia/pesquisa/lista",
                             params={"sigla": t, "ementa": tema, "tramitando": "S"})
            if not data:
                continue
            materias = (
                data.get("PesquisaBasicaMateria", {})
                    .get("Materias", {})
                    .get("Materia", [])
            )
            if isinstance(materias, dict):
                materias = [materias]
            for mat in materias:
                resultado.append({
                    "Tipo": mat.get("Sigla", t),
                    "Número": str(int(mat.get("Numero", "0"))),
                    "Ano": mat.get("Ano", ""),
                    "Ementa": (mat.get("Ementa", "N/D") or "")[:120] + "...",
                    "Autor": mat.get("Autor", "N/D"),
                })
            if len(resultado) >= itens:
                break
        except Exception:
            continue
    return resultado[:itens]
