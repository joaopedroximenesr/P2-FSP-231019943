"""Gera refs.bib a partir dos metadados verificados no OpenAlex (refs/refs_meta.json) + documentos oficiais."""
import json, re, os, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
meta = json.load(open(os.path.join(HERE, "refs", "refs_meta.json"), encoding="utf-8"))

# nomes com sobrenome composto/partículas ou grafia incorreta no OpenAlex -> "Sobrenome, Prenomes"
OVR = {
    "Barry R.VE Weingast": "Weingast, Barry R.", "Richard Miller Bird": "Bird, Richard M.", "Ernesto Hugo Stein": "Stein, Ernesto H.",
    "STEPHEN JAMES BAILEY": "Bailey, Stephen J.", "Albert Solé‐Ollé": "Solé-Ollé, Albert", "Pilar Sorribas‐Navarro": "Sorribas-Navarro, Pilar",
    "Núria Vergés Bosch": "Bosch, Núria", "Santiago Lago Peñas": "Lago-Peñas, Santiago", "Julio López Laborda": "López-Laborda, Julio",
    "Alberto Vaquero García": "Vaquero-García, Alberto", "Juan González Alegre": "González-Alegre, Juan", "Miriam Hortas‐Rico": "Hortas-Rico, Miriam",
    "Vicente Orts Ríos": "Ríos, Vicente", "María‐Dolores Guillamón": "Guillamón, María-Dolores", "Fernando Andrés Blanco Cossío": "Cossío, Fernando Andrés Blanco",
    "Leonardo Mello de Carvalho": "Carvalho, Leonardo Mello de", "Luiz Carlos Bresser‐Pereira": "Bresser-Pereira, Luiz Carlos", "Luiz R. de Mello": "Mello, Luiz R. de",
    "Paulo Aguiar do Monte": "Monte, Paulo Aguiar do", "Ronaldo José Rêgo de Araújo": "Araújo, Ronaldo José Rêgo de", "Clément de Chaisemartin": "de Chaisemartin, Clément",
    "Irineu de Carvalho Filho": "Carvalho Filho, Irineu de", "Stephan Litschig Y": "Litschig, Stephan", "Jürgen von Hagen": "von Hagen, Jürgen",
    "Friedrich Georg SCHNEIDER": "Schneider, Friedrich", "CLÁUDIO BENITO OLIVEIRA FERRAZ": "Ferraz, Claudio", "Eva Britt Johansson": "Johansson, Eva",
    "Paulo Reis Mourão": "Mourão, Paulo Reis", "Cleomar Gomes da Silva": "Silva, Cleomar Gomes da", "Luciana Dias de Lima": "Lima, Luciana Dias de",
    "Carla Lourenço Tavares de Andrade": "Andrade, Carla Lourenço Tavares de", "Joel de Jesus Macedo": "Macedo, Joel de Jesus",
    "Glenda Santos de Almeida Borges": "Borges, Glenda Santos de Almeida", "Jevuks Matheus de Araújo": "Araújo, Jevuks Matheus de",
    "Dimas Barrêto de Queiroz": "Queiroz, Dimas Barrêto de", "Ely do Carmo Oliveira Gomes": "Gomes, Ely do Carmo Oliveira",
    "Kleber Morais de Sousa": "Sousa, Kleber Morais de", "Jean‐Robert Tyran": "Tyran, Jean-Robert", "Jens Blom‐Hansen": "Blom-Hansen, Jens",
    "Xavier D’Haultfœuille": "D'Haultfœuille, Xavier", "Pedro H. C. Sant’Anna": "Sant'Anna, Pedro H. C.", "Roberto Dell’Anno": "Dell'Anno, Roberto",
    "Jorge Martínez-Vázquez": "Martínez-Vázquez, Jorge", "Alexandre Manoel Angelo da Silva": "Silva, Alexandre Manoel Angelo da",
    "Rozane Bezerra de Siqueira": "Siqueira, Rozane Bezerra de", "Edílson Paulo": "Paulo, Edílson", "Carla Janaína Ferreira Nobre": "Nobre, Carla Janaína Ferreira",
    "Andre Guimaraes Resende Martins do Valle": "Valle, André G. R. M. do",
}
PARTICULAS = {"de", "da", "do", "dos", "das", "von", "van", "del"}


