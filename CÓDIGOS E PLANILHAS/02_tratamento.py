"""
02_tratamento.py — Constrói as bases TRATADAS a partir dos dados BRUTOS (P2 FSP, matrícula 231019943).

Entradas (02_dados_brutos_atualizados/):
  siconfi/siconfi_dca_manaus_parintins_2013-2025.json        DCA completa (Anexos I-AB, I-C, I-D, I-E) dos dois focos
  ibge/ibge_ipca_pop_pib.json                                IPCA mensal, população (estimativas e Censos) e PIB de Manaus e Parintins
  eurostat/espanha_eurostat.json
Saídas (03_dados_tratados/):
  deflatores.csv, populacao_manaus_parintins.csv, painel_focos_manaus_parintins.csv (+ .xlsx),
  espanha_subsetores.csv, auditoria_contas_focos.csv
Execução:  python3 06_codigos_e_planilhas/02_tratamento.py
"""
import json, os, sys, math, collections
import pandas as pd
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from harmonizacao import extrai_ente_ano  # noqa: E402
from jsonstat import jsonstat_to_rows      # noqa: E402

RAW = os.path.join(ROOT, "02_dados_brutos_atualizados")
OUT = os.path.join(ROOT, "03_dados_tratados")
os.makedirs(OUT, exist_ok=True)
ANO_BASE = 2025
PERIODO = list(range(2016, 2026))
FOCOS = {1302603: "Manaus", 1303403: "Parintins"}


def load(p):
    with open(os.path.join(RAW, p), encoding="utf-8") as f:
        return json.load(f)


def serie_sidra(js, var_id=None):
    """Converte resposta SIDRA v3 em DataFrame (cod, nome, ano, valor). '...' e '-' -> NaN."""
    rows = []
    for var in js:
        if var_id and str(var["id"]) != str(var_id):
            continue
        for res in var["resultados"]:
            for s in res["series"]:
                for per, v in s["serie"].items():
                    try:
                        val = float(v)
                    except (TypeError, ValueError):
                        val = np.nan
                    rows.append(dict(cod_ibge=int(s["localidade"]["id"]), nome=s["localidade"]["nome"],
                                     periodo=per, valor=val, variavel=var["variavel"], var_id=var["id"]))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 1. Deflatores
ibge = load("ibge/ibge_ipca_pop_pib.json")
ipca = serie_sidra(ibge["ipca_indice_mensal"]["data"], 2266)
ipca["ano"] = ipca.periodo.str[:4].astype(int)
ipca_ano = ipca.groupby("ano").agg(ipca_indice_medio=("valor", "mean"), meses=("valor", "count")).reset_index()
ipca_ano = ipca_ano[ipca_ano.meses == 12]
base = ipca_ano.loc[ipca_ano.ano == ANO_BASE, "ipca_indice_medio"].iloc[0]
ipca_ano["fator_ipca_" + str(ANO_BASE)] = base / ipca_ano.ipca_indice_medio

eu = load("eurostat/espanha_eurostat.json")
hicp = pd.DataFrame(jsonstat_to_rows(eu["hicp_ES"]["data"]))
hicp = hicp.rename(columns={"time": "ano", "value": "hicp_2015_100"})[["ano", "hicp_2015_100"]]
hicp["ano"] = hicp.ano.astype(int)
hb = hicp.loc[hicp.ano == ANO_BASE, "hicp_2015_100"].iloc[0]
hicp["fator_hicp_" + str(ANO_BASE)] = hb / hicp.hicp_2015_100
defl = ipca_ano.merge(hicp, on="ano", how="outer").sort_values("ano")
defl.to_csv(os.path.join(OUT, "deflatores.csv"), index=False)
FIPCA = dict(zip(ipca_ano.ano, ipca_ano["fator_ipca_" + str(ANO_BASE)]))
FHICP = dict(zip(hicp.ano, hicp["fator_hicp_" + str(ANO_BASE)]))

