"""
04_numeros_artigo.py — Exporta os números citados no texto do artigo como macros LaTeX (08_artigo/numeros.tex),
garantindo que cada valor do texto venha diretamente dos resultados reprodutíveis.
Arredondamento: regra da ABNT NBR 5891 (meio para cima), com vírgula decimal.
"""
import os, json
import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TD, TAB, BIB = (os.path.join(ROOT, p) for p in ("03_dados_tratados", "07_resultados/tabelas", "07_resultados/bibliometria"))
out = {}


def br(x, d=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n.d."
    q = Decimal(str(x)).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    s = f"{q:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def mac(nome, valor):
    out[nome] = valor


f = pd.read_csv(os.path.join(TD, "painel_focos_manaus_parintins.csv"))
es = pd.read_csv(os.path.join(TD, "espanha_subsetores.csv"))
res = json.load(open(os.path.join(TAB, "resultados_resumo.json"), encoding="utf-8"))
reg = pd.read_csv(os.path.join(TAB, "tab4_regressoes_manaus_parintins.csv"))

for mun, tag in [("Manaus", "Man"), ("Parintins", "Par")]:
    d = f[(f.municipio == mun) & f.rec_corrente.notna()].sort_values("ano")
    a0, a1 = d.iloc[0], d.iloc[-1]
    mac(f"anoIni{tag}", str(int(a0.ano)))
    mac(f"dep{tag}Media", br(100 * d.dep_transf.mean(), 1))
    mac(f"dep{tag}Ini", br(100 * a0.dep_transf, 1)); mac(f"dep{tag}Fim", br(100 * a1.dep_transf, 1))
    mac(f"dep{tag}Min", br(100 * d.dep_transf.min(), 1)); mac(f"dep{tag}Max", br(100 * d.dep_transf.max(), 1))
    mac(f"aut{tag}Media", br(100 * d.autonomia_trib.mean(), 1))
    mac(f"aut{tag}Ini", br(100 * a0.autonomia_trib, 1)); mac(f"aut{tag}Fim", br(100 * a1.autonomia_trib, 1))
    for v, n in [("rec_tributaria_real_pc", "Trib"), ("transf_total_liq_real_pc", "Transf"), ("desp_total_real_pc", "Desp"),
                 ("rec_total_liq_real_pc", "Rec"), ("fpm_real_pc", "Fpm"), ("desp_pessoal_real_pc", "Pessoal"),
                 ("desp_saude_real_pc", "Saude"), ("desp_educacao_real_pc", "Educ"), ("desp_investimentos_real_pc", "Invest")]:
        mac(f"{n.lower()}{tag}Ini", br(a0[v])); mac(f"{n.lower()}{tag}Fim", br(a1[v]))
        mac(f"{n.lower()}{tag}Var", br(100 * (a1[v] / a0[v] - 1), 1))
    mac(f"fpmShare{tag}", br(100 * (d.fpm / d.transf_total_liq).mean(), 1))
    mac(f"icmsShare{tag}", br(100 * (d.icms_cota / d.transf_total_liq).mean(), 1))
    mac(f"fundebShare{tag}", br(100 * (d.fundeb_receb / d.transf_total_liq).mean(), 1))
    mac(f"susShare{tag}", br(100 * (d.sus_corrente / d.transf_total_liq).mean(), 1))
    mac(f"issShare{tag}", br(100 * (d.iss / d.rec_tributaria).mean(), 1))
    mac(f"iptuShare{tag}", br(100 * (d.iptu / d.rec_tributaria).mean(), 1))
    mac(f"resPos{tag}", str(int((d.resultado_orc > 0).sum()))); mac(f"nAnos{tag}", str(len(d)))
    mac(f"resMin{tag}", br(d.resultado_orc_real.min() / 1e6, 1)); mac(f"resMax{tag}", br(d.resultado_orc_real.max() / 1e6, 1))
    mac(f"anoResMin{tag}", str(int(d.loc[d.resultado_orc_real.idxmin(), "ano"])))
    mac(f"anoResMax{tag}", str(int(d.loc[d.resultado_orc_real.idxmax(), "ano"])))
    mac(f"pibpc{tag}Ini", br(d.pib_real_pc.dropna().iloc[0])); mac(f"pibpc{tag}Fim", br(d.pib_real_pc.dropna().iloc[-1]))
    p = f[f.municipio == mun]
    p21 = p[p.ano == 2021].iloc[0]
    mac(f"popOf{tag}Vinte", br(p21.pop_oficial, 0)); mac(f"popHa{tag}Vinte", br(p21.pop_harmonizada, 0))
    mac(f"popDif{tag}", br(100 * (p21.pop_oficial / p21.pop_harmonizada - 1), 1))
    mac(f"pop{tag}Fim", br(p[p.ano == 2025].pop_harmonizada.iloc[0], 0))

for s, tag in [("S1312", "CA"), ("S1313", "Loc"), ("S1311", "Cen"), ("S13", "Ger")]:
    d = es[es.setor == s].sort_values("ano")
    mac(f"esDep{tag}", br(100 * d.dep_transf.mean(), 1))
    mac(f"esDep{tag}Ini", br(100 * d.dep_transf.iloc[0], 1)); mac(f"esDep{tag}Fim", br(100 * d.dep_transf.iloc[-1], 1))
    mac(f"esAut{tag}", br(100 * d.autonomia_trib.mean(), 1))
    mac(f"esBnove{tag}Ini", br(d.B9_pct_pib.iloc[0], 1)); mac(f"esBnove{tag}Fim", br(d.B9_pct_pib.iloc[-1], 1))
    mac(f"esBnove{tag}Media", br(d.B9_pct_pib.mean(), 1))
    mac(f"esGD{tag}Ini", br(d.GD_pct_pib.iloc[0], 1)); mac(f"esGD{tag}Fim", br(d.GD_pct_pib.iloc[-1], 1))
    mac(f"esTE{tag}Ini", br(d.TE_pct_pib.iloc[0], 1)); mac(f"esTE{tag}Fim", br(d.TE_pct_pib.iloc[-1], 1))
g = es[es.setor == "S13"].set_index("ano")
mac("esGDvinte", br(g.loc[2020, "GD_pct_pib"], 1)); mac("esBnoveVinte", br(g.loc[2020, "B9_pct_pib"], 1))
mac("esSupLocAnos", str(int((es[es.setor == "S1313"].B9_pct_pib > 0).sum())))

R = reg.set_index(["modelo", "termo"])
ALIAS = {"transf": "Tr", "ln_transf": "Tr", "dtransf": "Tr", "transf_o": "Tr", "pib": "Pib", "ln_pib": "Pib", "dpib": "Pib", "pib_o": "Pib",
         "fpm": "Fpm", "outras_transf": "Out", "par": "Par", "t": "Tend", "Intercept": "Const"}
TAGS = {"M1_niveis": "Um", "M2_tendencia": "Dois", "M3_fpm": "Tres", "M4_log": "Quatro", "M5_primeiras_diferencas": "Cinco",
        "M6_pop_oficial": "Seis", "M7_esforco_fiscal": "Sete", "M8_sem_pib_2016_2025": "Oito", "M9_so_Manaus": "Nove", "M10_so_Parintins": "Dez"}
for m, tag in TAGS.items():
    sub = R.loc[m]
    for termo in sub.index:
        t = ALIAS[termo]
        mac(f"b{t}{tag}", br(sub.loc[termo, "coef"], 3)); mac(f"se{t}{tag}", br(sub.loc[termo, "ep"], 3))
        mac(f"p{t}{tag}", "< 0{,}001" if sub.loc[termo, "p"] < 0.001 else br(sub.loc[termo, "p"], 3))
    mm = res["meta"][m]
    mac(f"n{tag}", str(mm["nobs"])); mac(f"rdois{tag}", br(mm["r2_aj"], 3))
for m, tag in TAGS.items():
    if m in res["testes"]:
        t = res["testes"][m]
        mac(f"wt{tag}", br(t["t"], 2)); mac(f"wp{tag}", "< 0{,}001" if t["p"] < 0.001 else br(t["p"], 3))
mac("razaoFly", br(R.loc[("M1_niveis", "transf"), "coef"] / R.loc[("M1_niveis", "pib"), "coef"], 0))
dg = res["diagnosticos"]
mac("vifTr", br(dg["VIF"]["transf"], 2)); mac("vifPib", br(dg["VIF"]["pib"], 1)); mac("vifPar", br(dg["VIF"]["par"], 1))
mac("bpLM", br(dg["BreuschPagan"]["LM"], 2)); mac("bpP", br(dg["BreuschPagan"]["p"], 3))
mac("swW", br(dg["ShapiroWilk"]["W"], 3)); mac("swP", br(dg["ShapiroWilk"]["p"], 3))
mac("resetF", br(dg["RESET"]["F"], 2)); mac("resetP", br(dg["RESET"]["p"], 3))
mac("arRho", br(dg["AR1_residuos"]["rho"], 2)); mac("arP", br(dg["AR1_residuos"]["p"], 3))
mac("dwMan", br(dg["DurbinWatson"]["Manaus"], 2)); mac("dwPar", br(dg["DurbinWatson"]["Parintins"], 2))
mac("cookMax", br(dg["Cook_max"]["valor"], 2)); mac("cookAno", str(dg["Cook_max"]["ano"])); mac("cookMun", dg["Cook_max"]["municipio"])
pm = pd.read_csv(os.path.join(TAB, "tab_propensoes_medias.csv")).set_index("municipio")
for mun, tag in [("Manaus", "Man"), ("Parintins", "Par")]:
    mac(f"propTr{tag}", br(pm.loc[mun, "desp_por_transf"], 2)); mac(f"propDe{tag}", str(int(pm.loc[mun, "de"])))
    mac(f"dDesp{tag}", br(1000 * pm.loc[mun, "d_desp"], 2)); mac(f"dTransf{tag}", br(1000 * pm.loc[mun, "d_transf"], 2))
    mac(f"dPib{tag}", br(1000 * pm.loc[mun, "d_pib"], 2))
e = res["espanha"]
mac("esbTr", br(e["coef"]["TRF_pc"], 3)); mac("esbPib", br(e["coef"]["PIB_pc"], 3)); mac("esN", str(e["n"]))
mac("espTr", "< 0{,}001" if e["p"]["TRF_pc"] < 0.001 else br(e["p"]["TRF_pc"], 3)); mac("espPib", br(e["p"]["PIB_pc"], 3))
mac("esWt", br(e["teste_TRF_igual_PIB"]["t"], 2))

# bibliometria
txt = open(os.path.join(BIB, "summary_bibliometrix.txt"), encoding="utf-8").read()
import re
def grab(lbl):
    m = re.search(lbl + r"\s+([\d.]+)", txt)
    return m.group(1) if m else "n.d."
mac("bibDocs", br(float(grab("Documents")), 0)); mac("bibFontes", grab(r"Sources \(Journals, Books, etc\)"))
mac("bibAutores", br(float(grab(r"Authors ")), 0)); mac("bibCresc", grab(r"Annual Growth Rate %").replace(".", ","))
mac("bibCit", grab(r"Average citations per doc").replace(".", ",")); mac("bibCoaut", grab(r"Co-Authors per Doc").replace(".", ","))
mac("bibIntl", grab(r"International co-authorships %").replace(".", ","))
mac("bibSingle", grab(r"Single-authored docs"))
ap = pd.read_csv(os.path.join(BIB, "producao_anual.csv"))
mac("bibAnoMin", str(int(ap.ano.min()))); mac("bibAnoMax", str(int(ap.ano.max())))
mac("bibAteDoisMil", str(int(ap[ap.ano < 2000].artigos.sum()))); mac("bibDesdeVinte", str(int(ap[ap.ano >= 2020].artigos.sum())))
mac("bibPctDesdeVinte", br(100 * ap[ap.ano >= 2020].artigos.sum() / ap.artigos.sum(), 1))
tt = pd.read_csv(os.path.join(BIB, "termos_por_ano.csv"))
mac("bibFly", str(int(tt.flypaper.sum()))); mac("bibIlu", str(int(tt.fiscal_illusion.sum()))); mac("bibDid", str(int(tt.did.sum())))
mac("bibDidDesdeVinte", str(int(tt[tt.ano >= 2020].did.sum())))
lot = open(os.path.join(BIB, "lotka.txt"), encoding="utf-8").read()
m = re.search(r"beta\s+C\s+R2\s+p_KS\s*\n\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", lot)
if m:
    mac("lotkaBeta", br(float(m.group(1)), 2)); mac("lotkaR", br(float(m.group(3)), 2)); mac("lotkaP", br(float(m.group(4)), 2))
fon = pd.read_csv(os.path.join(BIB, "top_fontes.csv")); pai = pd.read_csv(os.path.join(BIB, "top_paises.csv"))
for i in range(5):
    mac("fonte" + "ABCDE"[i], fon.item.iloc[i].title().replace("&Amp", "\\&").replace("Of", "of").replace("And", "and"))
    mac("fonteN" + "ABCDE"[i], str(fon.n.iloc[i]))
for i in range(6):
    mac("pais" + "ABCDEF"[i], pai.item.iloc[i].title()); mac("paisN" + "ABCDEF"[i], str(pai.n.iloc[i]))
mac("paisBR", str(int(pai.loc[pai.item == "BRAZIL", "n"].iloc[0])) if (pai.item == "BRAZIL").any() else "n.d.")
mac("paisES", str(int(pai.loc[pai.item == "SPAIN", "n"].iloc[0])) if (pai.item == "SPAIN").any() else "n.d.")

with open(os.path.join(ROOT, "08_artigo", "numeros.tex"), "w", encoding="utf-8") as fh:
    fh.write("% Gerado automaticamente por 06_codigos_e_planilhas/04_numeros_artigo.py — não editar à mão\n")
    for k, v in out.items():
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
json.dump(out, open(os.path.join(TAB, "numeros_artigo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(out), "macros")

# ---- Tabela 1 no formato de Baker et al. (2022) e fluxo de seleção do corpus
out2 = {}
st = pd.read_csv(os.path.join(BIB, "tabela1_baker_subtotais.csv")).set_index("grupo")
ex = pd.read_csv(os.path.join(BIB, "tabela1_baker_extras.csv")).iloc[0]
fl = pd.read_csv(os.path.join(BIB, "fluxo_selecao_corpus.csv")).set_index("etapa").n
tot, cor = st.loc["Total dos 15 periódicos"], st.loc["Corpus completo (todos os periódicos)"]
for k, v in {"tUmTot": br(tot.transferencias, 0), "tUmFly": br(tot.flypaper_ilusao, 0), "tUmPct": br(tot.pct, 1),
             "tUmDezTot": br(tot.desde_2010, 0), "tUmDezPct": br(100 * tot.desde_2010 / tot.flypaper_ilusao, 1),
             "tUmFin": br(st.loc["Finanças públicas e escolha pública"].transferencias, 0), "tUmFinFly": br(st.loc["Finanças públicas e escolha pública"].flypaper_ilusao, 0),
             "tUmFed": br(st.loc["Federalismo, orçamento e governo local"].transferencias, 0), "tUmFedFly": br(st.loc["Federalismo, orçamento e governo local"].flypaper_ilusao, 0),
             "tUmBr": br(st.loc["Periódicos brasileiros"].transferencias, 0), "tUmBrFly": br(st.loc["Periódicos brasileiros"].flypaper_ilusao, 0),
             "tUmBrPct": br(st.loc["Periódicos brasileiros"].pct, 1),
             "corpTot": br(cor.transferencias, 0), "corpFly": br(cor.flypaper_ilusao, 0), "corpPct": br(cor.pct, 1),
             "corpDez": br(cor.desde_2010, 0), "corpDezPct": br(100 * cor.desde_2010 / cor.flypaper_ilusao, 1),
             "nDid": br(ex.n_did, 0), "nDidQuinze": br(ex.n_did_desde_2015, 0), "nBrasil": br(ex.n_brasil, 0), "nBrasilFly": br(ex.n_brasil_fly, 0),
             "flEn": br(fl["registros_ingles"], 0), "flPt": br(fl["registros_pt_es"], 0), "flUnicos": br(fl["unicos"], 0),
             "flSemAut": br(fl["sem_autoria"], 0), "flNaoPer": br(fl["nao_periodico"], 0), "flFinal": br(fl["corpus_final"], 0),
             "flDoisMilVinteSeis": br(fl["unicos"] - fl["sem_autoria"] - fl["nao_periodico"] - fl["corpus_final"], 0)}.items():
    out2[k] = v
with open(os.path.join(ROOT, "08_artigo", "numeros.tex"), "a", encoding="utf-8") as fh:
    for k, v in out2.items():
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(len(out2), "macros da Tabela 1")
