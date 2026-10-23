# Registro de alterações — da base da P1 à base da P2

**Matrícula:** 231019943  
**Trabalho anterior (ponto de partida):** Cauã Victor, P1 de Finanças do Setor Público, matrícula 231020069. Repositório <https://github.com/cauaviictor/P1---FSP---231020069---CAUA-VICTOR>, *commit* `5209bcec1a33b4687c53242936f330e7b4a8b83f`, clonado em 21/10/2026.  
**Conjunto atribuído na P2:** Espanha · Manaus/AM · Parintins/AM (tabela de distribuição atualizada pelo professor).

A base original foi preservada sem nenhuma modificação em `01_base_original/P1_231020069_CAUA_VICTOR/`.

---

## 1. O que havia na base original

| Item | Conteúdo | Observações da conferência |
|---|---|---|
| `SICONFI - AL/RJ - RECEITAS/DESPESAS/*.csv` | Exportações do Finbra/Siconfi (2013–2022) de todos os municípios de AL e RJ | Arquivos editáveis, mas sem registro de data de extração. Não cobrem o Amazonas. |
| `P1 FSP (2).xlsx` | Abas MACEIÓ, DUQUE DE CAXIAS, ESPANHA e respostas | Fórmulas preservadas (ex.: `=B3*W3`). |
| `PROVA EM PDF.pdf` / `PROVA EM WORD.docx` | Resolução das 10 questões | — |
| `LINKS IMPORTANTES.pdf` | Fontes: Siconfi, IBGE Cidades, painel do IDEB, Calculadora do Cidadão (BCB), FMI WEO abr./2024 | Links de dados, sem parâmetros de consulta. |

### Problemas identificados

1. **Unidades diferentes das atribuídas.** A base trata de Maceió/AL e Duque de Caxias/RJ; o conjunto da P2 é Manaus/AM e Parintins/AM. Os dados municipais precisaram ser **reconstruídos a partir das fontes oficiais**; a Espanha foi mantida e atualizada.
2. **Deflator inconsistente.** O fator de correção do IPCA de 2022 é 1,0054, embora 2022 seja o ano-base (deveria ser 1). Os fatores foram obtidos pontualmente na Calculadora do Cidadão, sem indicação das datas de início e fim.
3. **Mistura de bases populacionais.** A coluna POPULAÇÃO combina estimativas projetadas do Censo 2010 (até 2021) com o Censo 2022 (Maceió: 1.031.597 em 2021 → 957.916 em 2022), criando uma quebra artificial nos valores per capita. Parte dos números está armazenada como texto (`'1.013.773'`).
4. **Ausências misturadas a números.** O IDEB aparece como `'--'` nos anos ímpares/pares sem prova, na mesma coluna numérica.
5. **Receita bruta sem deduções e despesa com intraorçamentárias.** A receita corrente não descontava as deduções para o FUNDEB e a despesa total incluía as operações intraorçamentárias, o que superestima receita e despesa.
6. **Espanha — conceito de saldo.** A série rotulada “EQUILIBRIO ESTRUTURAL” não coincide com o saldo efetivo das administrações públicas (B.9): as diferenças chegam a 104% (ver `05_registro_alteracoes/comparacao_P1_P2_espanha.csv`). O próprio texto da P1 calcula o déficit como receita menos despesa, que é outro conceito.
7. **Espanha — nível de governo.** O FMI fornece apenas o governo geral, o que impede comparar os municípios brasileiros com o nível local ou regional espanhol.
8. **Arredondamento.** A P1 truncava os valores em duas casas. A P2 arredonda segundo a ABNT NBR 5891.

## 2. Inclusões (ampliação da base)

