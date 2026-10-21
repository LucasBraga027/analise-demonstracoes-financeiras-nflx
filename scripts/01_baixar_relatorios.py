"""
Etapa 1 - Baixa da SEC EDGAR (fonte oficial) todos os 10-Q e 10-K da Netflix desde 2019:
  * o documento principal (HTML, usado para validar textos do MD&A e notas explicativas);
  * a instância XBRL completa, que inclui as contas próprias da Netflix (ex.: ativos de conteúdo),
    ausentes da API resumida `companyfacts`.
Tudo fica em cache em dados_sec/filings/<accession>/.
"""
import json
import os

from sec_common import CIK_NFLX, DADOS, company_facts, filing_url, get_cached, list_filings


def instance_name(items):
    names = [i['name'] for i in items]
    # Inline XBRL (2019+) gera <doc>_htm.xml; filings antigos trazem <ticker>-<data>.xml
    for n in names:
        if n.endswith('_htm.xml'):
            return n
    for n in names:
        if n.endswith('.xml') and not any(n.endswith(s) for s in ('_cal.xml', '_def.xml', '_lab.xml', '_pre.xml')) \
                and n != 'FilingSummary.xml':
            return n
    raise ValueError(f'instância XBRL não encontrada: {names}')


def main():
    company_facts()
    filings = list_filings(CIK_NFLX, since='2019-04-01')
    manifest = []
    for f in filings:
        base = os.path.join(DADOS, 'filings', f['acc'])
        idx = json.loads(get_cached(filing_url(CIK_NFLX, f['acc'], 'index.json'), os.path.join(base, 'index.json')))
        inst = instance_name(idx['directory']['item'])
        get_cached(filing_url(CIK_NFLX, f['acc'], inst), os.path.join(base, inst), binary=True)
        get_cached(filing_url(CIK_NFLX, f['acc'], f['doc']), os.path.join(base, f['doc']), binary=True)
        manifest.append({**f, 'instance': inst})
        print(f"{f['form']:5} {f['report']}  {f['acc']}  {inst}")
    with open(os.path.join(DADOS, 'manifest_filings.json'), 'w') as fh:
        json.dump(manifest, fh, indent=1)
    print(f'-> {len(manifest)} relatórios em cache.')


if __name__ == '__main__':
    main()
