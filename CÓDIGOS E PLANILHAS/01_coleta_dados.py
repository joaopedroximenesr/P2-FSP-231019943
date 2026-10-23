"""
01_coleta_dados.py — Coleta reprodutível dos dados BRUTOS nas APIs oficiais (P2 FSP, matrícula 231019943).

Reproduz exatamente as consultas usadas para gerar 02_dados_brutos_atualizados/ (coleta original: 21/10/2026).
Requer acesso à internet e o pacote `requests`. Os arquivos são salvos com sufixo _recoleta para
não sobrescrever os brutos originais; compare-os para verificar revisões nas fontes.

Uso:
    python3 06_codigos_e_planilhas/01_coleta_dados.py            # coleta tudo
    python3 06_codigos_e_planilhas/01_coleta_dados.py siconfi    # só uma fonte (siconfi | ibge | eurostat | openalex)

Observação: a API do Siconfi limita a taxa de requisições (HTTP 429); o script espera e tenta de novo.
"""
import json, os, sys, time, datetime
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "02_dados_brutos_atualizados")
HOJE = datetime.datetime.now().isoformat(timespec="seconds")
S = requests.Session()


def get_json(url, params=None, tentativas=8):
    for t in range(tentativas):
        r = S.get(url, params=params, timeout=120)
        if r.status_code == 429:
            time.sleep(20)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Falha após {tentativas} tentativas: {url} {params}")


# ------------------------------------------------------------------ SICONFI (Tesouro Nacional)
SICONFI = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/"
FOCOS = {1302603: "Manaus", 1303403: "Parintins"}
ANEXOS = ["DCA-Anexo I-AB", "DCA-Anexo I-C", "DCA-Anexo I-D", "DCA-Anexo I-E"]


def dca(ente, ano, anexo):
    itens, off = [], 0
    while True:
        j = get_json(SICONFI + "dca", dict(an_exercicio=ano, no_anexo=anexo, id_ente=ente, offset=off))
        itens += j["items"]
        if not j.get("hasMore"):
            return itens
        off += len(j["items"])


def coleta_siconfi():
    # 1) DCA completa dos dois municípios focais, 2013–2025
    itens = []
    for ente in FOCOS:
        for ano in range(2013, 2026):
            for anexo in ANEXOS:
                itens += dca(ente, ano, anexo)
                time.sleep(0.6)
    meta = dict(fonte="Tesouro Nacional - API de Dados Abertos do SICONFI (DCA)", endpoint=SICONFI + "dca",
                entes=FOCOS, anos_consultados="2013-2025", anexos=ANEXOS, coletado_em=HOJE)
    json.dump(dict(meta=meta, items=itens), open(os.path.join(RAW, "siconfi", "siconfi_dca_manaus_parintins_recoleta.json"), "w"), ensure_ascii=False)
    # 2) extrato de entregas (verifica homologação, ex.: Parintins 2016)
    ext = []
    for ente in FOCOS:
        for ano in range(2013, 2027):
            ext += get_json(SICONFI + "extrato_entregas", dict(id_ente=ente, an_referencia=ano))["items"]
    json.dump(dict(meta=dict(fonte="API SICONFI extrato_entregas", coletado_em=HOJE), items=ext),
              open(os.path.join(RAW, "siconfi", "siconfi_extrato_entregas_manaus_parintins_recoleta.json"), "w"), ensure_ascii=False)


# ------------------------------------------------------------------ IBGE / SIDRA
IBGE = "https://servicodados.ibge.gov.br/api/v3/agregados/"


def coleta_ibge():
    L = "N6[1302603,1303403]"
    q = {
        "ipca_indice_mensal": (IBGE + "1737/periodos/201201-202609/variaveis/2266", {"localidades": "N1[all]"}),
        "ipca_var_anual_dez": (IBGE + "1737/periodos/201212|201312|201412|201512|201612|201712|201812|201912|202012|202112|202212|202312|202412|202512/variaveis/2265", {"localidades": "N1[all]"}),
        "pop_estimativas_6579": (IBGE + "6579/periodos/all/variaveis/9324", {"localidades": L}),
        "pop_censo2022_4714": (IBGE + "4714/periodos/2022/variaveis/93", {"localidades": L}),
        "pop_censo2010_1378": (IBGE + "1378/periodos/2010/variaveis/93", {"localidades": L, "classificacao": "1[0]|2[0]|287[0]|455[0]"}),
        "pib_municipal_5938": (IBGE + "5938/periodos/all/variaveis/37|498|513|517|6575|525|543|6574", {"localidades": L}),
        "pib_brasil_5938": (IBGE + "5938/periodos/all/variaveis/37", {"localidades": "N1[all]"}),
    }
    out = {"_meta": dict(fonte="IBGE - API de Agregados (SIDRA) v3", coletado_em=HOJE)}
    for k, (u, p) in q.items():
        r = S.get(u, params=p, timeout=120)
        r.raise_for_status()
        out[k] = dict(url=r.url, data=r.json())
    json.dump(out, open(os.path.join(RAW, "ibge", "ibge_ipca_pop_pib_recoleta.json"), "w"), ensure_ascii=False)