| Inclusão | Fonte | Arquivo bruto |
|---|---|---|
| DCA completa (Anexos I-AB, I-C, I-D, I-E) de Manaus e Parintins, 2013–2025 (19.249 registros) | API Siconfi | `02_dados_brutos_atualizados/siconfi/siconfi_dca_manaus_parintins_2013-2025.json` |
| Extrato de entregas de Manaus e Parintins (verificação de homologação) | API Siconfi | `02_dados_brutos_atualizados/siconfi/siconfi_extrato_entregas_manaus_parintins.json` |
| IPCA mensal (número-índice), população (estimativas, Censos 2010 e 2022) e PIB de Manaus e Parintins | IBGE/Sidra | `02_dados_brutos_atualizados/ibge/ibge_ipca_pop_pib.json` |
| Espanha por subsetor (central, CCAA, local, seguridade): receitas, despesas, impostos, transferências, saldo, dívida, PIB, população, IPCH | Eurostat | `02_dados_brutos_atualizados/eurostat/espanha_eurostat.json` |
| Corpus bibliométrico (2.466 registros em inglês + 406 em português/espanhol; 1.992 artigos após filtros) | OpenAlex | `02_dados_brutos_atualizados/openalex/*.json` |
| Metadados verificados das 114 referências do artigo | OpenAlex | `08_artigo/refs/` |

## 3. Correções

| # | Correção | Efeito |
|---|---|---|
| C1 | Deflator: média anual do número-índice do IPCA (Sidra 1737), base 2025 = 1 | Fator do ano-base passa a ser exatamente 1; valores reais comparáveis |
| C2 | População harmonizada aos Censos 2010 e 2022 (série oficial mantida para sensibilidade) | Remove quebra de ~11% (Manaus) e ~20% (Parintins) entre 2021 e 2022 |
| C3 | Receitas líquidas das deduções do FUNDEB; FUNDEB recebido mantido entre as transferências | Receita e dependência medem o que efetivamente financia o município |
| C4 | Exclusão das operações intraorçamentárias da receita e da despesa | Despesa de Manaus reduzida entre R$ 0,16 bi (2017) e R$ 0,90 bi (2020) por ano |
| C5 | Harmonização das três classificações da receita (até 2017; 2018–2021; 2022–2025) por nome de conta, com regra anti-dupla contagem | Séries de FPM, ICMS, FUNDEB, SUS, IPTU, ISS, ITBI e IRRF contínuas; contas usadas em `03_dados_tratados/auditoria_contas_focos.csv` |
| C6 | Espanha: saldo efetivo B.9 e dívida de Maastricht (Eurostat) no lugar do “equilíbrio estrutural” (FMI) | Conceito alinhado às regras fiscais europeias |
| C7 | Ausências explícitas (NA); nenhum dado ausente substituído por zero | Parintins 2016 e PIB 2024–2025 permanecem ausentes |
| C8 | Valores numéricos armazenados como número (não texto) | Evita erros de cálculo em planilhas |

## 4. Transformações (fórmulas)

- **Valor real (R$ de 2025):** `X_real = X × (Ī_2025 / Ī_t)`, com `Ī_t` = média dos 12 números-índices mensais do IPCA no ano `t`.
- **Per capita:** `X_real_pc = X_real / pop_harmonizada`.
- **População harmonizada (2016–2021):** `P_t = P_2010 × (P_2022/P_2010)^((t + 0,5 − 2010,583)/12)` (censos em 1.º/08, estimativas em 1.º/07); 2023 por interpolação entre o Censo 2022 e a estimativa de 2024.
- **Dependência:** `(transf. correntes − deduções + transf. de capital) / (receita corrente − deduções + receita de capital)`.
- **Autonomia tributária:** `receita tributária / (receita corrente − deduções)`.
- **Resultado orçamentário:** `receita total líquida − despesa empenhada (exceto intra)`.
- **Espanha:** `dep_transf = (D7REC + D9REC)/TR`; `autonomia = (D2REC + D5REC + D91REC)/TR`; `% PIB = 100 × X/PIB`; `euros de 2025 per capita = X × 10⁶ × (HICP_2025/HICP_t) / população`.

Todas as transformações estão em `06_codigos_e_planilhas/02_tratamento.py` e `06_codigos_e_planilhas/harmonizacao.py` (e, em fórmulas do Excel, `06_codigos_e_planilhas/planilha_calculos_P2_231019943.xlsx`).

## 5. Cobertura, quebras de série e revisões

