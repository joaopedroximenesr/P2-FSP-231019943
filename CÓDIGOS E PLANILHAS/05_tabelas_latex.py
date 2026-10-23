"""05_tabelas_latex.py — Gera as tabelas do artigo (08_artigo/tabelas/*.tex) a partir dos resultados."""
import os, json
import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TD, TAB, BIB = (os.path.join(ROOT, p) for p in ("03_dados_tratados", "07_resultados/tabelas", "07_resultados/bibliometria"))
OUT = os.path.join(ROOT, "08_artigo", "tabelas")
os.makedirs(OUT, exist_ok=True)


def br(x, d=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "--"
    q = Decimal(str(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return f"{q:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def stars(p):
    return "^{***}" if p < 0.01 else "^{**}" if p < 0.05 else "^{*}" if p < 0.10 else ""


f = pd.read_csv(os.path.join(TD, "painel_focos_manaus_parintins.csv"))
es = pd.read_csv(os.path.join(TD, "espanha_subsetores.csv"))
res = json.load(open(os.path.join(TAB, "resultados_resumo.json"), encoding="utf-8"))

# ---------------------------------------------------------- Tabela: série anual dos focos (valores reais per capita)
linhas = []
for mun in ["Manaus", "Parintins"]:
    d = f[f.municipio == mun].sort_values("ano")
    linhas.append(r"\multicolumn{8}{l}{\textit{" + mun + r"}}\\")
    for _, r in d.iterrows():
        if pd.isna(r.rec_corrente):
            linhas.append(f"{int(r.ano)} & \\multicolumn{{7}}{{c}}{{DCA não homologada no Siconfi (dado ausente, não imputado)}}\\\\")
            continue
        linhas.append(" & ".join([str(int(r.ano)), br(r.rec_total_liq_real_pc), br(r.rec_tributaria_real_pc),
                                  br(r.transf_total_liq_real_pc), br(r.desp_total_real_pc), br(r.resultado_orc_real / 1e6, 1),
                                  br(100 * r.dep_transf, 1), br(100 * r.autonomia_trib, 1)]) + r"\\")
tex = r"""\begin{table}[htbp]
\centering
\caption{Manaus e Parintins: receitas, despesas e indicadores fiscais, 2016--2025}
\label{tab:focos}
\footnotesize
\begin{tabular}{lrrrrrrr}
\toprule
Ano & \makecell{Receita\\total líq.\\(R\$ pc)} & \makecell{Receita\\tributária\\(R\$ pc)} & \makecell{Transf.\\líquidas\\(R\$ pc)} & \makecell{Despesa\\empenhada\\(R\$ pc)} & \makecell{Resultado\\orçam.\\(R\$ mi)} & \makecell{Depen-\\dência\\(\%)} & \makecell{Rec. trib./\\RCL\\(\%)}\\
\midrule
""" + "\n".join(linhas) + r"""
\bottomrule
\end{tabular}
\par\smallskip
\begin{minipage}{0.97\textwidth}\scriptsize
Fonte: elaboração própria com dados do Siconfi/DCA \cite{stn2025siconfi} e do IBGE \cite{ibge2026sidra}. Valores em reais de 2025 (IPCA, média anual) e per capita pela população harmonizada (Seção~\ref{sec:tratamentos}). Receita exceto intraorçamentária, líquida das deduções para o FUNDEB; despesa empenhada exceto intraorçamentária. Dependência = transferências correntes e de capital líquidas / receita total líquida.
\end{minipage}
\end{table}
"""
open(os.path.join(OUT, "tab_focos.tex"), "w", encoding="utf-8").write(tex)

# ---------------------------------------------------------- Tabela: regressões Manaus e Parintins
reg = pd.read_csv(os.path.join(TAB, "tab4_regressoes_manaus_parintins.csv"))
R = reg.set_index(["modelo", "termo"])
modelos = [("M1_niveis", "(1)", "Níveis"), ("M2_tendencia", "(2)", "Tendência"), ("M3_fpm", "(3)", "FPM"), ("M4_log", "(4)", "Log"),
           ("M5_primeiras_diferencas", "(5)", "Dif."), ("M6_pop_oficial", "(6)", "Pop. of."), ("M9_so_Manaus", "(7)", "Manaus"),
           ("M10_so_Parintins", "(8)", "Parintins"), ("M7_esforco_fiscal", "(9)", "Trib.")]
termos = [("T", "Transferências pc ($\\beta_1$)", ["transf", "ln_transf", "dtransf", "transf_o"]), ("FPM", "FPM pc", ["fpm"]),
          ("OUT", "Demais transferências pc", ["outras_transf"]), ("Y", "PIB pc ($\\beta_2$)", ["pib", "ln_pib", "dpib", "pib_o"]),
          ("D", "Parintins (efeito fixo)", ["par"]), ("TR", "Tendência linear", ["t"])]
rows = []
for _, lab, nomes in termos:
    c1, c2 = [lab], [""]
    for m, _, _ in modelos:
        hit = [n for n in nomes if (m, n) in R.index]
        if hit:
            r = R.loc[(m, hit[0])]
            c1.append(f"${br(r.coef, 3)}{stars(r.p)}$"); c2.append(f"({br(r.ep, 3)})")
        else:
            c1.append(""); c2.append("")
    rows += [" & ".join(c1) + r"\\", " & ".join(c2) + r"\\[1pt]"]
wl = ["$H_0$: $\\beta_1=\\beta_2$ ($t$)"]
for m, _, _ in modelos:
    t = res["testes"].get(m)
    wl.append(br(t["t"], 2) + (("$" + stars(t["p"]) + "$") if stars(t["p"]) else "") if t else "--")
nl = ["Observações"] + [str(res["meta"][m]["nobs"]) for m, _, _ in modelos]
r2 = ["$R^2$ ajustado"] + [br(res["meta"][m]["r2_aj"], 3) for m, _, _ in modelos]
dep = ["Var. dependente"] + ["Desp." if m not in ("M4_log", "M5_primeiras_diferencas", "M7_esforco_fiscal") else
                             {"M4_log": "ln Desp.", "M5_primeiras_diferencas": "$\\Delta$Desp.", "M7_esforco_fiscal": "Trib."}[m] for m, _, _ in modelos]
tex = r"""\begin{table}[htbp]
\centering
\caption{Manaus e Parintins: transferências, renda local e gasto per capita, 2016--2023}
\label{tab:reg}
\scriptsize
\setlength{\tabcolsep}{2.6pt}
\begin{tabular}{l""" + "c" * len(modelos) + r"""}
\toprule
 & """ + " & ".join(c for _, c, _ in modelos) + r"""\\
 & """ + " & ".join(e for _, _, e in modelos) + r"""\\
 & """ + " & ".join(dep[1:]) + r"""\\
\midrule
""" + "\n".join(rows) + r"""
\midrule
""" + " & ".join(wl) + r"""\\
""" + " & ".join(nl) + r"""\\
""" + " & ".join(r2) + r"""\\
\bottomrule
\end{tabular}
\par\smallskip
\begin{minipage}{0.98\textwidth}\scriptsize
Fonte: elaboração própria (código \texttt{03\_analise.py}). MQO com dados empilhados de Manaus e Parintins (município-ano). Variáveis em milhares de reais de 2025 per capita, exceto (4), em logaritmos, e (5), em primeiras diferenças. A coluna (6) usa a população oficial do IBGE (sem 2023); as colunas (7) e (8) estimam cada município separadamente; a coluna (9) tem a receita tributária per capita como variável dependente. Na coluna (3), o teste compara o coeficiente do FPM com o do PIB. Erros-padrão robustos HC3 entre parênteses, com distribuição $t$ de Student. A amostra termina em 2023 porque o PIB municipal ainda não foi divulgado para 2024--2025, e Parintins não tem DCA de 2016. *** $p<0{,}01$; ** $p<0{,}05$; * $p<0{,}10$.
\end{minipage}
\end{table}
"""
open(os.path.join(OUT, "tab_regressoes.tex"), "w", encoding="utf-8").write(tex)

# ---------------------------------------------------------- Tabela: Espanha por subsetor (médias e extremos)
lab = {"S13": "Governo geral", "S1311": "Administração central", "S1312": "Comunidades Autônomas", "S1313": "Entidades locais", "S1314": "Seguridade social"}
rows = []
for s in ["S13", "S1311", "S1312", "S1313", "S1314"]:
    d = es[es.setor == s].sort_values("ano")
    rows.append(" & ".join([lab[s], br(d.TR_pct_pib.mean(), 1), br(d.TE_pct_pib.mean(), 1), br(d.B9_pct_pib.iloc[0], 1),
                            br(d.B9_pct_pib.iloc[-1], 1), br(d.GD_pct_pib.iloc[0], 1), br(d.GD_pct_pib.iloc[-1], 1),
                            br(100 * d.dep_transf.mean(), 1), br(100 * d.autonomia_trib.mean(), 1)]) + r"\\")
tex = r"""\begin{table}[htbp]
\centering
\caption{Espanha: indicadores fiscais por subsetor das administrações públicas, 2016--2025}
\label{tab:espanha}
\scriptsize
\begin{tabular}{lrrrrrrrr}
\toprule
 & \makecell{Receita\\\% PIB\\(média)} & \makecell{Despesa\\\% PIB\\(média)} & \makecell{Saldo\\\% PIB\\2016} & \makecell{Saldo\\\% PIB\\2025} & \makecell{Dívida\\\% PIB\\2016} & \makecell{Dívida\\\% PIB\\2025} & \makecell{Transf.\\recebidas/\\receita (\%)} & \makecell{Impostos\\próprios/\\receita (\%)}\\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\par\smallskip
\begin{minipage}{0.97\textwidth}\scriptsize
Fonte: elaboração própria com dados do Eurostat \cite{eurostat2026gov} (\texttt{gov\_10a\_main}, \texttt{gov\_10dd\_edpt1}, \texttt{nama\_10\_gdp}). Subsetores não consolidados entre si; transferências recebidas = D.7 + D.9 (inclui transferências intragovernamentais D.73 e D.92); impostos próprios = D.2 + D.5 + D.91, segundo o SEC 2010, que registra como receita regional a parcela cedida do IRPF e do IVA. Saldo = capacidade (+) ou necessidade ($-$) de financiamento (B.9).
\end{minipage}
\end{table}
"""
open(os.path.join(OUT, "tab_espanha.tex"), "w", encoding="utf-8").write(tex)

# ---------------------------------------------------------- Tabela: principais informações bibliométricas
txt = open(os.path.join(BIB, "summary_bibliometrix.txt"), encoding="utf-8").read()
import re
def grab(lbl):
    m = re.search(lbl + r"\s+([\d.]+)", txt)
    return m.group(1).replace(".", ",") if m else "--"
fon = pd.read_csv(os.path.join(BIB, "top_fontes.csv")).head(5)
pai = pd.read_csv(os.path.join(BIB, "top_paises.csv")).head(6)
kw = pd.read_csv(os.path.join(BIB, "top_palavras.csv")).head(8)
PT = {"INDONESIA": "Indonésia", "USA": "Estados Unidos", "UKRAINE": "Ucrânia", "CHINA": "China", "BRAZIL": "Brasil",
      "UNITED KINDOM": "Reino Unido", "UNITED KINGDOM": "Reino Unido", "CANADA": "Canadá", "GERMANY": "Alemanha", "SPAIN": "Espanha", "INDIA": "Índia", "ITALY": "Itália", "JAPAN": "Japão"}
def tt(s):
    s = s.title().replace("&Amp", "\\&").replace(" Of ", " of ").replace(" And ", " and ").replace(" The ", " the ")
    return s.replace("Publius the Journal", "Publius: the Journal")
info = [("Período coberto", "1952--2025"), ("Documentos (artigos em periódicos)", grab("Documents")), ("Periódicos", grab(r"Sources \(Journals, Books, etc\)")),
        ("Autores", grab(r"Authors ")), (r"Taxa de crescimento anual (\%)", grab(r"Annual Growth Rate %")), ("Citações médias por documento", grab(r"Average citations per doc")),
        ("Coautores por documento", grab(r"Co-Authors per Doc")), (r"Coautoria internacional (\%)", grab(r"International co-authorships %"))]
left = [f"{a} & {b}\\\\" for a, b in info]
fl = [f"{tt(r["item"])} & {r["n"]}\\\\" for _, r in fon.iterrows()]
pl = [f"{PT.get(r["item"], r["item"].title())} & {r["n"]}\\\\" for _, r in pai.iterrows()]
kl = [f"{r["item"].lower()} & {r["n"]}\\\\" for _, r in kw.iterrows()]
tex = r"""\begin{table}[htbp]
\centering
\caption{Estudo bibliométrico: informações principais do corpus (\textit{bibliometrix})}
\label{tab:biblio}
\scriptsize
\begin{tabular}{@{}p{0.47\textwidth}@{\hspace{0.04\textwidth}}p{0.47\textwidth}@{}}
\begin{tabular}[t]{lr}
\toprule
\multicolumn{2}{l}{\textit{(a) Informações gerais}}\\
\midrule
""" + "\n".join(left) + r"""
\midrule
\multicolumn{2}{l}{\textit{(b) Periódicos mais produtivos}}\\
\midrule
""" + "\n".join(fl) + r"""
\bottomrule
\end{tabular}
&
\begin{tabular}[t]{lr}
\toprule
\multicolumn{2}{l}{\textit{(c) Países (afiliação dos autores, ocorrências)}}\\
\midrule
""" + "\n".join(pl) + r"""
\midrule
\multicolumn{2}{l}{\textit{(d) Palavras-chave mais frequentes}}\\
\midrule
""" + "\n".join(kl) + r"""
\bottomrule
\end{tabular}
\end{tabular}
\par\smallskip
\begin{minipage}{0.97\textwidth}\scriptsize
Fonte: elaboração própria com o pacote \textit{bibliometrix} \cite{aria2017} aplicado a registros do OpenAlex \cite{openalex2026} (consultas em título e resumo em inglês, português e espanhol, descritas na nota da Tabela~\ref{tab:baker}; apenas artigos com autoria e fonte primária classificada como periódico). Código: \texttt{05\_bibliometria.R}.
\end{minipage}
\end{table}
"""
open(os.path.join(OUT, "tab_biblio.tex"), "w", encoding="utf-8").write(tex)
print("tabelas ok")

# ---------------------------------------------------------- Tabela 1 no formato de Baker, Larcker e Wang (2022)
t1 = pd.read_csv(os.path.join(BIB, "tabela1_baker_periodicos.csv"))
st = pd.read_csv(os.path.join(BIB, "tabela1_baker_subtotais.csv")).set_index("grupo")
NOME = {"PUBLIC FINANCE REVIEW": "Public Finance Review", "INTERNATIONAL TAX AND PUBLIC FINANCE": "International Tax and Public Finance",
        "PUBLIC CHOICE": "Public Choice", "JOURNAL OF PUBLIC ECONOMICS": "Journal of Public Economics", "NATIONAL TAX JOURNAL": "National Tax Journal",
        "PUBLIC BUDGETING &AMP FINANCE": "Public Budgeting \\& Finance", "PUBLIUS THE JOURNAL OF FEDERALISM": "Publius: The Journal of Federalism",
        "LOCAL GOVERNMENT STUDIES": "Local Government Studies", "PUBLIC FINANCE AND MANAGEMENT": "Public Finance and Management",
        "STATE AND LOCAL GOVERNMENT REVIEW": "State and Local Government Review", "ECONOMIA APLICADA": "Economia Aplicada",
        "REVISTA DE ADMINISTRAÇÃO PÚBLICA": "Revista de Administração Pública", "REVISTA ECONÔMICA DO NORDESTE": "Revista Econômica do Nordeste",
        "ADMINISTRAÇÃO PÚBLICA E GESTÃO SOCIAL": "Administração Pública e Gestão Social", "ESTUDOS ECONÔMICOS (SÃO PAULO)": "Estudos Econômicos"}
ROT = {"Finanças públicas e escolha pública": "Finanças públicas e escolha pública", "Federalismo, orçamento e governo local": "Federalismo, orçamento e governo local",
       "Periódicos brasileiros": "Periódicos brasileiros"}
corpo = []
for g in ["Finanças públicas e escolha pública", "Federalismo, orçamento e governo local", "Periódicos brasileiros"]:
    for _, r in t1[t1.grupo == g].iterrows():
        corpo.append(f"\\textit{{{NOME.get(r['periodico'], r['periodico'].title())}}} & {int(r['transferencias'])} & {int(r['flypaper_ilusao'])} & {br(r['pct'], 1)}\\%\\\\")
    s = st.loc[g]
    corpo.append(f"\\textbf{{{ROT[g]}}} & \\textbf{{{int(s.transferencias)}}} & \\textbf{{{int(s.flypaper_ilusao)}}} & \\textbf{{{br(s.pct, 1)}\\%}}\\\\")
    corpo.append("\\midrule")
s = st.loc["Total dos 15 periódicos"]; c = st.loc["Corpus completo (todos os periódicos)"]
corpo.append(f"\\textbf{{Total dos 15 periódicos}} & \\textbf{{{int(s.transferencias)}}} & \\textbf{{{int(s.flypaper_ilusao)}}} & \\textbf{{{br(s.pct, 1)}\\%}}\\\\")
corpo.append(f"Corpus completo (todos os periódicos) & {br(c.transferencias, 0)} & {br(c.flypaper_ilusao, 0)} & {br(c.pct, 1)}\\%\\\\")
tex = r"""\begin{table}[htbp]
\centering
\caption{Artigos sobre transferências intergovernamentais e sobre efeito \textit{flypaper} ou ilusão fiscal, por periódico: 2000--2025}
\label{tab:baker}
\small
\begin{tabular}{lccc}
\toprule
 & (1) & (2) & (3)\\
 & Transferências & \textit{Flypaper}/ilusão fiscal & (2)/(1) (\%)\\
\midrule
""" + "\n".join(corpo) + r"""
\bottomrule
\end{tabular}
\par\smallskip
\begin{minipage}{0.97\textwidth}\scriptsize
Nota: a Tabela~\ref{tab:baker} segue o formato da Tabela 1 de \citeonline{baker2022}. Resume o número de artigos publicados entre 2000 e 2025 em cinco periódicos de finanças públicas e escolha pública, cinco periódicos de federalismo, orçamento e governo local (os mais produtivos do corpus em cada grupo) e cinco periódicos editados no Brasil. O corpus foi obtido no OpenAlex com busca em título e resumo pelos termos ``intergovernmental transfers'', ``intergovernmental grants'', ``flypaper effect'' e ``fiscal illusion'' e pelos equivalentes em português e espanhol (``transferências intergovernamentais'', ``transferências constitucionais'', ``efeito flypaper'', ``ilusão fiscal'', ``transferencias intergubernamentales'', ``ilusión fiscal''), mantendo apenas artigos com autoria identificada e fonte primária classificada como periódico. A coluna (1) informa o total de artigos do corpus em cada periódico; a coluna (2), quantos deles tratam do efeito \textit{flypaper} ou da ilusão fiscal (termo presente no título, no resumo ou nas palavras-chave); a coluna (3), a participação de (2) em (1). Contagens produzidas com o pacote \textit{bibliometrix} \cite{aria2017} (\texttt{06\_codigos\_e\_planilhas/05\_bibliometria.R}).
\end{minipage}
\end{table}
"""
open(os.path.join(OUT, "tab_baker.tex"), "w", encoding="utf-8").write(tex)
print("tab_baker ok")
