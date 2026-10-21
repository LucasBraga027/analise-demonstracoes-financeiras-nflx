"""
Etapa 3 - Contexto macroeconômico e setorial (fontes oficiais):
  * Federal Reserve (H.15): Fed Funds efetivo (diário -> média trimestral)
  * U.S. Treasury: rendimento do título de 10 anos (diário -> média trimestral)
  * BLS: inflação ao consumidor (CPI-U, var. 12 meses) e taxa de desemprego
  * Banco Central Europeu: câmbio mensal de USD, BRL, MXN, GBP, JPY (-> moedas por US$, média trimestral)
  * SEC EDGAR: concorrentes (Disney, Warner Bros. Discovery, Paramount, Comcast) — totais anuais (XBRL)
    e resultado dos segmentos de streaming (XBRL da WBD; texto do MD&A dos 10-K da Disney e da Paramount).
Saídas: dados/macro_trimestral.csv, dados/setor_anual.csv, dados/streaming_concorrentes.csv
"""
import io
import json
import os
import re

import pandas as pd
import requests

from sec_common import DADOS, ROOT, company_facts, filing_url, get_cached, list_filings
from texto_relatorios import html_to_text
from xbrl_parser import parse_instance

SAIDA = os.path.join(ROOT, 'dados')
WEB = {'User-Agent': 'Mozilla/5.0 (UFJF ECO057 - pesquisa academica)'}
INICIO, FIM = 2019, 2026


def baixar(url, nome, method='get', **kw):
    path = os.path.join(DADOS, 'macro', nome)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        r = requests.request(method, url, headers=WEB, timeout=90, **kw)
        r.raise_for_status()
        open(path, 'wb').write(r.content)
    return open(path, encoding='utf-8-sig').read()


def trimestre(idx):
    idx = pd.PeriodIndex(idx, freq='Q')
    return [f'{p.year}T{p.quarter}' for p in idx]


def fed_funds():
    url = ('https://www.federalreserve.gov/datadownload/Output.aspx?rel=H15&series=c5025f4bbbed155a6f17c587772ed69e'
           f'&lastobs=&from=01/01/{INICIO}&to=12/31/{FIM}&filetype=csv&label=include&layout=seriescolumn')
    df = pd.read_csv(io.StringIO(baixar(url, 'fed_funds_h15.csv')), skiprows=5)
    df.columns = ['data', 'valor']
    df['data'] = pd.to_datetime(df['data'])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    return df.set_index('data')['valor'].resample('QE').mean()


def treasury_10y():
    partes = []
    for ano in range(INICIO, FIM + 1):
        url = ('https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/'
               f'{ano}/all?type=daily_treasury_yield_curve&field_tdr_date_value={ano}&page&_format=csv')
        partes.append(pd.read_csv(io.StringIO(baixar(url, f'treasury_{ano}.csv'))))
    df = pd.concat(partes)
    df['Date'] = pd.to_datetime(df['Date'])
    return df.set_index('Date')['10 Yr'].sort_index().resample('QE').mean()


def bls():
    payload = {'seriesid': ['CUUR0000SA0', 'LNS14000000'], 'startyear': str(INICIO - 1), 'endyear': str(FIM)}
    js = json.loads(baixar('https://api.bls.gov/publicAPI/v1/timeseries/data/', 'bls_cpi_desemprego.json',
                           method='post', json=payload))
    out = {}
    for s in js['Results']['series']:
        # Meses sem coleta vêm como "-" (ex.: out/2025, paralisação do governo dos EUA) e ficam vazios
        d = pd.Series({pd.Timestamp(int(x['year']), int(x['period'][1:]), 1): pd.to_numeric(x['value'], errors='coerce')
                       for x in s['data'] if x['period'].startswith('M') and x['period'] != 'M13'}).sort_index()
        out[s['seriesID']] = d.asfreq('MS')
    cpi_yoy = (out['CUUR0000SA0'].pct_change(12) * 100).resample('QE').mean()
    desemprego = out['LNS14000000'].resample('QE').mean()
    return cpi_yoy, desemprego