def nome(n):
    n = n.strip()
    if n in OVR:
        return OVR[n]
    n = n.replace("‐", "-")
    t = n.split()
    if len(t) == 1:
        return t[0]
    sobren = t[-1]
    if sobren.isupper() and len(sobren) > 2:
        sobren = sobren.title()
    prenomes = " ".join(x.title() if x.isupper() and len(x) > 2 else x for x in t[:-1])
    return f"{sobren}, {prenomes}"


def chave(r):
    s = nome(r["authors"][0]).split(",")[0]
    s = s.replace("æ", "ae").replace("Æ", "Ae").replace("ø", "o")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z]", "", s).lower()
    return f"{s}{r['year']}"


def esc(s):
    return (s or "").replace("&amp;", "\\&").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


JOURNAL_FIX = {"Staff Papers": "IMF Staff Papers", "Public Budgeting &amp Finance": "Public Budgeting & Finance",
               "Pesquisa e planejamento economico (Rio de Janeiro)": "Pesquisa e Planejamento Econômico",
               "IRIS Research product catalog (Sapienza University of Rome)": "Journal of Public Economics",
               "RePEc: Research Papers in Economics": "Planejamento e Políticas Públicas",
               "CADERNOS DE FINANÇAS PÚBLICAS": "Cadernos de Finanças Públicas",
               "Papers of the Regional Science Association": "Papers in Regional Science",
               "Contabilidade, Gestão e Governança/UNB Contábil": "Contabilidade, Gestão e Governança",
               "The Journal of developing areas": "The Journal of Developing Areas",
               "Canadian Journal of Economics/Revue canadienne d économique": "Canadian Journal of Economics",
               "American Economic Journal Applied Economics": "American Economic Journal: Applied Economics",
               "American Economic Journal Economic Policy": "American Economic Journal: Economic Policy",
               "Publius The Journal of Federalism": "Publius: The Journal of Federalism"}
# correções pontuais: ano/volume da edição impressa (OpenAlex registra a data de publicação online)
FIX = {
    "10.1016/j.jpubeco.2014.11.007": dict(year=2015, vol="123", issue="", fp="78", lp="91"),
    "10.1016/j.jeconom.2020.12.001": dict(year=2021, vol="225", issue="2", fp="200", lp="230"),
    "10.1016/j.jpubeco.2007.06.014": dict(year=2008),
    "10.1007/s10797-013-9269-9": dict(year=2014),
    "10.1007/s10797-010-9160-x": dict(year=2011),
    "10.1016/j.jpubeco.2007.05.004": dict(year=2008),
    "10.1080/03003930.2014.968708": dict(year=2015),
    "10.1016/j.jpubeco.2005.09.002": dict(year=2006),
    "10.1007/s00181-013-0701-x": dict(year=2014),
    "10.1177/1091142111425226": dict(year=2012),
    "10.1016/j.jue.2008.12.005": dict(year=2009),
    "10.1080/00343404.2017.1287891": dict(year=2018),
    "10.3368/jhr.57.3.0917-9064r2": dict(year=2022),
    "10.21874/rsp.v47i1.702": dict(year=1996),
    "10.1016/j.jfineco.2022.01.004": dict(vol="144", issue="2", fp="370", lp="395"),
    "10.1257/aer.20181169": dict(vol="110", issue="9", fp="2964", lp="2996"),
    "10.1016/j.jeconom.2021.03.014": dict(vol="225", issue="2", fp="254", lp="277"),
    "10.1016/j.joi.2017.08.007": dict(vol="11", issue="4", fp="959", lp="975"),
}