# ------------------------------------------------------------------ EUROSTAT
EURO = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"


def coleta_eurostat():
    base = [("geo", "ES"), ("sinceTimePeriod", "2012"), ("format", "JSON"), ("lang", "EN")]
    setores = [("sector", s) for s in ["S13", "S1311", "S1312", "S1313", "S1314"]]
    q = {
        "hicp_ES": ("prc_hicp_aind", [("coicop", "CP00"), ("unit", "INX_A_AVG")]),
        "gov_10a_main_ES": ("gov_10a_main", [("unit", "MIO_EUR"), ("unit", "PC_GDP")] + setores),
        "gov_10dd_edpt1_ES": ("gov_10dd_edpt1", [("unit", "MIO_EUR"), ("unit", "PC_GDP")] + setores),
        "nama_10_gdp_ES": ("nama_10_gdp", [("na_item", "B1GQ"), ("unit", "CP_MEUR"), ("unit", "CLV15_MEUR"), ("unit", "PD15_EUR")]),
        "demo_pjan_ES": ("demo_pjan", [("age", "TOTAL"), ("sex", "T")]),
        "gov_10a_taxag_ES": ("gov_10a_taxag", [("sector", "S13_S212"), ("unit", "PC_GDP"), ("unit", "MIO_EUR"), ("na_item", "D2_D5_D91_D61_M_D995")]),
    }
    out = {"_meta": dict(fonte="Eurostat - API de disseminação (JSON-stat 2.0)", coletado_em=HOJE)}
    for k, (ds, p) in q.items():
        r = S.get(EURO + ds, params=p + base, timeout=120)
        r.raise_for_status()
        out[k] = dict(url=r.url, data=r.json())
    json.dump(out, open(os.path.join(RAW, "eurostat", "espanha_eurostat_recoleta.json"), "w"), ensure_ascii=False)


# ------------------------------------------------------------------ OPENALEX (bibliometria)
def coleta_openalex():
    filtro = 'title_and_abstract.search:("flypaper effect" OR "fiscal illusion" OR "intergovernmental transfers" OR "intergovernmental grants"),type:article'
    filtro_pt = ('title_and_abstract.search:("transferências intergovernamentais" OR "efeito flypaper" OR "ilusão fiscal" OR '
                 '"transferencias intergubernamentales" OR "ilusión fiscal" OR "efecto flypaper" OR "transferências constitucionais"),type:article')
    sel = "id,doi,title,publication_year,authorships,primary_location,cited_by_count,keywords,topics,abstract_inverted_index,biblio,language,type,referenced_works"
    for nome, fl, paginas in [("openalex_recoleta_ingles.json", filtro, 13), ("openalex_recoleta_pt_es.json", filtro_pt, 5)]:
        res = []
        for pagina in range(1, paginas + 1):
            j = get_json("https://api.openalex.org/works", {"filter": fl, "select": sel, "per-page": 200, "page": pagina, "sort": "cited_by_count:desc"})
            res += j["results"]
            if len(j["results"]) < 200:
                break
        meta = dict(fonte="OpenAlex API", consulta=fl, coletado_em=HOJE, n=len(res))
        json.dump(dict(meta=meta, results=res), open(os.path.join(RAW, "openalex", nome), "w"), ensure_ascii=False)


if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else "tudo"
    for nome, fn in [("siconfi", coleta_siconfi), ("ibge", coleta_ibge), ("eurostat", coleta_eurostat), ("openalex", coleta_openalex)]:
        if alvo in (nome, "tudo"):
            print("coletando", nome, "...")
            fn()
    print("ok")
