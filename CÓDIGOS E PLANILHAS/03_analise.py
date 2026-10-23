"""
03_analise.py — Estatísticas descritivas, regressões e gráficos (P2 FSP, matrícula 231019943).
Lê 03_dados_tratados/ e grava em 07_resultados/{tabelas,figuras}.
Execução: python3 06_codigos_e_planilhas/03_analise.py
"""
import os, json, warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan
from scipy import stats
from linearmodels.panel import PanelOLS, RandomEffects, compare
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TD = os.path.join(ROOT, "03_dados_tratados")
TAB = os.path.join(ROOT, "07_resultados", "tabelas")
FIG = os.path.join(ROOT, "07_resultados", "figuras")
BIB = os.path.join(ROOT, "07_resultados", "bibliometria")
for d in (TAB, FIG):
    os.makedirs(d, exist_ok=True)

# ----------------------------------------------------------------- estilo
COR = {"Manaus": "#1f5a96", "Parintins": "#c0392b", "Demais AM": "#9aa5b1", "Espanha_local": "#2e7d32",
     "Espanha_regional": "#8e6c00", "Espanha_central": "#6a1b9a"}
plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": .25, "figure.dpi": 150,
                     "savefig.bbox": "tight", "legend.frameon": False})


def brl(x, pos=None):
    return f"R$ {x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def trunc2(x):
    """Formata com duas casas decimais SEM arredondamento (truncamento), padrão adotado no trabalho anterior."""
    if pd.isna(x):
        return "n.d."
    s = np.trunc(x * 100) / 100
    return f"{s:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


focos = pd.read_csv(os.path.join(TD, "painel_focos_manaus_parintins.csv"))
es = pd.read_csv(os.path.join(TD, "espanha_subsetores.csv"))
res = {}

# ================================================================= 1. Descritivas — focos
vars_desc = [("rec_total_liq_real_pc", "Receita total líquida per capita (R$ 2025)"),
             ("arrec_propria_real_pc", "Receita corrente própria per capita (R$ 2025)"),
             ("rec_tributaria_real_pc", "Receita tributária per capita (R$ 2025)"),
             ("transf_total_liq_real_pc", "Transferências líquidas per capita (R$ 2025)"),
             ("fpm_real_pc", "FPM per capita (R$ 2025)"),
             ("icms_cota_real_pc", "Cota-parte do ICMS per capita (R$ 2025)"),
             ("fundeb_receb_real_pc", "FUNDEB recebido per capita (R$ 2025)"),
             ("desp_total_real_pc", "Despesa empenhada per capita (R$ 2025)"),
             ("desp_pessoal_real_pc", "Despesa com pessoal per capita (R$ 2025)"),
             ("desp_investimentos_real_pc", "Investimentos per capita (R$ 2025)"),
             ("desp_saude_real_pc", "Saúde per capita (R$ 2025)"),
             ("desp_educacao_real_pc", "Educação per capita (R$ 2025)"),
             ("dep_transf", "Dependência de transferências (proporção)"),
             ("autonomia_trib", "Receita tributária / RCL (proporção)"),
             ("pib_real_pc", "PIB per capita (R$ 2025)")]
linhas = []
for mun in ["Manaus", "Parintins"]:
    d = focos[focos.municipio == mun]
    for v, lab in vars_desc:
        s = d[v].dropna()
        if s.empty:
            continue
        y0, y1 = d.loc[s.index[0], "ano"], d.loc[s.index[-1], "ano"]
        cresc = (s.iloc[-1] / s.iloc[0] - 1) * 100 if s.iloc[0] != 0 and not v.startswith(("dep_", "autonomia")) else np.nan
        linhas.append(dict(municipio=mun, variavel=lab, n=len(s), media=s.mean(), dp=s.std(), minimo=s.min(),
                           maximo=s.max(), primeiro_ano=int(y0), valor_inicial=s.iloc[0], ultimo_ano=int(y1),
                           valor_final=s.iloc[-1], variacao_pct=cresc))
desc = pd.DataFrame(linhas)
desc.to_csv(os.path.join(TAB, "tab1_descritivas_focos.csv"), index=False)

