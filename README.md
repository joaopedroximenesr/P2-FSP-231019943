# P2 — Finanças do Setor Público — Matrícula 231019943

**Transferências intergovernamentais, ilusão fiscal e efeito *flypaper*: Manaus e Parintins (AM) diante do federalismo fiscal espanhol, 2016–2025**

*Versão 3 — análise restrita às unidades atribuídas (Manaus, Parintins e Espanha).*

Autor: João Pedro Furtado Ximenes da Rocha · Matrícula **231019943**  
Conjunto atribuído: **Espanha · Manaus/AM · Parintins/AM**  
Trabalho anterior (ponto de partida): P1 de Cauã Victor, matrícula 231020069 — <https://github.com/cauaviictor/P1---FSP---231020069---CAUA-VICTOR> (*commit* `5209bcec`)  
Referência de partida: Ferreira, L. O. G. *Constitutional tax transfer in Brazilian municipalities: the fiscal illusion and the flypaper effect*. Tese (Doutorado), Universidade de Brasília, 2021.

📄 **Artigo em PDF:** [`P2_FSP_231019943_artigo.pdf`](P2_FSP_231019943_artigo.pdf) (também em `08_artigo/`)


## Visão rápida

| Composição da receita | Dependência de transferências |
|---|---|
| ![fig1](07_resultados/figuras/fig1_composicao_receita_focos.png) | ![fig2](07_resultados/figuras/fig2_dependencia_transferencias.png) |

| Transferência × despesa per capita | Rede de coocorrência (bibliometrix) |
|---|---|
| ![fig3](07_resultados/figuras/fig3_dispersao_transf_despesa.png) | ![rede](07_resultados/bibliometria/rede_coocorrencia.png) |

## Checklist da entrega

| Item exigido pelo professor | Onde está |
|---|---|
| Artigo em PDF, identificado pela matrícula, com título, resumo, palavras-chave, seções obrigatórias e referências | [`P2_FSP_231019943_artigo.pdf`](P2_FSP_231019943_artigo.pdf) |
| Página de estudo bibliométrico no formato das 2 primeiras páginas de Baker, Larcker e Wang (2022), com **bibliometrix** | Seção 2.1 do artigo (Tabela 1 e Figura 1) · código [`06_codigos_e_planilhas/05_bibliometria.R`](06_codigos_e_planilhas/05_bibliometria.R) · saídas [`07_resultados/bibliometria/`](07_resultados/bibliometria/) |
| Pelo menos 80 artigos de periódicos citados e discutidos | 114 artigos de periódicos citados no texto, e a lista de referências do PDF contém somente eles · catálogo com periódico e DOI em [`08_artigo/refs/catalogo_artigos.json`](08_artigo/refs/catalogo_artigos.json). Leis, bases de dados, a tese-base e a P1 aparecem em notas de rodapé (lista em [`08_artigo/refs_outros_documentos.bib`](08_artigo/refs_outros_documentos.bib)) |
| Base original, quando disponível | [`01_base_original/`](01_base_original/) |
| Dados brutos atualizados, em formato editável | [`02_dados_brutos_atualizados/`](02_dados_brutos_atualizados/) (JSON das APIs) e [`02_dados_brutos_atualizados/planilhas/`](02_dados_brutos_atualizados/planilhas/) (CSV e XLSX) |
| Dados tratados, em formato editável | [`03_dados_tratados/`](03_dados_tratados/) (CSV e `base_tratada_P2_231019943.xlsx`) |
| Dicionário de variáveis, com conceitos, unidades e fontes | [`04_dicionario_variaveis/dicionario_variaveis.xlsx`](04_dicionario_variaveis/dicionario_variaveis.xlsx) · [`.md`](04_dicionario_variaveis/dicionario_variaveis.md) |
| Registro das atualizações e correções, comparando o material anterior com a nova versão | [`05_registro_alteracoes/registro_alteracoes.md`](05_registro_alteracoes/registro_alteracoes.md) · [`comparacao_P1_P2_espanha.csv`](05_registro_alteracoes/comparacao_P1_P2_espanha.csv) |
| Planilhas ou códigos que reproduzem tratamentos, cálculos, tabelas, gráficos e resultados | [`06_codigos_e_planilhas/`](06_codigos_e_planilhas/) (Python, R e [`planilha_calculos_P2_231019943.xlsx`](06_codigos_e_planilhas/planilha_calculos_P2_231019943.xlsx) com fórmulas) |
| README com organização e instruções de reprodução | este arquivo |

## Organização do repositório

