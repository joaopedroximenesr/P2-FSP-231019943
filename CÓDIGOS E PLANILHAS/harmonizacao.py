"""
harmonizacao.py — Regras de harmonização das contas do SICONFI/DCA (P2 FSP, matrícula 231019943).

O plano de contas da receita mudou duas vezes no período:
  * até 2017: codificação da Portaria Interministerial 163/2001 (ex.: 1.7.2.1.01.02.00 = FPM);
  * 2018–2021: nova natureza de receita (Portaria Conjunta STN/SOF 650/2019 e anteriores),
    com códigos "x.x.x.8.xx" de transição (ex.: 1.7.1.8.01.2.0 = FPM cota mensal);
  * 2022 em diante: estrutura definitiva (ex.: 1.7.1.1.51.0.0 = FPM).
Por isso as rubricas detalhadas são identificadas pelo NOME da conta (expressões regulares)
e não pelo código. Para evitar dupla contagem, quando uma conta e suas subcontas casam
com a mesma regra, só a conta de nível mais alto é somada (regra "raiz").
"""
import re

COL_BRUTA = "Receitas Brutas Realizadas"
COL_DED_FUNDEB = "Deduções - FUNDEB"
COL_DED_OUTRAS = "Outras Deduções da Receita"
COL_EMPENHADA = "Despesas Empenhadas"


def norm_code(cod: str) -> str:
    """'RO1.7.2.1.01.02.00' -> '1.7.2.1.1.2' (remove prefixo e segmentos finais nulos)."""
    c = re.sub(r"^[A-Z]+", "", cod)
    if not re.fullmatch(r"[0-9.]+", c):
        return cod          # códigos não numéricos (ex.: 'TotalReceitas') ficam como estão
    segs = c.split(".")
    while segs and set(segs[-1]) <= {"0"}:
        segs.pop()
    return ".".join(str(int(s)) for s in segs) if segs else ""


def is_desc(child: str, parent: str) -> bool:
    return child != parent and child.startswith(parent + ".")


# rubricas agregadas identificadas pelo código normalizado (estáveis entre classificações)
TOP = {
    "rec_corrente": "1",
    "rec_tributaria": "1.1",          # Impostos, Taxas e Contribuições de Melhoria (antes: Receita Tributária)
    "rec_contribuicoes": "1.2",
    "rec_patrimonial": "1.3",
    "rec_servicos": "1.6",
    "transf_correntes": "1.7",
    "outras_rec_correntes": "1.9",
    "rec_capital": "2",
    "op_credito": "2.1",
    "transf_capital": "2.4",
}

# rubricas detalhadas identificadas pelo nome (regex) + prefixo de código obrigatório
DETALHE = {
    "iptu": (r"Propriedade Predial e Territorial Urbana", "1.1"),
    "iss": (r"Impostos? [Ss]obre Servi[çc]os", "1.1"),
    "itbi": (r"Transmiss[ãa]o .{0,3}Inter Vivos", "1.1"),
    "irrf": (r"Renda.{0,6}Retido|Retido nas? Fontes?", "1.1"),
    "fpm": (r"Fundo de Participa[çc][ãa]o dos Munic[íi]pios", "1.7"),
    "icms_cota": (r"Cota-Parte do ICMS", "1.7"),
    "ipva_cota": (r"Cota-Parte do IPVA", "1.7"),
    "fundeb_receb": (r"Fundo de Manuten[çc][ãa]o e Desenvolvimento da Educa[çc][ãa]o B[áa]sica|FUNDEB", "1.7"),
    "sus_corrente": (r"Sistema [ÚU]nico de Sa[úu]de|SUS|Programas de Sa[úu]de", "1.7"),
}

# DCA Anexo I-D (por natureza), coluna Despesas Empenhadas. Os agregados "DO" do SICONFI INCLUEM
# as despesas intraorçamentárias (modalidade 91, códigos "DI"); elas são subtraídas para manter
# consistência com a receita, que é tomada exceto intraorçamentária.
DESPESA_TOP = {
    "desp_corrente": ("DO3.0.00.00.00.00", r"^DI3\.\d\.91\.00\.00\.00$"),
    "desp_pessoal": ("DO3.1.00.00.00.00", r"^DI3\.1\.91\.00\.00\.00$"),
    "desp_juros": ("DO3.2.00.00.00.00", r"^DI3\.2\.91\.00\.00\.00$"),
    "desp_capital": ("DO4.0.00.00.00.00", r"^DI4\.\d\.91\.00\.00\.00$"),
    "desp_investimentos": ("DO4.4.00.00.00.00", r"^DI4\.4\.91\.00\.00\.00$"),
    "desp_amortizacao": ("DO4.6.00.00.00.00", r"^DI4\.6\.91\.00\.00\.00$"),
}