# tabela anual (nominal e real) para o artigo e conferência
anual_cols = ["municipio", "ano", "pop_harmonizada", "rec_total_liq", "rec_tributaria", "transf_total_liq", "fpm",
              "desp_total", "resultado_orc", "fator_ipca", "rec_total_liq_real_pc", "rec_tributaria_real_pc",
              "transf_total_liq_real_pc", "desp_total_real_pc", "dep_transf", "autonomia_trib"]
focos[anual_cols].to_csv(os.path.join(TAB, "tab2_serie_anual_focos.csv"), index=False)

# ================================================================= 2. Descritivas — Espanha
es_cols = ["setor", "ano", "TR_pct_pib", "TE_pct_pib", "B9_pct_pib", "GD_pct_pib", "dep_transf", "autonomia_trib",
           "TE_real_pc_eur", "transf_recebidas_real_pc_eur"]
es[es_cols].to_csv(os.path.join(TAB, "tab3_espanha_subsetores.csv"), index=False)

# ================================================================= 3. Regressões — Manaus e Parintins (amostra pequena)
# Apenas os dois municípios atribuídos. Os dados são empilhados (município-ano) com efeito fixo de município
# (dummy de Parintins). Erros-padrão HC3, recomendados para amostras pequenas, e distribuição t de Student.
d = focos.copy().sort_values(["municipio", "ano"])
d["desp"] = d.desp_total_real_pc / 1000            # milhares de R$ de 2025 per capita
d["transf"] = d.transf_total_liq_real_pc / 1000
d["fpm"] = d.fpm_real_pc / 1000
d["outras_transf"] = (d.transf_total_liq_real_pc - d.fpm_real_pc) / 1000
d["pib"] = d.pib_real_pc / 1000
d["trib"] = d.rec_tributaria_real_pc / 1000
d["ln_desp"], d["ln_transf"], d["ln_pib"] = np.log(d.desp_total_real_pc), np.log(d.transf_total_liq_real_pc), np.log(d.pib_real_pc)
d["par"] = (d.municipio == "Parintins").astype(int)
d["t"] = d.ano - 2016
for c in ["desp", "transf", "pib"]:
    d["d" + c] = d.groupby("municipio")[c].diff()
d["desp_o"] = d.desp_total_real / d.pop_oficial / 1000
d["transf_o"] = d.transf_total_liq_real / d.pop_oficial / 1000
d["pib_o"] = d.pib_real / d.pop_oficial / 1000
base = d.dropna(subset=["desp", "transf", "pib"])          # 2016(17)–2023
todos = d.dropna(subset=["desp", "transf"])                # 2016(17)–2025
fdif = d.dropna(subset=["ddesp", "dtransf", "dpib"])
po = d.dropna(subset=["desp_o", "transf_o", "pib_o"])
base.to_csv(os.path.join(TAB, "amostra_regressoes.csv"), index=False)
rg = d.copy()


def ols(fm, data):
    return smf.ols(fm, data).fit(cov_type="HC3", use_t=True)


M = {}
M["M1_niveis"] = ols("desp ~ transf + pib + par", base)
M["M2_tendencia"] = ols("desp ~ transf + pib + par + t", base)
M["M3_fpm"] = ols("desp ~ fpm + outras_transf + pib + par", base)
M["M4_log"] = ols("ln_desp ~ ln_transf + ln_pib + par", base)
M["M5_primeiras_diferencas"] = ols("ddesp ~ dtransf + dpib", fdif)
M["M6_pop_oficial"] = ols("desp_o ~ transf_o + pib_o + par", po)
M["M7_esforco_fiscal"] = ols("trib ~ transf + pib + par", base)
M["M8_sem_pib_2016_2025"] = ols("desp ~ transf + par", todos)
M["M9_so_Manaus"] = ols("desp ~ transf + pib", base[base.municipio == "Manaus"])
M["M10_so_Parintins"] = ols("desp ~ transf + pib", base[base.municipio == "Parintins"])
tidies, meta = [], {}
for k, r in M.items():
    for termo in r.params.index:
        tidies.append(dict(modelo=k, termo=termo, coef=r.params[termo], ep=r.bse[termo], t=r.tvalues[termo], p=r.pvalues[termo]))
    meta[k] = dict(nobs=int(r.nobs), r2=float(r.rsquared), r2_aj=float(r.rsquared_adj), gl_resid=float(r.df_resid))