# ---------------------------------------------------------------- 2. População (oficial e harmonizada)
est = serie_sidra(ibge["pop_estimativas_6579"]["data"])
est["ano"] = est.periodo.astype(int)
c10 = serie_sidra(ibge["pop_censo2010_1378"]["data"])[["cod_ibge", "valor"]].rename(columns={"valor": "censo2010"})
c22 = serie_sidra(ibge["pop_censo2022_4714"]["data"])[["cod_ibge", "nome", "valor"]].rename(columns={"valor": "censo2022"})
pop_rows = []
for _, m in c22.merge(c10, on="cod_ibge").iterrows():
    e = est[est.cod_ibge == m.cod_ibge].set_index("ano").valor
    # datas de referência: censos em 01/08; estimativas em 01/07
    t10, t22 = 2010 + 7 / 12, 2022 + 7 / 12
    r = (m.censo2022 / m.censo2010) ** (1 / (t22 - t10)) - 1          # taxa geométrica intercensitária
    e24 = e.get(2024, np.nan)
    r2 = (e24 / m.censo2022) ** (1 / (2024 + 6 / 12 - t22)) - 1 if not np.isnan(e24) else np.nan
    for ano in PERIODO:
        oficial = e.get(ano, np.nan)
        fonte_of = "IBGE estimativa (tab. 6579)"
        if ano == 2022:
            oficial, fonte_of = m.censo2022, "IBGE Censo 2022 (tab. 4714)"
        if ano == 2023:
            oficial, fonte_of = np.nan, "sem publicação oficial do IBGE"
        if ano <= 2021:
            harm = m.censo2010 * (1 + r) ** (ano + 6 / 12 - t10)
            fonte_h = "interpolação geométrica Censo 2010–Censo 2022"
        elif ano == 2022:
            harm, fonte_h = m.censo2022, "Censo 2022"
        elif ano == 2023:
            harm = m.censo2022 * (1 + r2) ** (2023 + 6 / 12 - t22)
            fonte_h = "interpolação geométrica Censo 2022–estimativa 2024"
        else:
            harm, fonte_h = oficial, "IBGE estimativa pós-censo (tab. 6579)"
        pop_rows.append(dict(cod_ibge=m.cod_ibge, municipio=m.nome.replace(" (AM)", "").replace(" - AM", ""), ano=ano,
                             pop_oficial=oficial, fonte_pop_oficial=fonte_of,
                             pop_harmonizada=round(harm), fonte_pop_harmonizada=fonte_h))
pop = pd.DataFrame(pop_rows)
pop.to_csv(os.path.join(OUT, "populacao_manaus_parintins.csv"), index=False)

# ---------------------------------------------------------------- 3. PIB municipal
pib = serie_sidra(ibge["pib_municipal_5938"]["data"])
pib = pib[pib.var_id.astype(str).isin(["37", "498", "517", "525"])]
pib["ano"] = pib.periodo.astype(int)
pibw = pib.pivot_table(index=["cod_ibge", "ano"], columns="var_id", values="valor").reset_index()
pibw.columns = [str(c) for c in pibw.columns]
pibw = pibw.rename(columns={"37": "pib_mil", "498": "vab_mil", "517": "vab_industria_mil", "525": "vab_adm_publica_mil"})
for c in ["pib_mil", "vab_mil", "vab_industria_mil", "vab_adm_publica_mil"]:
    if c in pibw:
        pibw[c.replace("_mil", "")] = pibw[c] * 1000.0
        pibw = pibw.drop(columns=c)

# ---------------------------------------------------------------- 4. SICONFI — focos (DCA completa)
foc = load("siconfi/siconfi_dca_manaus_parintins_2013-2025.json")["items"]
g = collections.defaultdict(list)
for r in foc:
    g[(r["cod_ibge"], r["exercicio"])].append(r)
rows, aud = [], []
for (cod, ano), rr in sorted(g.items()):
    o, a = extrai_ente_ano(rr)
    o.update(cod_ibge=cod, ano=ano, municipio=FOCOS[cod], pop_siconfi=rr[0].get("populacao"))
    rows.append(o)
    for k, v in a.items():
        aud.append(dict(cod_ibge=cod, municipio=FOCOS[cod], ano=ano, variavel=k, contas_somadas=";".join(v)))
focos = pd.DataFrame(rows)
# anos sem DCA homologada ficam registrados como ausentes (nunca zero)
full = pd.MultiIndex.from_product([list(FOCOS), list(range(2014, 2026))], names=["cod_ibge", "ano"]).to_frame(index=False)
focos = full.merge(focos, on=["cod_ibge", "ano"], how="left")
focos["municipio"] = focos.cod_ibge.map(FOCOS)
focos["dca_disponivel"] = focos.rec_corrente.notna()
pd.DataFrame(aud).to_csv(os.path.join(OUT, "auditoria_contas_focos.csv"), index=False)


def deriva(df, fator_col="fator_ipca"):
    """Variáveis derivadas: receitas líquidas, arrecadação própria, dependência, reais e per capita."""
    df = df.copy()
    df["rec_corrente_liq"] = df.rec_corrente - df.ded_rec_corrente
    df["transf_correntes_liq"] = df.transf_correntes - df.ded_transf_correntes
    df["transf_total_liq"] = df.transf_correntes_liq + df.transf_capital.fillna(0)
    df["rec_total_liq"] = df.rec_corrente_liq + df.rec_capital.fillna(0)
    df["arrec_propria"] = df.rec_corrente - df.transf_correntes          # receitas correntes próprias (brutas)
    df["dep_transf"] = df.transf_total_liq / df.rec_total_liq             # grau de dependência
    df["autonomia_trib"] = df.rec_tributaria / df.rec_corrente_liq        # receita tributária / RCL
    df["resultado_orc"] = df.rec_total_liq - df.desp_total                # superávit(+)/déficit(−) orçamentário
    df[fator_col] = df.ano.map(FIPCA)
    monet = ["rec_total_liq", "rec_corrente_liq", "rec_tributaria", "iptu", "iss", "itbi", "irrf", "transf_correntes_liq",
             "transf_total_liq", "transf_capital", "fpm", "icms_cota", "ipva_cota", "fundeb_receb", "sus_corrente",
             "arrec_propria", "desp_total", "desp_corrente", "desp_pessoal", "desp_investimentos", "desp_saude",
             "desp_educacao", "resultado_orc", "pib"]
    for c in monet:
        if c in df:
            df[c + "_real"] = df[c] * df[fator_col]
            df[c + "_real_pc"] = df[c + "_real"] / df.pop_harmonizada
    return df


