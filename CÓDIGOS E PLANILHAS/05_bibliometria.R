# =====================================================================
# 05_bibliometria.R — Estudo bibliométrico com o pacote bibliometrix
# P2 FSP — Matrícula 231019943
#
# Uso interativo exigido na disciplina (RStudio):
#   install.packages("bibliometrix")
#   library(bibliometrix)
#   biblioshiny()
#   -> Data > Import or Load files > Database: "OpenAlex API"
#      > arquivo 07_resultados/bibliometria/openalex_works.RData (gerado por este script)
#
# Este script reproduz em modo não interativo as mesmas análises e gera a
# Tabela 1 no formato de Baker, Larcker e Wang (2022, Tabela 1).
# Execução: Rscript 06_codigos_e_planilhas/05_bibliometria.R
# =====================================================================
suppressMessages({library(bibliometrix); library(jsonlite); library(ggplot2)})
Sys.setlocale("LC_ALL", "C.UTF-8")
args <- commandArgs(trailingOnly = FALSE)
here <- normalizePath(dirname(sub("--file=", "", args[grep("--file=", args)])))
root <- normalizePath(file.path(here, ".."))
rawdir <- file.path(root, "02_dados_brutos_atualizados/openalex")
out  <- file.path(root, "07_resultados/bibliometria"); dir.create(out, showWarnings = FALSE, recursive = TRUE)

# ---------------------------------------------------------------- 1. Corpus (duas consultas, sem duplicatas)
q_en <- fromJSON(file.path(rawdir, "openalex_flypaper_fiscalillusion_transfers.json"), simplifyVector = FALSE)$results
q_pt <- fromJSON(file.path(rawdir, "openalex_termos_pt_es.json"), simplifyVector = FALSE)$results
works <- c(q_en, q_pt)
ids <- vapply(works, function(w) w$id, "")
works <- works[!duplicated(ids)]
log <- c(registros_ingles = length(q_en), registros_pt_es = length(q_pt), unicos = length(works))
sem_autor <- vapply(works, function(w) length(w$authorships) == 0, TRUE)
works <- works[!sem_autor]
eh_periodico <- vapply(works, function(w) { s <- w$primary_location$source; !is.null(s) && identical(s$type, "journal") }, TRUE)
works <- works[eh_periodico]
ano <- vapply(works, function(w) as.numeric(w$publication_year), 1)
works <- works[ano <= 2025]
log <- c(log, sem_autoria = sum(sem_autor), nao_periodico = sum(!eh_periodico), corpus_final = length(works))
for (i in seq_along(works)) for (f in c("grants","mesh","concepts","sustainable_development_goals","counts_by_year","corresponding_author_ids","corresponding_institution_ids"))
  if (is.null(works[[i]][[f]])) works[[i]][f] <- list(list())
save(works, file = file.path(out, "openalex_works.RData"))
write.csv(data.frame(etapa = names(log), n = as.integer(log)), file.path(out, "fluxo_selecao_corpus.csv"), row.names = FALSE)

# ---------------------------------------------------------------- 2. Conversão e análise descritiva (bibliometrix)
M <- convert2df(file.path(out, "openalex_works.RData"), dbsource = "openalex_api")
saveRDS(M, file.path(out, "bibliometrix_M.rds"))
cat("Registros:", nrow(M), " Período:", min(M$PY), "-", max(M$PY), "\n")
res <- biblioAnalysis(M, sep = ";")
S <- summary(res, k = 20, pause = FALSE, verbose = FALSE)
sink(file.path(out, "summary_bibliometrix.txt")); print(S$MainInformation); print(S$AnnualProduction)
print(S$MostProdAuthors); print(S$MostCitedPapers); print(S$MostProdCountries); print(S$MostRelSources); print(S$MostRelKeywords); sink()

ap <- as.data.frame(table(M$PY)); names(ap) <- c("ano","artigos"); ap$ano <- as.integer(as.character(ap$ano))
write.csv(ap, file.path(out, "producao_anual.csv"), row.names = FALSE)

txt <- tolower(paste(M$TI, M$AB, M$DE))
M$tema_fly <- grepl("flypaper|fiscal illusion|ilus[aã]o fiscal|ilusi[oó]n fiscal", txt)
M$tema_did <- grepl("difference-in-difference|difference in difference|differences-in-differences|staggered|diferen[cç]as[- ]em[- ]diferen[cç]as", txt)
M$brasil  <- grepl("brazil|brasil", paste(txt, tolower(M$AU_CO)))
termos <- aggregate(cbind(flypaper = grepl("flypaper", txt), fiscal_illusion = grepl("fiscal illusion|ilus[aã]o fiscal|ilusi[oó]n fiscal", txt),
                          did = M$tema_did, brasil = M$brasil) ~ M$PY, FUN = sum)
names(termos)[1] <- "ano"
write.csv(termos, file.path(out, "termos_por_ano.csv"), row.names = FALSE)

tab <- function(x, n = 15) { t <- sort(table(trimws(unlist(strsplit(x[!is.na(x) & x != ""], ";")))), decreasing = TRUE)
  d <- data.frame(item = names(t), n = as.integer(t)); d <- d[d$item != "" & d$item != "NA", ]; head(d, n) }