tid = pd.DataFrame(tidies)
tid.to_csv(os.path.join(TAB, "tab4_regressoes_manaus_parintins.csv"), index=False)

testes = {}
for k, h in [("M1_niveis", "transf - pib = 0"), ("M2_tendencia", "transf - pib = 0"), ("M3_fpm", "fpm - pib = 0"),
             ("M4_log", "ln_transf - ln_pib = 0"), ("M5_primeiras_diferencas", "dtransf - dpib = 0"), ("M6_pop_oficial", "transf_o - pib_o = 0"),
             ("M8_sem_pib_2016_2025", None), ("M9_so_Manaus", "transf - pib = 0"), ("M10_so_Parintins", "transf - pib = 0")]:
    if h:
        tt = M[k].t_test(h)
        testes[k] = dict(hipotese=h, diferenca=float(np.ravel(tt.effect)[0]), t=float(np.ravel(tt.tvalue)[0]), p=float(np.ravel(tt.pvalue)[0]))

# ---- diagnósticos do modelo M1 (estimado também por MQO comum para os testes)
from statsmodels.stats.diagnostic import linear_reset
from statsmodels.stats.stattools import durbin_watson
m1 = smf.ols("desp ~ transf + pib + par", base).fit()
X = base[["transf", "pib", "par"]].assign(const=1.0)
vif = {c: variance_inflation_factor(X.values, i) for i, c in enumerate(X.columns) if c != "const"}
bp = het_breuschpagan(m1.resid, m1.model.exog)
sw = stats.shapiro(m1.resid)
reset = linear_reset(m1, power=2, use_f=True)
res_df = base.assign(e=m1.resid.values)
res_df["e_l"] = res_df.groupby("municipio").e.shift()
ar = smf.ols("e ~ e_l - 1", res_df.dropna(subset=["e_l"])).fit()
dw = {mun: float(durbin_watson(res_df[res_df.municipio == mun].e)) for mun in ["Manaus", "Parintins"]}
infl = m1.get_influence()
cook = infl.cooks_distance[0]
imax = int(np.argmax(cook))
diag = dict(VIF=vif, BreuschPagan=dict(LM=bp[0], p=bp[1]), ShapiroWilk=dict(W=sw.statistic, p=sw.pvalue),
            RESET=dict(F=float(reset.fvalue), p=float(reset.pvalue)), AR1_residuos=dict(rho=float(ar.params["e_l"]), p=float(ar.pvalues["e_l"])),
            DurbinWatson=dw, Cook_max=dict(valor=float(cook[imax]), municipio=base.iloc[imax].municipio, ano=int(base.iloc[imax].ano), limiar_4n=4 / len(base)),
            nota="Diagnósticos do modelo M1 (desp ~ transf + pib + Parintins), MQO, 2016–2023.")

# ---- propensões médias (variação acumulada): quanto a despesa variou por real de variação das transferências e do PIB
prop = []
for mun in ["Manaus", "Parintins"]:
    b = base[base.municipio == mun].sort_values("ano"); a0, a1 = b.iloc[0], b.iloc[-1]
    prop.append(dict(municipio=mun, de=int(a0.ano), ate=int(a1.ano), d_desp=a1.desp - a0.desp, d_transf=a1.transf - a0.transf, d_pib=a1.pib - a0.pib,
                     desp_por_transf=(a1.desp - a0.desp) / (a1.transf - a0.transf), desp_por_pib=(a1.desp - a0.desp) / (a1.pib - a0.pib)))
pd.DataFrame(prop).to_csv(os.path.join(TAB, "tab_propensoes_medias.csv"), index=False)