focos = focos.merge(pop[["cod_ibge", "ano", "pop_oficial", "pop_harmonizada"]], on=["cod_ibge", "ano"], how="left")
focos = focos.merge(pibw, on=["cod_ibge", "ano"], how="left")
focos = deriva(focos)
focos_p = focos[focos.ano.isin(PERIODO)].sort_values(["cod_ibge", "ano"])
focos_p.to_csv(os.path.join(OUT, "painel_focos_manaus_parintins.csv"), index=False)

# ---------------------------------------------------------------- 6. Espanha — governo geral e subsetores (Eurostat)
g10 = pd.DataFrame(jsonstat_to_rows(eu["gov_10a_main_ES"]["data"]))
g10 = g10[(g10.unit == "MIO_EUR")]
itens = ["TR", "TE", "B9", "D2REC", "D5REC", "D61REC", "D91REC", "D7REC", "D9REC", "D4REC", "P11_P12_P131",
         "D1PAY", "P51G", "D41PAY", "D7PAY", "D7PAY_S1312", "D7PAY_S1313", "D9PAY_S1312", "D9PAY_S1313"]
es = g10[g10.na_item.isin(itens)].pivot_table(index=["sector", "time"], columns="na_item", values="value").reset_index()
es = es.rename(columns={"time": "ano", "sector": "setor"})
es["ano"] = es.ano.astype(int)
edp = pd.DataFrame(jsonstat_to_rows(eu["gov_10dd_edpt1_ES"]["data"]))
gd = edp[(edp.na_item == "GD") & (edp.unit == "MIO_EUR")].rename(columns={"sector": "setor", "time": "ano", "value": "GD"})
gd["ano"] = gd.ano.astype(int)
es = es.merge(gd[["setor", "ano", "GD"]], on=["setor", "ano"], how="left")
gdp = pd.DataFrame(jsonstat_to_rows(eu["nama_10_gdp_ES"]["data"]))
gdp = gdp[gdp.unit == "CP_MEUR"].rename(columns={"time": "ano", "value": "PIB_MIO_EUR"})[["ano", "PIB_MIO_EUR"]]
gdp["ano"] = gdp.ano.astype(int)
popes = pd.DataFrame(jsonstat_to_rows(eu["demo_pjan_ES"]["data"])).rename(columns={"time": "ano", "value": "pop_1jan"})[["ano", "pop_1jan"]]
popes["ano"] = popes.ano.astype(int)
es = es.merge(gdp, on="ano", how="left").merge(popes, on="ano", how="left")
es["fator_hicp"] = es.ano.map(FHICP)
es["impostos_proprios"] = es[["D2REC", "D5REC", "D91REC"]].sum(axis=1, min_count=1)
es["transf_recebidas"] = es[["D7REC", "D9REC"]].sum(axis=1, min_count=1)   # inclui transf. intragovernamentais (D73, D92)
es["dep_transf"] = es.transf_recebidas / es.TR
es["autonomia_trib"] = es.impostos_proprios / es.TR
for c in ["TR", "TE", "B9", "transf_recebidas", "impostos_proprios", "GD", "PIB_MIO_EUR"]:
    es[c + "_pct_pib"] = 100 * es[c] / es.PIB_MIO_EUR
    es[c + "_real_pc_eur"] = es[c] * 1e6 * es.fator_hicp / es.pop_1jan
es = es[es.ano.isin(PERIODO)].sort_values(["setor", "ano"])
es.to_csv(os.path.join(OUT, "espanha_subsetores.csv"), index=False)

# ---------------------------------------------------------------- 7. Planilha consolidada
with pd.ExcelWriter(os.path.join(OUT, "base_tratada_P2_231019943.xlsx")) as xw:
    focos_p.to_excel(xw, sheet_name="focos_manaus_parintins", index=False)
    es.to_excel(xw, sheet_name="espanha_subsetores", index=False)
    pop.to_excel(xw, sheet_name="populacao", index=False)
    defl.to_excel(xw, sheet_name="deflatores", index=False)
print("OK — focos:", focos_p.shape, "| ES:", es.shape)