FUNCAO = {  # DCA Anexo I-E (por função), coluna Despesas Empenhadas — identificado pelo texto da conta
    "desp_total": r"^Despesas \(?Exceto Intra",
    "desp_intra": r"^Despesas \(?Intra",
    "desp_saude": r"^10 - Sa[úu]de$",
    "desp_educacao": r"^12 - Educa[çc][ãa]o$",
    "desp_administracao": r"^04 - Administra[çc][ãa]o$",
    "desp_legislativa": r"^01 - Legislativa$",
}


def soma_raiz(rows):
    """Soma valores apenas das contas 'raiz' (sem ancestral no mesmo conjunto)."""
    codes = {norm_code(r["cod_conta"]) for r in rows}
    tot, usados = 0.0, []
    vistos = set()
    for r in rows:
        c = norm_code(r["cod_conta"])
        if any(is_desc(c, p) for p in codes):
            continue
        if c in vistos:          # mesma conta repetida (ex.: rótulos diferentes) — conta uma vez
            continue
        vistos.add(c)
        tot += float(r["valor"])
        usados.append(r["cod_conta"])
    return tot, usados


def extrai_ente_ano(rows):
    """rows: registros DCA (I-C, I-D, I-E) de um ente-ano. Retorna dict de variáveis nominais (R$)
    e dict de auditoria (contas usadas). Ausência de conta => None (nunca zero)."""
    out, audit = {}, {}
    ic = [r for r in rows if r["anexo"] == "DCA-Anexo I-C"]
    idd = [r for r in rows if r["anexo"] == "DCA-Anexo I-D"]
    ie = [r for r in rows if r["anexo"] == "DCA-Anexo I-E"]
    if ic:
        def val(cod_norm, col):
            v = [float(r["valor"]) for r in ic if norm_code(r["cod_conta"]) == cod_norm and r["coluna"] == col
                 and r["cod_conta"].startswith("RO")]
            return v[0] if v else None
        tot = [r for r in ic if r["cod_conta"] == "ReceitasExcetoIntraOrcamentarias"]
        g = lambda col: next((float(r["valor"]) for r in tot if r["coluna"] == col), None)
        # total exceto intra = correntes + capital (o rótulo do total muda entre anos; recalcula-se)
        out["rec_total_bruta_declarada"] = g(COL_BRUTA)
        out["ded_fundeb_total"] = g(COL_DED_FUNDEB)
        out["ded_outras_total"] = g(COL_DED_OUTRAS)
        for k, c in TOP.items():
            out[k] = val(c, COL_BRUTA)
        out["rec_total_bruta"] = (out["rec_corrente"] + (out["rec_capital"] or 0.0)) if out["rec_corrente"] is not None else None
        # deduções (FUNDEB e outras) incidentes sobre receita corrente, tributária e transferências
        for k in ("rec_corrente", "rec_tributaria", "transf_correntes"):
            d1 = val(TOP[k], COL_DED_FUNDEB)
            d2 = val(TOP[k], COL_DED_OUTRAS)
            # o sinal das deduções varia entre declarações (alguns entes informam negativo): usa-se o módulo
            out["ded_" + k] = abs(d1 or 0.0) + abs(d2 or 0.0) if out[k] is not None else None
        for k, (rx, pref) in DETALHE.items():
            sel = [r for r in ic if r["coluna"] == COL_BRUTA and r["cod_conta"].startswith("RO")
                   and re.search(rx, r["conta"]) and norm_code(r["cod_conta"]).startswith(pref)]
            if sel:
                out[k], audit[k] = soma_raiz(sel)
            else:
                out[k], audit[k] = None, []
    if idd:
        emp = [r for r in idd if r["coluna"] == COL_EMPENHADA]
        out["desp_total_com_intra"] = next((float(r["valor"]) for r in emp if r["cod_conta"] == "TotalDespesas"), None)
        for k, (c, rx_intra) in DESPESA_TOP.items():
            v = [float(r["valor"]) for r in emp if r["cod_conta"] == c]
            intra = sum(float(r["valor"]) for r in emp if re.match(rx_intra, r["cod_conta"]))
            out[k] = (v[0] - intra) if v else None
    if ie:
        for k, rx in FUNCAO.items():
            v = [float(r["valor"]) for r in ie if re.search(rx, r["conta"].strip()) and r["coluna"] == COL_EMPENHADA]
            out[k] = v[0] if v else None
    return out, audit
