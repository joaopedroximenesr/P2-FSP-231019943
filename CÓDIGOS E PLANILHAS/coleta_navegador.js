// coleta_navegador.js — registro das rotinas efetivamente executadas no console do navegador em 21/10/2026
// para gerar os arquivos de 02_dados_brutos_atualizados/ (o ambiente de processamento não tinha acesso direto às APIs).
// O script 01_coleta_dados.py reproduz as mesmas consultas em Python.

// ---- 1. SICONFI: DCA completa dos municípios focais (executado em https://apidatalake.tesouro.gov.br)
const base = 'https://apidatalake.tesouro.gov.br/ords/siconfi/tt/';
const entes = { '1302603': 'Manaus', '1303403': 'Parintins' };
const anexos = ['DCA-Anexo I-AB', 'DCA-Anexo I-C', 'DCA-Anexo I-D', 'DCA-Anexo I-E'];
async function getAll(url) {               // paginação da API ORDS (hasMore/offset) com espera em caso de HTTP 429
  let out = [], off = 0;
  while (true) {
    let r;
    for (let t = 0; t < 8; t++) { r = await fetch(url + '&offset=' + off); if (r.status === 429) { await new Promise(z => setTimeout(z, 20000)); continue; } break; }
    if (!r.ok) throw new Error(r.status);
    const j = await r.json(); out = out.concat(j.items);
    if (!j.hasMore) break; off += j.items.length;
  }
  return out;
}
async function coletaFocos() {
  const dca = [], ext = [];
  for (const id of Object.keys(entes)) {
    for (let y = 2013; y <= 2026; y++) ext.push(...await getAll(`${base}extrato_entregas?id_ente=${id}&an_referencia=${y}`));
    for (let y = 2013; y <= 2025; y++) for (const a of anexos)
      dca.push(...await getAll(`${base}dca?an_exercicio=${y}&no_anexo=${encodeURIComponent(a)}&id_ente=${id}`));
  }
  return { dca, ext };   // salvo como siconfi_dca_manaus_parintins_2013-2025.json
}

// ---- 3. IBGE/Sidra (executado em https://servicodados.ibge.gov.br)
const ibge = 'https://servicodados.ibge.gov.br/api/v3/agregados/';
const L = 'localidades=N6[1302603,1303403]';
const consultasIBGE = {
  ipca_indice_mensal: ibge + '1737/periodos/201201-202609/variaveis/2266?localidades=N1[all]',
  pop_estimativas_6579: ibge + '6579/periodos/all/variaveis/9324?' + L,
  pop_censo2022_4714: ibge + '4714/periodos/2022/variaveis/93?' + L,
  pop_censo2010_1378: ibge + '1378/periodos/2010/variaveis/93?' + L + '&classificacao=1[0]|2[0]|287[0]|455[0]',
  pib_municipal_5938: ibge + '5938/periodos/all/variaveis/37|498|513|517|6575|525|543|6574?' + L,
};

// ---- 4. Eurostat (executado em https://ec.europa.eu)
const eu = 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/';
const T = '&sinceTimePeriod=2012&format=JSON&lang=EN';
const consultasEU = {
  hicp_ES: eu + 'prc_hicp_aind?geo=ES&coicop=CP00&unit=INX_A_AVG' + T,
  gov_10a_main_ES: eu + 'gov_10a_main?geo=ES&unit=MIO_EUR&unit=PC_GDP&sector=S13&sector=S1311&sector=S1312&sector=S1313&sector=S1314' + T,
  gov_10dd_edpt1_ES: eu + 'gov_10dd_edpt1?geo=ES&sector=S13&sector=S1311&sector=S1312&sector=S1313&sector=S1314&unit=MIO_EUR&unit=PC_GDP' + T,
  nama_10_gdp_ES: eu + 'nama_10_gdp?geo=ES&na_item=B1GQ&unit=CP_MEUR&unit=CLV15_MEUR&unit=PD15_EUR' + T,
  demo_pjan_ES: eu + 'demo_pjan?geo=ES&age=TOTAL&sex=T' + T,
};

// ---- 5. OpenAlex (executado em https://api.openalex.org): consulta em inglês (13 páginas de 200) e em português/espanhol (até 5 páginas)
const filtroOA = 'title_and_abstract.search:("flypaper effect" OR "fiscal illusion" OR "intergovernmental transfers" OR "intergovernmental grants"),type:article';