```
P2_FSP_231019943_artigo.pdf          artigo final
01_base_original/                    cópia integral da P1 (CSVs do Finbra, planilha, prova, referencial teórico)
02_dados_brutos_atualizados/
   siconfi/   DCA (Anexos I-AB, I-C, I-D, I-E) de Manaus e Parintins 2013–2025 e extrato de entregas
   ibge/      IPCA mensal (Sidra 1737), população (6579, 4714, 1378) e PIB municipal (5938) de Manaus e Parintins
   eurostat/  gov_10a_main, gov_10dd_edpt1, prc_hicp_aind, nama_10_gdp, demo_pjan (Espanha)
   openalex/  corpus bibliométrico (consultas em inglês e em português/espanhol)
   planilhas/ os mesmos dados brutos em CSV e em dados_brutos_atualizados.xlsx (uma aba por tabela)
03_dados_tratados/
   painel_focos_manaus_parintins.csv   nominais, reais (R$ 2025) e per capita dos dois municípios
   espanha_subsetores.csv              Espanha por subsetor (S13, S1311, S1312, S1313, S1314)
   populacao_manaus_parintins.csv      população oficial e harmonizada
   deflatores.csv                      IPCA e IPCH, base 2025
   auditoria_contas_focos.csv          contas do Siconfi somadas em cada variável/ano
   base_tratada_P2_231019943.xlsx      todas as bases acima em abas
04_dicionario_variaveis/             dicionário (dados tratados + campos dos dados brutos)
05_registro_alteracoes/              registro de correções e inclusões; confronto P1 × P2
06_codigos_e_planilhas/
   01_coleta_dados.py            recoleta dos dados nas APIs (Siconfi, IBGE, Eurostat, OpenAlex)
   coleta_navegador.js           registro das rotinas executadas na coleta original
   01b_brutos_para_planilhas.py  JSON brutos -> CSV/XLSX editáveis
   harmonizacao.py, jsonstat.py  regras do plano de contas; leitor JSON-stat
   02_tratamento.py              brutos -> tratados (deflação, população, per capita, indicadores)
   03_analise.py                 descritivas, regressões (Manaus e Parintins), diagnósticos, figuras
   04_numeros_artigo.py          exporta cada número citado no texto para o LaTeX
   05_bibliometria.R             estudo bibliométrico com bibliometrix (Tabela 1 no formato de Baker et al.)
   05_tabelas_latex.py           tabelas do artigo
   06_dicionario.py              dicionário de variáveis
   07_comparacao_p1.py           confronto dos valores da Espanha entre P1 (FMI) e P2 (Eurostat)
   08_planilha_formulas.py       gera a planilha de cálculos com fórmulas
   planilha_calculos_P2_231019943.xlsx   cálculos em fórmulas do Excel, com aba de conferência contra o Python
07_resultados/   tabelas/ (CSV, JSON) · figuras/ (PNG) · bibliometria/ (saídas do bibliometrix)
08_artigo/       LaTeX (abnTeX2), seções, tabelas, refs.bib e PDF
```

## Como reproduzir

Requisitos: Python ≥ 3.10 (`pandas`, `numpy`, `openpyxl`, `statsmodels`, `linearmodels`, `scipy`, `matplotlib`; `requests` só para recoletar), R ≥ 4.1 com `bibliometrix` e, para o PDF, LaTeX com `abntex2`.

```bash
pip install pandas numpy openpyxl statsmodels linearmodels scipy matplotlib requests

python3 06_codigos_e_planilhas/01_coleta_dados.py          # opcional: recoleta (grava *_recoleta para comparação)
python3 06_codigos_e_planilhas/01b_brutos_para_planilhas.py
python3 06_codigos_e_planilhas/02_tratamento.py
Rscript 06_codigos_e_planilhas/05_bibliometria.R
python3 06_codigos_e_planilhas/03_analise.py
python3 06_codigos_e_planilhas/04_numeros_artigo.py
python3 06_codigos_e_planilhas/05_tabelas_latex.py
python3 06_codigos_e_planilhas/06_dicionario.py
python3 06_codigos_e_planilhas/07_comparacao_p1.py
python3 06_codigos_e_planilhas/08_planilha_formulas.py
cd 08_artigo && latexmk -pdf artigo_P2_231019943.tex
```

### Bibliometria no RStudio (como pedido na disciplina)

```r
## bibliometrix
install.packages("bibliometrix")
library(bibliometrix)
biblioshiny()
# No biblioshiny: Data > Import or Load files > Database "OpenAlex API"
# > selecione 07_resultados/bibliometria/openalex_works.RData
```

O script `05_bibliometria.R` gera esse `.RData` a partir dos JSON do OpenAlex e reproduz, sem interface, as mesmas análises (informações gerais, produção anual, lei de Lotka, rede de coocorrência, mapa temático) e a Tabela 1 no formato de Baker, Larcker e Wang (2022): por periódico, (1) artigos sobre transferências intergovernamentais, (2) quantos tratam do efeito *flypaper* ou da ilusão fiscal e (3) a participação de (2) em (1), de 2000 a 2025.

## Principais decisões metodológicas

- **Período:** 2016–2025 (dez exercícios mais recentes com DCA completa). Parintins não tem DCA de 2016 no Siconfi (ausente, não imputado). O PIB municipal vai até 2023.
- **Valores reais:** R$ de 2025 pelo IPCA (média anual do número-índice); euros de 2025 pelo IPCH.
- **Per capita:** população harmonizada aos Censos de 2010 e 2022; a série oficial do IBGE é usada como teste de sensibilidade.
- **Receitas e despesas:** exceto intraorçamentárias; receitas líquidas das deduções para o FUNDEB.
- **Plano de contas:** as três classificações da receita (até 2017, 2018–2021, 2022–2025) harmonizadas pelo nome das contas.
- **Espanha:** Eurostat por subsetor (SEC 2010); municípios comparados às Comunidades Autônomas e às entidades locais.
- **Unidades:** somente as atribuídas — Manaus, Parintins e Espanha (sem outros municípios).
- **Inferência:** MQO com os dados anuais dos dois municípios empilhados e efeito fixo de município (15 observações com PIB, 2016–2023); erros robustos HC3 com distribuição *t*; oito testes de sensibilidade (tendência, FPM, log, primeiras diferenças, população oficial, cada município separado, sem PIB até 2025) e diagnósticos para amostra pequena. Resultados lidos como associações, não como efeitos causais.

## Fontes (coleta em 21/10/2026)

- Secretaria do Tesouro Nacional — API Siconfi: <https://apidatalake.tesouro.gov.br/ords/siconfi/tt/>
- IBGE — API de Agregados (Sidra): <https://servicodados.ibge.gov.br/api/v3/agregados>
- Eurostat — API de disseminação: <https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/>
- OpenAlex: <https://api.openalex.org>
