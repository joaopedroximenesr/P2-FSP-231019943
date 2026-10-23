"""07_comparacao_p1.py — Compara os valores da Espanha da base original (P1) com a base atualizada (Eurostat).
Saída: 05_registro_alteracoes/comparacao_P1_P2_espanha.csv"""
import os, openpyxl, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wb = openpyxl.load_workbook(os.path.join(ROOT, "01_base_original/P1_231020069_CAUA_VICTOR/DOCS DE RESOLUÇÃO DA PROVA/P1 FSP (2).xlsx"), data_only=True)
ws = wb["ESPANHA"]
rows = list(ws.iter_rows(values_only=True))
p1 = pd.DataFrame(rows[1:], columns=rows[0]).dropna(subset=["ANO"])
es = pd.read_csv(os.path.join(ROOT, "03_dados_tratados/espanha_subsetores.csv"))
g = es[es.setor == "S13"].set_index("ano")
pares = [("RECEITAS CORRENTES", "TR", 1e6, "Receita total (TR)"), ("DESPESA TOTAL", "TE", 1e6, "Despesa total (TE)"),
         ("DIVIDA BRUTA", "GD", 1e6, "Dívida bruta de Maastricht (GD)"), ("EQUILIBRIO ESTRUTURAL", "B9", 1e6, "Saldo efetivo B.9 (P1 rotulava 'equilíbrio estrutural')"),
         ("PIB", "PIB_MIO_EUR", 1e6, "PIB a preços correntes"), ("POPULAÇÃO", "pop_1jan", 1, "População (P1: FMI, média; P2: Eurostat, 1.º jan.)")]
out = []
for _, r in p1.iterrows():
    a = int(r["ANO"])
    if a not in g.index:
        continue
    for c1, c2, esc, lab in pares:
        v1, v2 = float(r[c1]), float(g.loc[a, c2]) * esc
        out.append(dict(ano=a, variavel=lab, valor_P1=v1, valor_P2_eurostat=v2, diferenca=v2 - v1, diferenca_pct=100 * (v2 / v1 - 1) if v1 else None))
df = pd.DataFrame(out)
df.to_csv(os.path.join(ROOT, "05_registro_alteracoes/comparacao_P1_P2_espanha.csv"), index=False)
print(df.groupby("variavel").diferenca_pct.agg(["min", "max"]).round(2))