# ================================================================= 4. Espanha — associação descritiva (CCAA e locais)
esr = es[es.setor.isin(["S1312", "S1313"])].copy()
esr["TE_pc"] = esr.TE_real_pc_eur / 1000
esr["TRF_pc"] = esr.transf_recebidas_real_pc_eur / 1000
esr["PIB_pc"] = esr.PIB_MIO_EUR_real_pc_eur / 1000
es_m = smf.ols("TE_pc ~ TRF_pc + PIB_pc + C(setor)", data=esr).fit(cov_type="HC1")
pd.DataFrame(dict(coef=es_m.params, ep=es_m.bse, p=es_m.pvalues)).to_csv(os.path.join(TAB, "tab5_espanha_regressao.csv"))
es_test = es_m.t_test("TRF_pc - PIB_pc = 0")

# ================================================================= 5. Comparação com o trabalho anterior (P1)
p1 = dict(periodo="2013–2022", municipios="Maceió/AL e Duque de Caxias/RJ", deflator="IPCA (fator BCB, base 2022)",
          pais="Espanha (FMI WEO abr/2024)")

# ================================================================= 6. Figuras
anos = list(range(2016, 2026))

# Fig. 1 — composição real per capita da receita (focos)
fig, axs = plt.subplots(1, 2, figsize=(8.2, 3.2), sharey=True)
for ax, mun in zip(axs, ["Manaus", "Parintins"]):
    d = focos[focos.municipio == mun].set_index("ano").reindex(anos)
    prop = d.arrec_propria_real_pc
    trf = d.transf_total_liq_real_pc
    ax.bar(d.index, prop, color=COR[mun], label="Receita corrente própria")
    ax.bar(d.index, trf, bottom=prop, color=COR[mun], alpha=.35, label="Transferências líquidas")
    for a in d.index[d.rec_corrente.isna()]:
        ax.text(a, 150, "sem\nDCA", ha="center", fontsize=7, color="#555")
    ax.set_title(mun, fontsize=10, loc="left")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(brl))
    ax.set_xticks(anos[::1]); ax.tick_params(axis="x", labelsize=7, rotation=45)
axs[0].legend(fontsize=7, loc="upper left")
fig.savefig(os.path.join(FIG, "fig1_composicao_receita_focos.png"))
plt.close(fig)

# Fig. 2 — dependência de transferências: focos, mediana AM e Espanha (CCAA, locais)
fig, ax = plt.subplots(figsize=(7.2, 3.4))
for mun in ["Manaus", "Parintins"]:
    d = focos[focos.municipio == mun].set_index("ano").reindex(anos)
    ax.plot(d.index, 100 * d.dep_transf, marker="o", ms=3.5, color=COR[mun], label=mun)
for s, lab, col in [("S1312", "Espanha – Comunidades Autônomas", COR["Espanha_regional"]), ("S1313", "Espanha – entidades locais", COR["Espanha_local"])]:
    d = es[es.setor == s].set_index("ano")
    ax.plot(d.index, 100 * d.dep_transf, color=col, marker="s", ms=3, label=lab)
ax.set_ylabel("% da receita total"); ax.set_ylim(0, 100)
ax.legend(fontsize=7, ncol=2, loc="lower right")
fig.savefig(os.path.join(FIG, "fig2_dependencia_transferencias.png"))
plt.close(fig)

# Fig. 3 — transferências x despesa per capita, Manaus e Parintins (2016–2025), com retas por município
fig, ax = plt.subplots(figsize=(6.2, 3.8))
dd = rg.dropna(subset=["transf", "desp"])
for mun in ["Manaus", "Parintins"]:
    x = dd[dd.municipio == mun]
    ax.scatter(x.transf, x.desp, s=24, color=COR[mun], label=mun, zorder=3)
    for _, r in x.iterrows():
        ax.annotate(str(int(r.ano))[2:], (r.transf, r.desp), fontsize=6, xytext=(3, 2), textcoords="offset points", color=COR[mun])
    b = np.polyfit(x.transf, x.desp, 1); xs = np.linspace(x.transf.min(), x.transf.max(), 10)
    ax.plot(xs, b[0] * xs + b[1], color=COR[mun], lw=1)