entries, keys, catalogo = [], {}, []
for r in meta:
    if r["title"] and r["title"].startswith("Demanda por Gasto Público"):
        r = dict(r, year=2015, title="Demanda por gasto público no Brasil no período pós-redemocratização: testes da hipótese de Mill de ilusão fiscal e da lei de Wagner",
                 authors=["Alexandre Manoel Angelo da Silva", "Rozane Bezerra de Siqueira"], journal="Planejamento e Políticas Públicas", issue="43", vol=None, fp=None, lp=None, doi="")
    f = FIX.get(r["doi"], {})
    r = dict(r)
    for k, v in f.items():
        r[k] = v
    k = chave(r)
    if k in keys:
        k = k + "b" if k + "b" not in keys else k + "c"
    keys[k] = r
    jr = JOURNAL_FIX.get(r["journal"], r["journal"])
    jr = re.sub(r"\s+", " ", jr or "")
    title = esc(r["title"]).replace("  ", " ")
    title = re.sub(r"^(M) exican", r"Mexican", title)
    if sum(c.isupper() for c in title) > 0.6 * sum(c.isalpha() for c in title):
        title = title.lower().capitalize()
        for w in ["brazilian", "brazil", "australian", "flemish", "south african", "mill", "ricardian", "uk", "us"]:
            title = re.sub(r"\b" + w + r"\b", w.title() if w not in ("uk", "us") else w.upper(), title)
    autores = " and ".join(nome(a) for a in r["authors"])
    pages = f"{r['fp']}--{r['lp']}" if r.get("fp") and r.get("lp") else (r.get("fp") or "")
    e = [f"@article{{{k},", f"  author = {{{autores}}},", f"  title = {{{{{title}}}}},", f"  journal = {{{esc(jr)}}},", f"  year = {{{r['year']}}},"]
    if r.get("vol"): e.append(f"  volume = {{{r['vol']}}},")
    if r.get("issue"): e.append(f"  number = {{{r['issue']}}},")
    if pages: e.append(f"  pages = {{{pages}}},")
    if r.get("doi"): e.append(f"  doi = {{{r['doi']}}},")
    e.append(f"  note = {{OpenAlex: {r['id'].split('/')[-1]}}}")
    e.append("}")
    entries.append("\n".join(e))
    catalogo.append(dict(chave=k, ano=r["year"], autores="; ".join(nome(a) for a in r["authors"]), titulo=r["title"], periodico=jr, doi=r.get("doi"), openalex=r["id"]))

