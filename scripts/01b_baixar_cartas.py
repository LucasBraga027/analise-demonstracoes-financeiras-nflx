"""
Etapa 1b - Baixa as cartas trimestrais aos acionistas (Exhibit 99.1 dos 8-K de resultados, item 2.02),
arquivadas oficialmente na SEC. Servem de fonte primária para explicar as variações de cada trimestre.
"""
import json
import os

from sec_common import CIK_NFLX, DADOS, filing_url, get_cached, submissions


def main():
    sub = submissions()
    blocks = [sub['filings']['recent']] + [json.load(open(os.path.join(DADOS, x['name']))) for x in sub['filings'].get('files', [])]
    cartas = []
    for f in blocks:
        for i, form in enumerate(f['form']):
            if form == '8-K' and '2.02' in f['items'][i] and f['filingDate'][i] >= '2019-04-01':
                acc = f['accessionNumber'][i]
                base = os.path.join(DADOS, 'cartas', acc)
                idx = json.loads(get_cached(filing_url(CIK_NFLX, acc, 'index.json'), os.path.join(base, 'index.json')))
                ex = [it['name'] for it in idx['directory']['item']
                      if it['name'].lower().endswith(('.htm', '.html')) and ('ex99' in it['name'].lower() or 'ex-99' in it['name'].lower())]
                for name in ex:
                    get_cached(filing_url(CIK_NFLX, acc, name), os.path.join(base, name), binary=True)
                cartas.append({'filed': f['filingDate'][i], 'acc': acc, 'exhibits': ex})
                print(f['filingDate'][i], acc, ex)
    with open(os.path.join(DADOS, 'manifest_cartas.json'), 'w') as fh:
        json.dump(sorted(cartas, key=lambda c: c['filed']), fh, indent=1)


if __name__ == '__main__':
    main()
