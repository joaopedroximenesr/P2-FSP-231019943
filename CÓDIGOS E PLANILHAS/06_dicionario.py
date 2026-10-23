"""06_dicionario.py — Gera o dicionário de variáveis (04_dicionario_variaveis/)."""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIC = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
IB = "https://servicodados.ibge.gov.br/api/v3/agregados"
EU = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
AUS = "Ausente permanece vazio (NA); nunca substituído por zero"
P_F = "2016–2025 (Parintins: 2017–2025, sem DCA de 2016 no Siconfi)"

V = [
    # nome, definição, fonte, url, período, cobertura, unidade, ausentes, transformação
    ("cod_ibge", "Código IBGE do município (7 dígitos)", "IBGE/Siconfi", SIC, "—", "Manaus e Parintins", "código", "—", "—"),
    ("ano", "Exercício financeiro", "—", "—", "2016–2025", "—", "ano", "—", "—"),
    ("rec_corrente", "Receita corrente bruta, exceto intraorçamentária (conta 1.0.0.0)", "STN/Siconfi, DCA Anexo I-C, coluna 'Receitas Brutas Realizadas'", SIC, P_F, "Manaus e Parintins", "R$ correntes", AUS, "Leitura direta; código normalizado para comparar as três classificações"),
    ("rec_capital", "Receita de capital bruta (conta 2.0.0.0)", "STN/Siconfi, DCA I-C", SIC, P_F, "idem", "R$ correntes", AUS + "; na soma da receita total, ausência de receita de capital é tratada como inexistência de lançamento", "Leitura direta"),
    ("ded_rec_corrente", "Deduções da receita corrente (FUNDEB + outras deduções)", "STN/Siconfi, DCA I-C, colunas 'Deduções - FUNDEB' e 'Outras Deduções da Receita'", SIC, P_F, "idem", "R$ correntes", AUS, "Soma dos módulos (alguns entes informam sinal negativo)"),
    ("rec_total_liq", "Receita total líquida exceto intraorçamentária", "Calculada", "—", P_F, "idem", "R$ correntes", AUS, "rec_corrente − ded_rec_corrente + rec_capital"),
    ("rec_tributaria", "Impostos, taxas e contribuições de melhoria (conta 1.1; antes de 2018 'Receita Tributária')", "STN/Siconfi, DCA I-C", SIC, P_F, "idem", "R$ correntes", AUS, "Leitura direta (bruta)"),
    ("iptu, iss, itbi, irrf", "Impostos municipais e IRRF", "STN/Siconfi, DCA I-C", SIC, P_F, "Manaus e Parintins", "R$ correntes", AUS, "Identificação pelo nome da conta; soma só das contas-raiz (06_codigos_e_planilhas/harmonizacao.py)"),
    ("transf_correntes", "Transferências correntes brutas (conta 1.7)", "STN/Siconfi, DCA I-C", SIC, P_F, "idem", "R$ correntes", AUS, "Leitura direta"),
    ("ded_transf_correntes", "Deduções sobre transferências correntes (principalmente FUNDEB)", "STN/Siconfi, DCA I-C", SIC, P_F, "idem", "R$ correntes", AUS, "Soma dos módulos"),
    ("transf_capital", "Transferências de capital (conta 2.4)", "STN/Siconfi, DCA I-C", SIC, P_F, "idem", "R$ correntes", "Ausência tratada como zero apenas na soma de transf_total_liq, pois indica inexistência de lançamento na DCA entregue", "Leitura direta"),
    ("transf_correntes_liq", "Transferências correntes líquidas", "Calculada", "—", P_F, "idem", "R$ correntes", AUS, "transf_correntes − ded_transf_correntes"),
    ("transf_total_liq", "Transferências intergovernamentais líquidas (correntes + capital)", "Calculada", "—", P_F, "idem", "R$ correntes", AUS, "transf_correntes_liq + transf_capital"),
    ("fpm", "Cota-parte do Fundo de Participação dos Municípios (inclui cotas de 1%)", "STN/Siconfi, DCA I-C", SIC, P_F, "Manaus e Parintins", "R$ correntes", AUS, "Nome da conta: 1.7.2.1.01.02 (até 2017), 1.7.1.8.01.2/.4 (2018–21), 1.7.1.1.51 (2022–25)"),
    ("icms_cota", "Cota-parte do ICMS", "STN/Siconfi, DCA I-C", SIC, P_F, "idem", "R$ correntes", AUS, "Nome da conta: 1.7.2.2.01.01 / 1.7.2.8.01.1 / 1.7.2.1.50"),
    ("ipva_cota", "Cota-parte do IPVA", "STN/Siconfi, DCA I-C", SIC, P_F, "Manaus e Parintins", "R$ correntes", AUS, "Nome da conta"),
    ("fundeb_receb", "Transferências recebidas do FUNDEB (inclui complementação da União)", "STN/Siconfi, DCA I-C", SIC, P_F, "idem", "R$ correntes", AUS, "Nome da conta"),
    ("sus_corrente", "Transferências correntes do SUS (União e estado)", "STN/Siconfi, DCA I-C", SIC, P_F, "idem", "R$ correntes", AUS, "Nome da conta"),
    ("arrec_propria", "Receita corrente própria", "Calculada", "—", P_F, "idem", "R$ correntes", AUS, "rec_corrente − transf_correntes"),
    ("desp_total", "Despesa empenhada exceto intraorçamentária", "STN/Siconfi, DCA Anexo I-E, linha 'Despesas Exceto Intraorçamentárias'", SIC, P_F, "idem", "R$ correntes", AUS + "; se a linha não existir, usa-se o total com intra e sinaliza-se desp_total_inclui_intra", "Leitura direta"),
    ("desp_corrente, desp_pessoal, desp_capital, desp_investimentos, desp_juros, desp_amortizacao", "Despesa empenhada por natureza, exceto intraorçamentária", "STN/Siconfi, DCA Anexo I-D", SIC, P_F, "idem", "R$ correntes", AUS, "Agregado 'DO' menos as linhas 'DI' (modalidade 91) correspondentes"),
    ("desp_saude, desp_educacao", "Despesa empenhada nas funções 10 (Saúde) e 12 (Educação)", "STN/Siconfi, DCA Anexo I-E", SIC, P_F, "idem", "R$ correntes", AUS, "Leitura direta"),
    ("resultado_orc", "Resultado orçamentário", "Calculada", "—", P_F, "idem", "R$ correntes", AUS, "rec_total_liq − desp_total"),
    ("dep_transf", "Grau de dependência de transferências", "Calculada", "—", P_F, "idem", "proporção (0–1)", AUS, "transf_total_liq / rec_total_liq"),
    ("autonomia_trib", "Autonomia tributária", "Calculada", "—", P_F, "idem", "proporção (0–1)", AUS, "rec_tributaria / (rec_corrente − ded_rec_corrente)"),
    ("pib", "PIB municipal a preços correntes", "IBGE, Sidra tab. 5938, variável 37", IB + "/5938", "2016–2023", "Manaus e Parintins", "R$ correntes (fonte em mil R$)", "2024–2025 ainda não divulgados: ausentes", "× 1.000"),
    ("pop_oficial", "População oficial", "IBGE, tab. 6579 (estimativas) e 4714 (Censo 2022)", IB + "/6579", "2016–2025 (2023 sem publicação)", "Manaus e Parintins", "habitantes", "2023 ausente", "Leitura direta"),
    ("pop_harmonizada", "População compatível com os Censos 2010 e 2022", "IBGE, tab. 1378, 4714 e 6579", IB, "2016–2025", "Manaus e Parintins", "habitantes", "Sem ausências", "2016–21: P10·(P22/P10)^((t+0,5−2010,58)/12); 2022: Censo; 2023: interpolação Censo 2022–estimativa 2024; 2024–25: estimativas"),
    ("fator_ipca", "Fator de conversão para R$ de 2025", "IBGE, Sidra tab. 1737, variável 2266 (número-índice)", IB + "/1737", "2015–2025", "Brasil", "adimensional", "—", "F_t = média(I_2025)/média(I_t), médias dos 12 meses"),
    ("<var>_real", "Variável monetária em R$ de 2025", "Calculada", "—", "idem à variável", "idem", "R$ de 2025", AUS, "<var> × fator_ipca"),
    ("<var>_real_pc", "Variável monetária real per capita", "Calculada", "—", "idem", "idem", "R$ de 2025 por habitante", AUS, "<var>_real / pop_harmonizada"),
    ("ES: TR, TE, B9", "Receita total, despesa total e capacidade(+)/necessidade(−) de financiamento", "Eurostat gov_10a_main (SEC 2010)", EU + "gov_10a_main", "2016–2025", "Espanha: S13, S1311, S1312, S1313, S1314", "milhões de euros", "Sem ausências", "Leitura direta"),
    ("ES: impostos_proprios", "Impostos sobre produção e importação, sobre renda e patrimônio e de capital", "Eurostat gov_10a_main", EU + "gov_10a_main", "2016–2025", "idem", "milhões de euros", "—", "D2REC + D5REC + D91REC"),
    ("ES: transf_recebidas", "Outras transferências correntes e transferências de capital recebidas (inclui intragovernamentais)", "Eurostat gov_10a_main", EU + "gov_10a_main", "2016–2025", "idem", "milhões de euros", "—", "D7REC + D9REC"),
    ("ES: GD", "Dívida bruta consolidada (Maastricht)", "Eurostat gov_10dd_edpt1", EU + "gov_10dd_edpt1", "2016–2025", "idem", "milhões de euros", "—", "Leitura direta"),
    ("ES: PIB, pop_1jan", "PIB a preços correntes e população em 1.º de janeiro", "Eurostat nama_10_gdp; demo_pjan", EU, "2016–2025", "Espanha", "milhões de euros; habitantes", "—", "Leitura direta"),
    ("ES: fator_hicp", "Fator para euros de 2025", "Eurostat prc_hicp_aind (INX_A_AVG, CP00)", EU + "prc_hicp_aind", "2012–2025", "Espanha", "adimensional", "—", "HICP_2025 / HICP_t"),
    ("ES: *_pct_pib, *_real_pc_eur, dep_transf, autonomia_trib", "Indicadores derivados", "Calculada", "—", "2016–2025", "idem", "% PIB; euros de 2025 per capita; proporção", "—", "100·X/PIB; X·10^6·fator_hicp/pop; transf_recebidas/TR; impostos_proprios/TR"),
]
cols = ["variavel", "conceito", "fonte", "endereco_eletronico", "periodo", "cobertura", "unidade", "tratamento_ausentes", "transformacao_formula"]
df = pd.DataFrame(V, columns=cols)
df.insert(0, "base", ["03_dados_tratados/painel_focos_manaus_parintins.csv"] * 32 + ["03_dados_tratados/espanha_subsetores.csv"] * (len(df) - 32))