write.csv(tab(M$SO, 15), file.path(out, "top_fontes.csv"), row.names = FALSE)
write.csv(tab(M$AU_CO, 15), file.path(out, "top_paises.csv"), row.names = FALSE)
write.csv(tab(M$DE, 25), file.path(out, "top_palavras.csv"), row.names = FALSE)
write.csv(head(M[order(-M$TC), c("AU","PY","TI","SO","TC","DI")], 30), file.path(out, "mais_citados.csv"), row.names = FALSE)

L <- tryCatch(lotka(M), error = function(e) NULL)
if (!is.null(L) && is.list(L)) { sink(file.path(out, "lotka.txt")); print(L$AuthorProd); print(c(beta = L$Beta, C = L$C, R2 = L$R2, p_KS = L$p.value)); sink() }

# ---------------------------------------------------------------- 3. Tabela 1 no formato de Baker, Larcker e Wang (2022)
# Baker et al. contam, por periódico, artigos com DiD (col. 1), com DiD escalonado (col. 2) e a razão (col. 3), 2000–2019.
# Aqui: artigos sobre transferências intergovernamentais (col. 1), dos quais tratam de efeito flypaper ou ilusão fiscal
# (col. 2) e a razão (col. 3), 2000–2025, em três grupos de periódicos.
P <- M[M$PY >= 2000, ]
grupos <- list(
  "Finanças públicas e escolha pública" = c("PUBLIC FINANCE REVIEW", "INTERNATIONAL TAX AND PUBLIC FINANCE", "PUBLIC CHOICE",
                                            "JOURNAL OF PUBLIC ECONOMICS", "NATIONAL TAX JOURNAL"),
  "Federalismo, orçamento e governo local" = c("PUBLIC BUDGETING &AMP FINANCE", "PUBLIUS THE JOURNAL OF FEDERALISM", "LOCAL GOVERNMENT STUDIES",
                                               "PUBLIC FINANCE AND MANAGEMENT", "STATE AND LOCAL GOVERNMENT REVIEW"),
  "Periódicos brasileiros" = NULL)
# Periódicos brasileiros: os cinco editados no Brasil com mais artigos no corpus em 2000–2025
# (lista explícita; editoras conferidas no campo host_organization do OpenAlex: USP, FGV, BNB, UFV)
grupos[["Periódicos brasileiros"]] <- toupper(c("Economia Aplicada", "Revista de Administração Pública", "Revista Econômica do Nordeste",
                                               "Administração Pública e Gestão Social", "Estudos Econômicos (São Paulo)"))
linhas <- list()
for (g in names(grupos)) {
  for (so in grupos[[g]]) {
    d <- P[toupper(P$SO) == so, ]
    linhas[[length(linhas) + 1]] <- data.frame(grupo = g, periodico = so, transferencias = nrow(d), flypaper_ilusao = sum(d$tema_fly),
                                               desde_2010 = sum(d$tema_fly & d$PY >= 2010))
  }
}
T1 <- do.call(rbind, linhas)
T1$pct <- round(100 * T1$flypaper_ilusao / T1$transferencias, 1)
sub <- aggregate(cbind(transferencias, flypaper_ilusao, desde_2010) ~ grupo, T1, sum)
sub$pct <- round(100 * sub$flypaper_ilusao / sub$transferencias, 1)
tot <- data.frame(grupo = "Total dos 15 periódicos", transferencias = sum(T1$transferencias), flypaper_ilusao = sum(T1$flypaper_ilusao),
                  desde_2010 = sum(T1$desde_2010)); tot$pct <- round(100 * tot$flypaper_ilusao / tot$transferencias, 1)
corpus <- data.frame(grupo = "Corpus completo (todos os periódicos)", transferencias = nrow(P), flypaper_ilusao = sum(P$tema_fly),
                     desde_2010 = sum(P$tema_fly & P$PY >= 2010)); corpus$pct <- round(100 * corpus$flypaper_ilusao / corpus$transferencias, 1)
write.csv(T1, file.path(out, "tabela1_baker_periodicos.csv"), row.names = FALSE)
write.csv(rbind(sub, tot, corpus), file.path(out, "tabela1_baker_subtotais.csv"), row.names = FALSE)
write.csv(data.frame(n_did = sum(P$tema_did), n_did_desde_2015 = sum(P$tema_did & P$PY >= 2015), n_brasil = sum(P$brasil),
                     n_brasil_fly = sum(P$brasil & P$tema_fly)), file.path(out, "tabela1_baker_extras.csv"), row.names = FALSE)

# ---------------------------------------------------------------- 4. Redes e mapa temático
NetM <- biblioNetwork(M, analysis = "co-occurrences", network = "author_keywords", sep = ";")
png(file.path(out, "rede_coocorrencia.png"), width = 1800, height = 1400, res = 200)
net <- networkPlot(NetM, n = 40, Title = "Coocorrencia de palavras-chave", type = "fruchterman", size.cex = TRUE, labelsize = 0.8, verbose = FALSE)
plot(net$graph)
dev.off()
tm <- tryCatch(thematicMap(M, field = "DE", n = 250, minfreq = 5), error = function(e) NULL)
if (!is.null(tm)) ggsave(file.path(out, "mapa_tematico.png"), tm$map, width = 9, height = 7, dpi = 200)
cat("OK bibliometria\n")
