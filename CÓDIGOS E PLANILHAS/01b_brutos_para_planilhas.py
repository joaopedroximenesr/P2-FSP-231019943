"""
01b_brutos_para_planilhas.py — Converte os arquivos BRUTOS (JSON das APIs) em tabelas editáveis (CSV e XLSX),
sem nenhuma transformação de conteúdo: cada linha corresponde a um registro original da fonte.
Saída: 02_dados_brutos_atualizados/planilhas/
"""
import os, json, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from jsonstat import jsonstat_to_rows  # noqa: E402

RAW = os.path.join(ROOT, "02_dados_brutos_atualizados")
OUT = os.path.join(RAW, "planilhas")
os.makedirs(OUT, exist_ok=True)
tabs = {}

# SICONFI — DCA (mantém todos os campos da API)
for nome, arq in [("siconfi_dca_manaus_parintins_2013_2025", "siconfi/siconfi_dca_manaus_parintins_2013-2025.json"),
                  ("siconfi_extrato_entregas_focos", "siconfi/siconfi_extrato_entregas_manaus_parintins.json")]:
    d = json.load(open(os.path.join(RAW, arq), encoding="utf-8"))
    tabs[nome] = pd.DataFrame(d["items"])


# IBGE — SIDRA (formato longo: variável, localidade, período, valor como publicado)
def sidra_long(js, consulta):
    rows = []
    for var in js:
        for res in var["resultados"]:
            classif = "; ".join(f"{c['nome']}={list(c['categoria'].values())[0]}" for c in res.get("classificacoes", []))
            for s in res["series"]:
                for per, v in s["serie"].items():
                    rows.append(dict(consulta=consulta, variavel_id=var["id"], variavel=var["variavel"], unidade=var["unidade"],
                                     classificacao=classif, cod_ibge=s["localidade"]["id"], localidade=s["localidade"]["nome"],
                                     periodo=per, valor_publicado=v))
    return rows


ib = []
for arq in ["ibge/ibge_ipca_pop_pib.json"]:
    d = json.load(open(os.path.join(RAW, arq), encoding="utf-8"))
    for k, v in d.items():
        if k.startswith("_"):
            continue
        js = v["data"] if isinstance(v, dict) and "data" in v else v
        ib += [dict(r, arquivo=os.path.basename(arq)) for r in sidra_long(js, k)]
tabs["ibge_sidra"] = pd.DataFrame(ib).drop_duplicates(subset=["consulta", "variavel_id", "cod_ibge", "periodo", "classificacao", "arquivo"])

# EUROSTAT — JSON-stat em formato longo
d = json.load(open(os.path.join(RAW, "eurostat/espanha_eurostat.json"), encoding="utf-8"))
eu = []
for k, v in d.items():
    if k.startswith("_"):
        continue
    for r in jsonstat_to_rows(v["data"]):
        eu.append(dict(r, tabela=k, url=v["url"]))
tabs["eurostat_espanha"] = pd.DataFrame(eu)

# OPENALEX — uma linha por artigo
for nome, arq in [("openalex_corpus_ingles", "openalex/openalex_flypaper_fiscalillusion_transfers.json"),
                  ("openalex_corpus_pt_es", "openalex/openalex_termos_pt_es.json")]:
    res = json.load(open(os.path.join(RAW, arq), encoding="utf-8"))["results"]
    rows = []
    for w in res:
        src = (w.get("primary_location") or {}).get("source") or {}
        ii = w.get("abstract_inverted_index") or {}
        pos = {p: t for t, ps in ii.items() for p in ps}
        rows.append(dict(openalex_id=w["id"], doi=w.get("doi"), ano=w.get("publication_year"), titulo=w.get("title"),
                         autores="; ".join(a["author"]["display_name"] for a in w.get("authorships", [])),
                         paises="; ".join(sorted({c for a in w.get("authorships", []) for c in (a.get("countries") or [])})),
                         periodico=src.get("display_name"), tipo_fonte=src.get("type"), citacoes=w.get("cited_by_count"),
                         palavras_chave="; ".join(k["display_name"] for k in (w.get("keywords") or [])),
                         n_referencias=len(w.get("referenced_works") or []), resumo=" ".join(pos[i] for i in sorted(pos))))
    tabs[nome] = pd.DataFrame(rows)

for nome, df in tabs.items():
    df.to_csv(os.path.join(OUT, nome + ".csv"), index=False, encoding="utf-8-sig")
with pd.ExcelWriter(os.path.join(OUT, "dados_brutos_atualizados.xlsx")) as xw:
    for nome, df in tabs.items():
        df.to_excel(xw, sheet_name=nome[:31], index=False)
for nome, df in tabs.items():
    print(f"{nome}: {df.shape}")