# Campos das tabelas brutas (02_dados_brutos_atualizados/planilhas)
B = [
 ("siconfi_dca_manaus_parintins_2013_2025", "exercicio", "Ano do exercício da Declaração de Contas Anuais", "ano"),
 ("siconfi_dca_manaus_parintins_2013_2025", "instituicao", "Nome do ente declarante", "texto"),
 ("siconfi_dca_manaus_parintins_2013_2025", "cod_ibge", "Código IBGE do ente", "código"),
 ("siconfi_dca_manaus_parintins_2013_2025", "uf", "Unidade da Federação", "texto"),
 ("siconfi_dca_manaus_parintins_2013_2025", "anexo", "Anexo da DCA (I-AB balanço; I-C receitas; I-D despesas por natureza; I-E despesas por função)", "texto"),
 ("siconfi_dca_manaus_parintins_2013_2025", "rotulo", "Rótulo do quadro do anexo", "texto"),
 ("siconfi_dca_manaus_parintins_2013_2025", "coluna", "Coluna do demonstrativo (ex.: Receitas Brutas Realizadas, Deduções - FUNDEB, Despesas Empenhadas)", "texto"),
 ("siconfi_dca_manaus_parintins_2013_2025", "cod_conta", "Código da conta no plano de contas (prefixo RO/RI receita; DO/DI despesa, I = intraorçamentária)", "código"),
 ("siconfi_dca_manaus_parintins_2013_2025", "conta", "Descrição da conta", "texto"),
 ("siconfi_dca_manaus_parintins_2013_2025", "valor", "Valor declarado", "R$ correntes"),
 ("siconfi_dca_manaus_parintins_2013_2025", "populacao", "População informada pelo Siconfi para o exercício (defasada em um ano em relação ao IBGE)", "habitantes"),
 ("siconfi_extrato_entregas_focos", "entregavel / periodo / data_status / status_relatorio", "Relatório entregue, período, data e situação (HO = homologado)", "texto/data"),
 ("ibge_sidra", "consulta / variavel_id / variavel / unidade", "Tabela e variável do Sidra consultadas", "texto"),
 ("ibge_sidra", "cod_ibge / localidade / periodo", "Município (ou Brasil) e período de referência", "código/texto"),
 ("ibge_sidra", "valor_publicado", "Valor como publicado ('...' = não disponível)", "conforme a unidade"),
 ("eurostat_espanha", "tabela / unit / sector / na_item / time / value / flag", "Dimensões JSON-stat: unidade (MIO_EUR, PC_GDP, INX_A_AVG...), subsetor (S13 governo geral, S1311 central, S1312 regional, S1313 local, S1314 seguridade), item SEC 2010, ano, valor e sinalizador", "conforme a unidade"),
 ("openalex_corpus_*", "openalex_id / doi / ano / titulo / autores / paises / periodico / tipo_fonte / citacoes / palavras_chave / n_referencias / resumo", "Metadados bibliográficos de cada artigo (resumo reconstruído do índice invertido)", "texto/número"),
]
dfb = pd.DataFrame(B, columns=["tabela_bruta", "campo", "conceito", "unidade"])
os.makedirs(os.path.join(ROOT, "04_dicionario_variaveis"), exist_ok=True)
with pd.ExcelWriter(os.path.join(ROOT, "04_dicionario_variaveis", "dicionario_variaveis.xlsx")) as xw:
    df.to_excel(xw, sheet_name="dados_tratados", index=False)
    dfb.to_excel(xw, sheet_name="dados_brutos", index=False)
with open(os.path.join(ROOT, "04_dicionario_variaveis", "dicionario_variaveis.md"), "w", encoding="utf-8") as f:
    f.write("# Dicionário de variáveis\n\nBases tratadas em `03_dados_tratados/`. Valores monetários em R$ correntes salvo indicação; sufixos `_real` (R$ de 2025, IPCA) e `_real_pc` (per capita, população harmonizada).\n\n")
    f.write("## 1. Dados tratados\n\n| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
    for r in V:
        f.write("| " + " | ".join(str(x).replace("|", "/") for x in r) + " |\n")
    f.write("\n## 2. Campos dos dados brutos (02_dados_brutos_atualizados/planilhas)\n\n| tabela | campo | conceito | unidade |\n|---|---|---|---|\n")
    for r in B:
        f.write("| " + " | ".join(str(x).replace("|", "/") for x in r) + " |\n")
print("dicionário ok:", len(df), "linhas")
