"""Leitura das instâncias XBRL dos 10-Q/10-K: devolve todos os fatos numéricos sem dimensão."""
import json
import os
import xml.etree.ElementTree as ET

import pandas as pd

from sec_common import DADOS

XBRLI = '{http://www.xbrl.org/2003/instance}'
XBRLDI = '{http://xbrl.org/2006/xbrldi}'


def parse_instance(path: str) -> pd.DataFrame:
    """Fatos numéricos da instância. `dims` vem vazio no consolidado e como 'Eixo=Membro' nos detalhamentos."""
    root = ET.parse(path).getroot()
    contexts = {}
    for ctx in root.iter(f'{XBRLI}context'):
        if ctx.find(f'.//{XBRLDI}typedMember') is not None:
            continue
        members = sorted(f"{m.get('dimension').split(':')[-1]}={m.text.strip().split(':')[-1]}"
                         for m in ctx.iter(f'{XBRLDI}explicitMember'))
        dims = ';'.join(members)
        per = ctx.find(f'{XBRLI}period')
        inst = per.find(f'{XBRLI}instant')
        if inst is not None:
            contexts[ctx.get('id')] = (None, inst.text.strip(), dims)
        else:
            contexts[ctx.get('id')] = (per.find(f'{XBRLI}startDate').text.strip(),
                                       per.find(f'{XBRLI}endDate').text.strip(), dims)
    rows = []
    for el in root:
        ref = el.get('contextRef')
        if ref not in contexts or el.get('unitRef') is None or el.text is None:
            continue
        ns, local = el.tag[1:].split('}')
        prefix = 'us-gaap' if 'fasb.org/us-gaap' in ns else ('nflx' if 'netflix' in ns else ns.rsplit('/', 1)[-1])
        try:
            val = float(el.text.strip())
        except ValueError:
            continue
        start, end, dims = contexts[ref]
        rows.append((prefix, local, start, end, dims, val, el.get('unitRef')))
    df = pd.DataFrame(rows, columns=['ns', 'concept', 'start', 'end', 'dims', 'val', 'unit'])
    return df.drop_duplicates()


def all_facts() -> pd.DataFrame:
    """Fatos de todos os relatórios em cache, com forma, data de arquivamento e período do relatório."""
    cache = os.path.join(DADOS, 'fatos_xbrl.csv')
    manifest = json.load(open(os.path.join(DADOS, 'manifest_filings.json')))
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(os.path.join(DADOS, 'manifest_filings.json')):
        return pd.read_csv(cache, keep_default_na=False, na_values={'start': [''], 'val': ['']})
    frames = []
    for f in manifest:
        df = parse_instance(os.path.join(DADOS, 'filings', f['acc'], f['instance']))
        df['form'], df['filed'], df['report'], df['acc'] = f['form'], f['filed'], f['report'], f['acc']
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(cache, index=False)
    return out