lim = [1.5, max(dd.transf.max(), dd.desp.max()) * 1.05]
ax.plot(lim, lim, color="#333", lw=.8, ls=":", label=r"45° (R\$ 1 transferido = R\$ 1 gasto)")
ax.set_xlim(lim[0], lim[1]); ax.set_ylim(lim[0], lim[1])
ax.set_xlabel("Transferências líquidas per capita (mil R$ de 2025)"); ax.set_ylabel("Despesa empenhada per capita (mil R$ de 2025)")
ax.legend(fontsize=7, loc="upper left")
fig.savefig(os.path.join(FIG, "fig3_dispersao_transf_despesa.png"))
plt.close(fig)

# Fig. 4 — Espanha: saldo (B9) e dívida (%PIB) por subsetor
fig, axs = plt.subplots(1, 2, figsize=(8.2, 3.0))
lab = {"S13": "Governo geral", "S1311": "Central", "S1312": "Comunidades Autônomas", "S1313": "Entidades locais", "S1314": "Seguridade social"}
cols = {"S13": "#222", "S1311": COR["Espanha_central"], "S1312": COR["Espanha_regional"], "S1313": COR["Espanha_local"], "S1314": "#999"}
for s in ["S13", "S1311", "S1312", "S1313", "S1314"]:
    d = es[es.setor == s].set_index("ano")
    axs[0].plot(d.index, d.B9_pct_pib, color=cols[s], marker="o", ms=2.5, label=lab[s])
    axs[1].plot(d.index, d.GD_pct_pib, color=cols[s], marker="o", ms=2.5, label=lab[s])
axs[0].axhline(-3, color="#c0392b", lw=.8, ls="--"); axs[0].text(2021.2, -3.6, "referência de −3% (PEC/UE)", fontsize=7, color="#c0392b")
axs[1].axhline(60, color="#c0392b", lw=.8, ls="--"); axs[1].text(2016.1, 63, "referência de 60%", fontsize=7, color="#c0392b")
axs[0].set_title("Capacidade(+)/necessidade(−) de financiamento, % PIB", fontsize=8.5, loc="left")
axs[1].set_title("Dívida bruta (Maastricht), % PIB", fontsize=8.5, loc="left")
axs[0].legend(fontsize=6.5, loc="lower left", bbox_to_anchor=(0.0, 0.0))
fig.savefig(os.path.join(FIG, "fig4_espanha_subsetores.png"))
plt.close(fig)

# Fig. 5 — página bibliométrica (inspirada na Fig. 1 de Baker, Larcker e Wang, 2022)
ap = pd.read_csv(os.path.join(BIB, "producao_anual.csv"))
tt = pd.read_csv(os.path.join(BIB, "termos_por_ano.csv"))
ap = ap[ap.ano >= 1970]
fig, ax = plt.subplots(figsize=(7.2, 3.2))
ax.bar(ap.ano, ap.artigos, color="#9aa5b1", label="Artigos no corpus (total)")
t = tt[tt.ano >= 1970].set_index("ano")
ax.plot(t.index, t.flypaper, color=COR["Parintins"], lw=1.4, label="menciona 'flypaper'")
ax.plot(t.index, t.fiscal_illusion, color=COR["Manaus"], lw=1.4, label="menciona 'fiscal illusion'")
ax.plot(t.index, t.did, color=COR["Espanha_local"], lw=1.4, label="menciona diferenças-em-diferenças/'staggered'")
ax.set_ylabel("Nº de artigos por ano"); ax.legend(fontsize=7, loc="upper left")
fig.savefig(os.path.join(FIG, "fig5_bibliometria_producao_anual.png"))
plt.close(fig)

# ================================================================= 7. Exporta resultados resumidos (para o texto)
def r2(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)


out = dict(meta=meta, testes=testes, diagnosticos=diag,
           espanha=dict(coef=es_m.params.to_dict(), p=es_m.pvalues.to_dict(), n=int(es_m.nobs),
                        teste_TRF_igual_PIB=dict(t=float(np.ravel(es_test.tvalue)[0]), p=float(np.ravel(es_test.pvalue)[0]))),
           p1=p1)
with open(os.path.join(TAB, "resultados_resumo.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=float)
print(tid.round(4).to_string()); print(pd.DataFrame(prop).round(3))
print(json.dumps(out, ensure_ascii=False, indent=1, default=float)[:3000])
