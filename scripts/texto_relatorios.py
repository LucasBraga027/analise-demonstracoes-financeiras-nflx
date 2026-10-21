"""Busca trechos no texto oficial (MD&A e notas) dos 10-Q/10-K em cache, para fundamentar as explicações."""
import html
import json
import os
import re
import sys

from sec_common import DADOS


def filing_text(ref: str) -> tuple[dict, str]:
    """`ref` = data do período de um 10-Q/10-K (ex.: 2024-03-31) ou código de carta aos acionistas (ex.: q124)."""
    if re.fullmatch(r'q\d{3}', ref):
        cartas = json.load(open(os.path.join(DADOS, 'manifest_cartas.json')))
        c = next(c for c in cartas for e in c['exhibits'] if ref in e.replace('_', ''))
        f = {'form': 'Carta aos acionistas (8-K, Ex. 99.1)', 'report': ref, 'acc': c['acc'], 'doc': c['exhibits'][0]}
        path = os.path.join(DADOS, 'cartas', c['acc'], c['exhibits'][0])
    else:
        manifest = json.load(open(os.path.join(DADOS, 'manifest_filings.json')))
        f = next(m for m in manifest if m['report'] == ref)
        path = os.path.join(DADOS, 'filings', f['acc'], f['doc'])
    return f, html_to_text(open(path, encoding='utf-8', errors='replace').read())


def html_to_text(raw: str) -> str:
    raw = re.sub(r'(?is)<(script|style|ix:header).*?</\1>', ' ', raw)
    txt = html.unescape(re.sub(r'<[^>]+>', ' ', raw))
    return re.sub(r'\s+', ' ', txt.replace('\xa0', ' '))


def search(report_date: str, pattern: str, width: int = 350, limit: int = 4):
    f, txt = filing_text(report_date)
    hits = []
    for m in re.finditer(pattern, txt, flags=re.I):
        hits.append(txt[max(0, m.start() - width): m.end() + width])
        if len(hits) >= limit:
            break
    return f, hits


if __name__ == '__main__':
    f, hits = search(sys.argv[1], sys.argv[2], limit=int(sys.argv[3]) if len(sys.argv) > 3 else 4)
    print(f"== {f['form']} {f['report']} ({f['acc']}) ==")
    for h in hits:
        print('...', h, '...\n')