| Situação | Tratamento |
|---|---|
| Parintins sem DCA de 2016 no Siconfi (API retorna zero registros para DCA e RREO do 6.º bimestre; extrato de entregas só registra RGF) | Ano mantido como ausente; séries do município analisadas a partir de 2017 |
| 2013: nenhum dos dois municípios tem DCA na API | Período fixado em 2016–2025 (dez exercícios mais recentes completos para Manaus) |
| Plano de contas da receita alterado em 2018 e 2022 | Harmonização por nome de conta (C5) |
| População: estimativas pré-censo (até 2021) × Censo 2022 × estimativas pós-censo (2024–25); 2023 sem publicação | Série harmonizada (C2); série oficial guardada |
| PIB municipal disponível só até 2023 | Regressões com PIB limitadas a 2016–2023; especificação sem PIB cobre 2016–2025 |
| Revisões do Eurostat (PIB revisado em até 2,2% em relação ao FMI usado na P1) | Comparação em `05_registro_alteracoes/comparacao_P1_P2_espanha.csv` |

## 6. Coleta

As consultas às APIs foram executadas em 21/10/2026 a partir de um navegador (requisições `fetch` aos mesmos *endpoints*), porque o ambiente de processamento não tinha acesso direto a esses domínios. O script `06_codigos_e_planilhas/01_coleta_dados.py` reproduz exatamente as mesmas consultas em Python e grava os resultados com o sufixo `_recoleta`, permitindo conferir eventuais revisões das fontes.

## 7. Quadro-síntese: material anterior × nova versão

| Item exigido | P1 (material anterior) | P2 (nova versão) | Onde está |
|---|---|---|---|
| Base original | Planilha e CSVs do Finbra (AL e RJ) | Preservada sem alterações | `01_base_original/` |
| Dados brutos | CSVs baixados manualmente, sem data/parâmetros | Respostas das APIs (JSON) + as mesmas tabelas em CSV/XLSX | `02_dados_brutos_atualizados/` e `/planilhas/` |
| Dados tratados | Abas da planilha com fórmulas | CSV e XLSX gerados por código | `03_dados_tratados/` |
| Dicionário de variáveis | Inexistente | Conceito, fonte, URL, período, cobertura, unidade, ausentes e fórmula (tratados) + campos dos brutos | `04_dicionario_variaveis/` |
| Registro de alterações | Inexistente | Este arquivo + confronto numérico P1 × P2 (Espanha) | `05_registro_alteracoes/` |
| Planilhas/códigos | Uma planilha | Scripts Python/R + planilha com fórmulas vivas conferida contra o Python | `06_codigos_e_planilhas/` |
| Estudo bibliométrico | Inexistente | `bibliometrix`, Tabela 1 no formato de Baker, Larcker e Wang (2022) | `06_codigos_e_planilhas/05_bibliometria.R`, `07_resultados/bibliometria/` |

## 8. Versões

- **v1 (21/10/2026):** reconstrução da base, artigo (com painel complementar dos 62 municípios do AM).
- **v2 (21/10/2026):** (i) pastas renomeadas para corresponder a cada item exigido; (ii) dados brutos também em CSV/XLSX; (iii) consulta bibliométrica ampliada com termos em português e espanhol (+406 registros) e página bibliométrica refeita no formato da Tabela 1 de Baker, Larcker e Wang (2022); (iv) planilha de cálculos com fórmulas; (v) dicionário ampliado com os campos dos dados brutos.
- **v3 (21/10/2026):** a análise passou a usar **somente as unidades atribuídas — Manaus, Parintins e Espanha**. Foram retirados do repositório os dados e as estimações do painel dos demais municípios do Amazonas (arquivos `siconfi_dca_amazonas_62mun_*`, `ibge_amazonas_pib_pop_ipca.json` e `painel_amazonas.csv`); o extrato de entregas dos dois municípios, que estava dentro de um desses arquivos, foi preservado em arquivo próprio. As regressões foram refeitas com os dados anuais dos dois municípios (MQO com efeito fixo de município, erros HC3 e distribuição *t*, 15 observações), com oito testes de sensibilidade e diagnósticos para amostra pequena. As bases de Manaus, Parintins e Espanha e os demais tratamentos não mudaram.