def cambio_ecb():
    """Moedas por 1 US$, a partir das cotações de referência do BCE (moeda por 1 EUR)."""
    serie = {}
    for moeda in ['USD', 'BRL', 'MXN', 'GBP', 'JPY']:
        url = f'https://data-api.ecb.europa.eu/service/data/EXR/M.{moeda}.EUR.SP00.A?startPeriod={INICIO}-01&format=csvdata'
        df = pd.read_csv(io.StringIO(baixar(url, f'ecb_{moeda}.csv')))
        serie[moeda] = df.set_index(pd.PeriodIndex(df['TIME_PERIOD'], freq='M').to_timestamp())['OBS_VALUE']
    usd = serie['USD']
    out = {'EUR_por_USD': 1 / usd}
    for m in ['BRL', 'MXN', 'GBP', 'JPY']:
        out[f'{m}_por_USD'] = serie[m] / usd
    return {k: v.resample('QE').mean() for k, v in out.items()}


def macro():
    ff, t10 = fed_funds(), treasury_10y()
    cpi, des = bls()
    fx = cambio_ecb()
    df = pd.DataFrame({'fed_funds_pct': ff, 'treasury_10a_pct': t10, 'inflacao_cpi_12m_pct': cpi,
                       'desemprego_pct': des, **fx})
    df = df[(df.index.year >= INICIO)].dropna(how='all')
    df.index = trimestre(df.index)
    df.index.name = 'trimestre'
    # Índice simples do dólar frente às moedas das regiões da Netflix (base 2019T4 = 100; alta = dólar mais forte)
    base = df.loc['2019T4', ['EUR_por_USD', 'BRL_por_USD', 'MXN_por_USD', 'GBP_por_USD', 'JPY_por_USD']]
    df['indice_dolar_cesta_2019T4_100'] = (df[base.index] / base).mean(axis=1) * 100
    return df


# ---------------------------------------------------------------- setor
PARES = {'NFLX': '0001065280', 'DIS': '0001744489', 'WBD': '0001437107', 'PARA': '0000813828', 'CMCSA': '0001166691'}


def anual_companyfacts(cik, tags):
    """Valor anual (10-K) por ano fiscal, unindo as tags (empresas trocam de tag ao longo dos anos)."""
    g = company_facts(cik)['facts']['us-gaap']
    s = pd.Series(dtype=float)
    for tag in tags:
        if tag in g and 'USD' in g[tag]['units']:
            d = pd.DataFrame(g[tag]['units']['USD'])
            d = d[(d['form'] == '10-K') & d['start'].notna()]
            d = d[(pd.to_datetime(d['end']) - pd.to_datetime(d['start'])).dt.days.between(350, 380)]
            d = d.sort_values('filed').drop_duplicates('end', keep='last')
            s = s.combine_first(pd.Series(d['val'].values / 1e6, index=pd.to_datetime(d['end']).dt.year.values))
    return s


def setor_anual():
    linhas = []
    for tk, cik in PARES.items():
        rec = anual_companyfacts(cik, ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
                                       'RevenueFromContractWithCustomerIncludingAssessedTax'])
        ebit = anual_companyfacts(cik, ['OperatingIncomeLoss'])
        for ano in range(INICIO, FIM + 1):
            if ano in rec.index:
                linhas.append({'empresa': tk, 'ano_fiscal': ano, 'receita_usd_mi': rec.get(ano),
                               'ebit_usd_mi': ebit.get(ano) if ano in ebit.index else None})
    df = pd.DataFrame(linhas).sort_values(['empresa', 'ano_fiscal'])
    df['cresc_receita_pct'] = df.groupby('empresa')['receita_usd_mi'].pct_change() * 100
    df['margem_operacional_pct'] = df['ebit_usd_mi'] / df['receita_usd_mi'] * 100
    return df


