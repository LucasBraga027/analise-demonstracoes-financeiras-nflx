"""Funções comuns de acesso à SEC EDGAR (cache local em dados_sec/)."""
import json
import os
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(ROOT, 'dados_sec')
SEC_HEADERS = {'User-Agent': 'UFJF-ECO057 Analise Academica (analise_financeira_academica@instituicao.edu)'}
CIK_NFLX = '0001065280'


def get_cached(url: str, path: str, binary: bool = False):
    """Baixa `url` uma única vez e guarda em `path` (respeitando o limite de 10 req/s da SEC)."""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        r = requests.get(url, headers=SEC_HEADERS, timeout=90)
        r.raise_for_status()
        with open(path, 'wb') as f:
            f.write(r.content)
        time.sleep(0.15)
    with open(path, 'rb') as f:
        content = f.read()
    return content if binary else content.decode('utf-8', errors='replace')


def company_facts(cik: str = CIK_NFLX) -> dict:
    url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json'
    return json.loads(get_cached(url, os.path.join(DADOS, f'companyfacts_{cik}.json')))


def submissions(cik: str = CIK_NFLX) -> dict:
    url = f'https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json'
    return json.loads(get_cached(url, os.path.join(DADOS, f'submissions_{cik}.json')))


def list_filings(cik: str, forms=('10-Q', '10-K'), since='2020-01-01'):
    """Lista os relatórios periódicos (sem emendas) arquivados a partir de `since`."""
    sub = submissions(cik)
    blocks = [sub['filings']['recent']]
    # Filings mais antigos ficam em arquivos paginados (CIK...-submissions-001.json etc.)
    for extra in sub['filings'].get('files', []):
        url = f'https://data.sec.gov/submissions/{extra["name"]}'
        blocks.append(json.loads(get_cached(url, os.path.join(DADOS, extra['name']))))
    out = []
    for f in blocks:
        for i, form in enumerate(f['form']):
            if form in forms and f['filingDate'][i] >= since:
                out.append({'form': form, 'filed': f['filingDate'][i], 'report': f['reportDate'][i],
                            'acc': f['accessionNumber'][i], 'doc': f['primaryDocument'][i]})
    return sorted(out, key=lambda x: x['report'])


def filing_url(cik: str, acc: str, name: str) -> str:
    return f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-", "")}/{name}'