OFICIAIS = r"""
@misc{ferreira2021tese,
  author = {Ferreira, Lucas Oliveira Gomes},
  title = {Constitutional tax transfer in {Brazilian} municipalities: the fiscal illusion and the flypaper effect},
  howpublished = {Tese (Doutorado) -- Universidade de Brasília},
  year = {2021},
  note = {Referência de partida indicada pelo professor; não integra a contagem de artigos}
}
@misc{caua2026p1,
  author = {Victor, Cauã},
  title = {Prova {P1} de Finanças do Setor Público -- matrícula 231020069 ({Espanha}, {Maceió/AL} e {Duque de Caxias/RJ})},
  howpublished = {Repositório GitHub: \url{https://github.com/cauaviictor/P1---FSP---231020069---CAUA-VICTOR}, commit 5209bcec},
  year = {2026},
  note = {Trabalho anterior atribuído; base original preservada em 01\_base\_original}
}
@misc{brasil2000lrf,
  author = {{BRASIL}},
  title = {Lei Complementar n.º 101, de 4 de maio de 2000 ({Lei de Responsabilidade Fiscal})},
  howpublished = {\url{https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp101.htm}},
  year = {2000}
}
@misc{brasil1988cf,
  author = {{BRASIL}},
  title = {Constituição da República Federativa do Brasil de 1988},
  howpublished = {\url{https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm}},
  year = {1988}
}
@misc{brasil1995pdrae,
  author = {{BRASIL. Presidência da República. Câmara da Reforma do Estado}},
  title = {Plano Diretor da Reforma do Aparelho do Estado},
  howpublished = {Brasília: Presidência da República},
  year = {1995}
}
@misc{brasil2020fundeb,
  author = {{BRASIL}},
  title = {Lei n.º 14.113, de 25 de dezembro de 2020 (regulamenta o {FUNDEB} permanente)},
  howpublished = {\url{https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l14113.htm}},
  year = {2020}
}
@misc{brasil2023ec132,
  author = {{BRASIL}},
  title = {Emenda Constitucional n.º 132, de 20 de dezembro de 2023 (Reforma Tributária)},
  howpublished = {\url{https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm}},
  year = {2023}
}
@misc{stn2025siconfi,
  author = {{SECRETARIA DO TESOURO NACIONAL}},
  title = {{API} de Dados Abertos do {SICONFI} -- Declaração de Contas Anuais ({DCA}), Anexos {I-C}, {I-D} e {I-E}},
  howpublished = {\url{https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca}. Acesso em: 21 out. 2026},
  year = {2026}
}
@misc{stn2024mcasp,
  author = {{SECRETARIA DO TESOURO NACIONAL}},
  title = {Manual de Contabilidade Aplicada ao Setor Público ({MCASP}), 10.ª edição},
  howpublished = {Brasília: STN},
  year = {2023}
}
@misc{ibge2026sidra,
  author = {{INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA}},
  title = {Sistema {IBGE} de Recuperação Automática ({SIDRA}): tabelas 1737 ({IPCA}), 6579 (estimativas de população), 4714 e 1378 (Censos 2022 e 2010) e 5938 ({PIB} dos municípios)},
  howpublished = {\url{https://servicodados.ibge.gov.br/api/v3/agregados}. Acesso em: 21 out. 2026},
  year = {2026}
}
@misc{eurostat2026gov,
  author = {{EUROSTAT}},
  title = {Government revenue, expenditure and main aggregates (gov\_10a\_main); Government deficit/surplus, debt ({EDP} notification) (gov\_10dd\_edpt1); {HICP} (prc\_hicp\_aind); {GDP} (nama\_10\_gdp); Population (demo\_pjan)},
  howpublished = {\url{https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/}. Acesso em: 21 out. 2026},
  year = {2026}
}
@misc{espana1978ce,
  author = {{ESPAÑA}},
  title = {Constitución Española de 1978},
  howpublished = {\url{https://www.boe.es/eli/es/c/1978/12/27/(1)/con}},
  year = {1978}
}
@misc{espana2012loepsf,
  author = {{ESPAÑA}},
  title = {Ley Orgánica 2/2012, de 27 de abril, de Estabilidad Presupuestaria y Sostenibilidad Financiera},
  howpublished = {\url{https://www.boe.es/eli/es/lo/2012/04/27/2/con}},
  year = {2012}
}
@misc{espana2009financiacion,
  author = {{ESPAÑA}},
  title = {Ley 22/2009, de 18 de diciembre, por la que se regula el sistema de financiación de las Comunidades Autónomas de régimen común},
  howpublished = {\url{https://www.boe.es/eli/es/l/2009/12/18/22/con}},
  year = {2009}
}
@misc{espana2004trlrhl,
  author = {{ESPAÑA}},
  title = {Real Decreto Legislativo 2/2004, de 5 de marzo, Texto Refundido de la Ley Reguladora de las Haciendas Locales},
  howpublished = {\url{https://www.boe.es/eli/es/rdlg/2004/03/05/2/con}},
  year = {2004}
}
@misc{openalex2026,
  author = {{OPENALEX}},
  title = {{OpenAlex API} -- consulta bibliográfica (\textit{works})},
  howpublished = {\url{https://api.openalex.org}. Acesso em: 21 out. 2026},
  year = {2026}
}
@misc{ue2024governance,
  author = {{UNIÃO EUROPEIA}},
  title = {Regulamento ({UE}) 2024/1263 relativo à coordenação eficaz das políticas económicas e à supervisão orçamental multilateral},
  howpublished = {Jornal Oficial da União Europeia, L 2024/1263},
  year = {2024}
}
"""
with open(os.path.join(HERE, "refs.bib"), "w", encoding="utf-8") as f:
    f.write("% Artigos científicos verificados no OpenAlex (metadados em refs/refs_meta.json)\n\n")
    f.write("\n\n".join(entries))
    f.write("\n\n% Documentos oficiais, bases e trabalhos não contabilizados entre os 80 artigos\n")
    f.write(OFICIAIS)
json.dump(catalogo, open(os.path.join(HERE, "refs", "catalogo_artigos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(entries), "artigos;", "chaves:")
print(" ".join(sorted(keys)))