def texto_10k(tk, cik, f):
    p = os.path.join(DADOS, 'pares', tk, f['acc'], f['doc'])
    return html_to_text(get_cached(filing_url(cik, f['acc'], f['doc']), p))


def num(s):
    s = s.replace(',', '').replace('$', '').strip()
    neg = s.startswith('(')
    v = float(s.strip('()'))
    return -v if neg else v


def streaming_concorrentes():
    """Resultado operacional dos negócios de streaming dos concorrentes, conforme os 10-K (US$ milhões)."""
    out = []
    # Disney: "Operating loss from Direct-to-Consumer decreased $X million, to $A million from $B million" (MD&A).
    # Cada 10-K traz o ano corrente e o anterior; mantém-se a versão mais recente (a partir do 10-K FY2023 o
    # ESPN+ saiu do segmento e os anos anteriores foram reapresentados).
    cik = PARES['DIS']
    for f in list_filings(cik, forms=('10-K',), since='2020-10-01'):
        t = texto_10k('DIS', cik, f)
        padrao = (r'Direct-to-Consumer Operating (results|loss|income) from Direct-to-Consumer (?:increased|decreased) '
                  r'\$[\d,]+ million, to (operating income of |operating loss of )?\$([\d,]+) million from '
                  r'(an operating loss of |operating income of )?\$([\d,]+) million')
        for i, m in enumerate(re.finditer(padrao, t)):
            tipo, qual_atual, atual, qual_ant, anterior = m.groups()
            # Sem qualificador explícito, vale o tipo da frase ("Operating loss from ..." => prejuízo)
            atual_neg = 'loss' in qual_atual if qual_atual else tipo == 'loss'
            ant_neg = 'loss' in qual_ant if qual_ant else tipo == 'loss'
            ano = int(f['report'][:4]) - i
            for a, v, neg in [(ano, atual, atual_neg), (ano - 1, anterior, ant_neg)]:
                out.append({'empresa': 'Disney (Disney+, Hulu)', 'ano_fiscal': a,
                            'metrica': 'Resultado operacional do segmento DTC', 'valor_usd_mi': -num(v) if neg else num(v),
                            'fonte': f"10-K DIS {f['acc']} (MD&A)", 'filed': f['filed']})
    # Paramount: tabela de Adjusted OIBDA por segmento (MD&A)
    cik = PARES['PARA']
    for f in list_filings(cik, forms=('10-K',), since='2022-01-01'):
        t = texto_10k('PARA', cik, f)
        m = re.search(r'Adjusted OIBDA:? TV Media \$ [\d,()]+ \$ [\d,()]+ \$ [\d,()]+ \(?\d+\)? % Direct-to-Consumer (\(?[\d,]+\)?) (\(?[\d,]+\)?)', t)
        if m:
            ano = int(f['report'][:4])
            for a, v in [(ano, m.group(1)), (ano - 1, m.group(2))]:
                out.append({'empresa': 'Paramount (Paramount+, Pluto TV)', 'ano_fiscal': a, 'metrica': 'Adjusted OIBDA do segmento DTC',
                            'valor_usd_mi': num(v), 'fonte': f"10-K PARA {f['acc']} (MD&A)", 'filed': f['filed']})
    # Warner Bros. Discovery: 2022 só no texto do 10-K (tabela "Adjusted EBITDA by segment", linha DTC; inclui a
    # WarnerMedia apenas a partir de 08/04/2022). De 2023 em diante, XBRL do segmento "Streaming" (10-K FY2025).
    cik = PARES['WBD']
    for f in list_filings(cik, forms=('10-K',), since='2023-01-01'):
        m = re.search(r'Adjusted EBITDA by segment \(in millions\)\. Year Ended December 31, (\d{4}) \d{4} % Change .*? '
                      r'DTC (\([\d,]+\)|[\d,]+)', texto_10k('WBD', cik, f))
        if m:
            out.append({'empresa': 'Warner Bros. Discovery (Max/HBO Max)', 'ano_fiscal': int(m.group(1)),
                        'metrica': 'Adjusted EBITDA do segmento DTC/Streaming', 'valor_usd_mi': num(m.group(2)),
                        'fonte': f"10-K WBD {f['acc']} (MD&A)", 'filed': f['filed']})
    for f in list_filings(cik, forms=('10-K',), since='2023-01-01'):
        base = os.path.join(DADOS, 'pares', 'WBD', f['acc'])
        idx = json.loads(get_cached(filing_url(cik, f['acc'], 'index.json'), os.path.join(base, 'index.json')))
        inst = next(i['name'] for i in idx['directory']['item'] if i['name'].endswith('_htm.xml'))
        get_cached(filing_url(cik, f['acc'], inst), os.path.join(base, inst), binary=True)
        df = parse_instance(os.path.join(base, inst))
        seg = df[df['dims'].str.contains(r'StatementBusinessSegmentsAxis=(?:DirectToConsumer|Streaming)Member', regex=True)
                 & ~df['dims'].str.contains('ProductOrServiceAxis') & df['start'].notna()]
        for conceito, metrica in [('TotalAdjustedEBITDA', 'Adjusted EBITDA do segmento DTC/Streaming'),
                                  ('SegmentReportingInformationOperatingIncomeLoss', 'Adjusted EBITDA do segmento DTC/Streaming')]:
            s = seg[seg['concept'] == conceito]
            s = s[(pd.to_datetime(s['end']) - pd.to_datetime(s['start'])).dt.days > 350]
            for _, r in s.drop_duplicates('end').iterrows():
                out.append({'empresa': 'Warner Bros. Discovery (Max/HBO Max)', 'ano_fiscal': int(r['end'][:4]),
                            'metrica': metrica, 'valor_usd_mi': r['val'] / 1e6, 'fonte': f"10-K WBD {f['acc']} (XBRL)",
                            'filed': f['filed']})
    df = pd.DataFrame(out).sort_values('filed')
    # Mantém a versão mais recente de cada ano (reapresentações por mudança de definição de segmento)
    df = df.drop_duplicates(['empresa', 'ano_fiscal'], keep='last').drop(columns=['filed'])
    notas = {('Disney (Disney+, Hulu)', 2020): 'Definição antiga do segmento (incluía ESPN+); não reapresentada',
             ('Warner Bros. Discovery (Max/HBO Max)', 2022): 'Inclui WarnerMedia (HBO Max) só a partir de 08/04/2022 (fusão)',
             ('Paramount (Paramount+, Pluto TV)', 2024): 'Último 10-K da Paramount Global antes da fusão com a Skydance (ago/2025)'}
    df['nota'] = [notas.get((e, a), '') for e, a in zip(df['empresa'], df['ano_fiscal'])]
    return df.sort_values(['empresa', 'ano_fiscal'])


def main():
    m = macro()
    ultimo = pd.read_csv(os.path.join(SAIDA, 'base_trimestral_nflx.csv'), index_col=0).index[-1]
    m = m.loc[:ultimo]
    m.round(4).to_csv(os.path.join(SAIDA, 'macro_trimestral.csv'), encoding='utf-8-sig')
    s = setor_anual()
    s.round(2).to_csv(os.path.join(SAIDA, 'setor_anual.csv'), index=False, encoding='utf-8-sig')
    st = streaming_concorrentes()
    st.to_csv(os.path.join(SAIDA, 'streaming_concorrentes.csv'), index=False, encoding='utf-8-sig')
    pd.set_option('display.width', 250, 'display.max_rows', 200)
    print(m.round(2).to_string())
    print(s.round(1).to_string(index=False))
    print(st.to_string(index=False))


if __name__ == '__main__':
    main()
