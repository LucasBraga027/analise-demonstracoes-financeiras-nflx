"""
Etapa 2 - Monta a base trimestral da Netflix (2019T1 até o último 10-Q) a partir das instâncias XBRL
oficiais e valida cada número. Diferenças em relação à versão original (adf_nflx_vs_dis.py):
  * Nenhum valor é inventado: não há bfill/ffill nem "custo = 52% da receita". Lacuna vira vazio e é reportada.
  * Q4 = 10-K (ano) - 9 meses acumulados do 10-Q; Q2 e Q3 da DFC = acumulado do período - acumulado anterior.
  * Sinal do imposto preservado (benefício fiscal aparece como negativo).
  * Contas próprias da Netflix incluídas: ativos e passivos de conteúdo, gasto de caixa e amortização de conteúdo.
  * Aplicações financeiras de curto prazo separadas do capital de giro operacional (Fleuriet).
Saídas (US$ milhões): dados/base_trimestral_nflx.csv, dados/regioes_nflx.csv e dados/validacao_base.md
"""
import os

import numpy as np
import pandas as pd

from sec_common import ROOT, company_facts
from xbrl_parser import all_facts

SAIDA = os.path.join(ROOT, 'dados')
ANO_INICIAL = 2019

# Conta -> conceitos XBRL em ordem de preferência (o primeiro com valor no período vence)
FLUXOS = {
    'receita': ['us-gaap:Revenues'],
    'custo_servicos': ['us-gaap:CostOfRevenue'],
    'marketing': ['us-gaap:SellingAndMarketingExpense', 'us-gaap:MarketingExpense'],
    # Até 2021 a linha da DRE é "Technology and development"; o P&D de 2019 citado nas notas é outro número
    'tecnologia': ['nflx:TechnologyandDevelopmentExpense', 'us-gaap:ResearchAndDevelopmentExpense'],
    'gerais_admin': ['us-gaap:GeneralAndAdministrativeExpense'],
    'ebit': ['us-gaap:OperatingIncomeLoss'],
    'despesa_juros': ['us-gaap:InterestExpenseNonoperating', 'us-gaap:InterestExpense'],
    'outras_rec_desp_fin': ['us-gaap:NonoperatingIncomeExpense'],
    'ganho_perda_cambial': ['us-gaap:ForeignCurrencyTransactionGainLossBeforeTax'],
    'lair': ['us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
             'us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments'],
    'ir_csll': ['us-gaap:IncomeTaxExpenseBenefit'],
    'lucro_liquido': ['us-gaap:NetIncomeLoss'],
    'amort_conteudo': ['nflx:CostofServicesAmortizationofStreamingContentAssets'],
    'gasto_caixa_conteudo': ['nflx:AdditionstoStreamingContentAssets'],
    'depreciacao_amort': ['us-gaap:DepreciationDepletionAndAmortization'],
    'remuneracao_acoes': ['us-gaap:ShareBasedCompensation'],
    'fco': ['us-gaap:NetCashProvidedByUsedInOperatingActivities'],
    'capex': ['us-gaap:PaymentsToAcquirePropertyPlantAndEquipment'],
    'fci': ['us-gaap:NetCashProvidedByUsedInInvestingActivities'],
    'fcf_financiamento': ['us-gaap:NetCashProvidedByUsedInFinancingActivities'],
    'recompra_acoes': ['us-gaap:PaymentsForRepurchaseOfCommonStock'],
}
SALDOS = {
    'caixa': ['us-gaap:CashAndCashEquivalentsAtCarryingValue'],
    'aplicacoes_cp': ['us-gaap:ShortTermInvestments'],
    'outros_ativos_circ': ['us-gaap:OtherAssetsCurrent', 'nflx:OtherCurrentAssets'],
    'ativo_circulante': ['us-gaap:AssetsCurrent'],
    'ativos_conteudo': ['nflx:ContentAssetsNetNoncurrent', 'nflx:ContentAssetsNet'],
    'imobilizado': ['us-gaap:PropertyPlantAndEquipmentNet'],
    'ativo_total': ['us-gaap:Assets'],
    'passivo_conteudo_cp': ['nflx:ContentLiabilitiesCurrent'],
    'fornecedores': ['us-gaap:AccountsPayableCurrent'],
    'contas_a_pagar_provisoes': ['us-gaap:AccruedLiabilitiesCurrent'],
    'receita_diferida': ['us-gaap:ContractWithCustomerLiabilityCurrent'],
    'divida_cp': ['us-gaap:ShortTermBorrowings'],
    'passivo_circulante': ['us-gaap:LiabilitiesCurrent'],
    'passivo_conteudo_lp': ['nflx:ContentLiabilitiesNoncurrent'],
    'divida_lp': ['us-gaap:LongTermDebtNoncurrent'],
    'outros_passivos_lp': ['us-gaap:OtherLiabilitiesNoncurrent'],
    'passivo_total': ['us-gaap:Liabilities'],
    'patrimonio_liquido': ['us-gaap:StockholdersEquity'],
    'passivo_mais_pl': ['us-gaap:LiabilitiesAndStockholdersEquity'],
}
# Contas que a Netflix simplesmente não tinha em parte do período (zero legítimo, verificado pela soma do AC/PC;
# recompras só começaram com o programa autorizado em mar/2021)
ZERO_SE_AUSENTE = {'aplicacoes_cp', 'divida_cp', 'recompra_acoes'}
REGIOES = {'UnitedStatesAndCanadaMember': 'EUA_Canada', 'EMEAMember': 'EMEA',
           'LatinAmericaMember': 'America_Latina', 'AsiaPacificMember': 'Asia_Pacifico'}


def quarters(last_end: str):
    out = []
    for y in range(ANO_INICIAL, int(last_end[:4]) + 1):
        for q, (ms, me) in enumerate([('01-01', '03-31'), ('04-01', '06-30'), ('07-01', '09-30'), ('10-01', '12-31')], 1):
            if f'{y}-{me}' <= last_end:
                out.append((f'{y}T{q}', f'{y}-{ms}', f'{y}-{me}', f'{y}-01-01'))
    return out


def latest(df: pd.DataFrame):
    """Valor do relatório arquivado mais recentemente (incorpora reapresentações)."""
    return df.sort_values('filed').iloc[-1]['val'] if not df.empty else np.nan


def serie_fluxo(f: pd.DataFrame, qs) -> tuple[pd.Series, dict]:
    origem, vals = {}, {}
    for label, start, end, jan1 in qs:
        v = latest(f[(f['start'] == start) & (f['end'] == end)])
        how = '3M'
        if np.isnan(v) and start != jan1:
            ytd = latest(f[(f['start'] == jan1) & (f['end'] == end)])
            prev_end = (pd.Timestamp(start) - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            ytd_prev = latest(f[(f['start'] == jan1) & (f['end'] == prev_end)])
            v = ytd - ytd_prev
            how = 'acumulado - acumulado anterior'
        vals[label], origem[label] = v, (how if not np.isnan(v) else 'ausente')
    return pd.Series(vals), origem


def serie_saldo(f: pd.DataFrame, qs) -> pd.Series:
    return pd.Series({label: latest(f[f['end'] == end]) for label, _, end, _ in qs})


def build(facts: pd.DataFrame):
    consol = facts[(facts['dims'] == '') & (facts['unit'] == 'usd')]
    consol = consol.assign(key=consol['ns'] + ':' + consol['concept'])
    last_end = facts['report'].max()
    qs = quarters(last_end)
    base, log = {}, []
    for conta, tags in FLUXOS.items():
        # Une as tags por período antes de derivar trimestres: a mesma linha da DRE pode mudar de tag
        # entre o 10-Q e o 10-K (ex.: 2019, "Technology and development" x "ResearchAndDevelopment")
        pool = consol[consol['key'].isin(tags) & consol['start'].notna()].copy()
        pool['prio'] = pool['key'].map({t: i for i, t in enumerate(tags)})
        pool = pool.sort_values('prio').drop_duplicates(['start', 'end', 'filed'])
        pool = pool[pool['prio'] == pool.groupby(['start', 'end'])['prio'].transform('min')]
        s, origem = serie_fluxo(pool, qs)
        log += [(conta, '|'.join(tags), q, o) for q, o in origem.items()]
        if conta in ZERO_SE_AUSENTE:
            s = s.fillna(0.0)
        base[conta] = s
    for conta, tags in SALDOS.items():
        s = pd.Series(np.nan, index=[q[0] for q in qs])
        for tag in tags:
            s = s.combine_first(serie_saldo(consol[(consol['key'] == tag) & consol['start'].isna()], qs))
        if conta in ZERO_SE_AUSENTE:
            s = s.fillna(0.0)
        base[conta] = s
    df = pd.DataFrame(base) / 1e6
    df.index.name = 'trimestre'

    # Detalhamento por região: receita (US$ mi) e assinantes pagos (milhões; divulgados até 2024T4)
    reg = {}
    for membro, nome in REGIOES.items():
        r = facts[(facts['concept'] == 'Revenues') & facts['dims'].str.endswith(f'StatementGeographicalAxis={membro}')
                  & facts['dims'].str.contains('StreamingMember')]
        reg[f'receita_{nome}'] = serie_fluxo(r, qs)[0] / 1e6
        m = facts[(facts['concept'] == 'NumberOfPaidMemberships') & facts['dims'].str.endswith(f'StatementGeographicalAxis={membro}')]
        reg[f'assinantes_{nome}'] = serie_saldo(m, qs) / 1e6
    regioes = pd.DataFrame(reg)
    # DVD (encerrado em set/2023) = total - streaming; o 10-K só traz o DVD anual arredondado (ex.: "0,3 bi").
    # A conferência com os trimestres em que o 10-Q traz o valor exato fica na validação.
    regioes['receita_DVD'] = (df['receita'] - regioes[[c for c in regioes if c.startswith('receita_')]].sum(axis=1)).round(3)
    regioes['assinantes_total'] = regioes[[c for c in regioes if c.startswith('assinantes_')]].sum(axis=1, min_count=4)
    regioes.index.name = 'trimestre'
    return df, regioes, pd.DataFrame(log, columns=['conta', 'tag', 'trimestre', 'metodo'])


def validar(df: pd.DataFrame, regioes: pd.DataFrame, facts_global: pd.DataFrame) -> list[str]:
    linhas = ['# Validação da base trimestral (gerado por scripts/02_base_trimestral.py)', '']
    tol = 1.0  # US$ 1 milhão (arredondamentos)

    def check(nome, calc, real):
        dif = (calc - real).abs()
        ruins = dif[dif > tol]
        status = 'OK' if ruins.empty else f'**{len(ruins)} divergência(s)**: ' + ', '.join(f'{i} ({d:,.1f})' for i, d in ruins.items())
        linhas.append(f'- {nome}: {status} (maior diferença {dif.max():,.2f} US$ mi)')

    linhas.append('## 1. Identidades contábeis')
    check('Ativo = Passivo + PL', df['passivo_total'] + df['patrimonio_liquido'], df['ativo_total'])
    check('Passivo + PL informado = Ativo', df['passivo_mais_pl'], df['ativo_total'])
    check('EBIT = Receita - Custos - Marketing - Tecnologia - G&A',
          df['receita'] - df['custo_servicos'] - df['marketing'] - df['tecnologia'] - df['gerais_admin'], df['ebit'])
    check('LAIR = EBIT - Juros + Outras receitas/despesas financeiras',
          df['ebit'] - df['despesa_juros'] + df['outras_rec_desp_fin'], df['lair'])
    check('Lucro líquido = LAIR - IR', df['lair'] - df['ir_csll'], df['lucro_liquido'])
    check('AC = Caixa + Aplicações CP + Outros AC', df['caixa'] + df['aplicacoes_cp'] + df['outros_ativos_circ'], df['ativo_circulante'])
    check('PC = Passivo conteúdo CP + Fornecedores + Provisões + Receita diferida + Dívida CP',
          df[['passivo_conteudo_cp', 'fornecedores', 'contas_a_pagar_provisoes', 'receita_diferida', 'divida_cp']].sum(axis=1),
          df['passivo_circulante'])
    dvd = facts_global[(facts_global['concept'] == 'Revenues') & (facts_global['dims'] == 'ProductOrServiceAxis=DVDMember')]
    dvd = dvd[(pd.to_datetime(dvd['end']) - pd.to_datetime(dvd['start'])).dt.days.between(80, 100)]
    dvd_rep = {q: dvd[dvd['end'] == e].sort_values('filed')['val'].iloc[-1] / 1e6
               for q, _, e, _ in quarters(df.index[-1][:4] + '-12-31') if q in df.index and not dvd[dvd['end'] == e].empty}
    check('Receita DVD (total - 4 regiões de streaming) = DVD informado no 10-Q', regioes['receita_DVD'].loc[list(dvd_rep)], pd.Series(dvd_rep))
    neg = regioes['receita_DVD'][regioes['receita_DVD'] < -tol]
    linhas.append(f'- Receita DVD nunca negativa e zerada após 2023T3: {"OK" if neg.empty and (regioes.loc["2023T4":, "receita_DVD"].abs() < tol).all() else "verificar"}')

    linhas += ['', '## 2. Conferência cruzada com a API companyfacts da SEC (fonte independente do XBRL bruto)']
    cf = company_facts()['facts']['us-gaap']
    for conta, tag in [('receita', 'Revenues'), ('lucro_liquido', 'NetIncomeLoss'), ('ativo_total', 'Assets'),
                       ('fco', 'NetCashProvidedByUsedInOperatingActivities'), ('patrimonio_liquido', 'StockholdersEquity')]:
        api = pd.DataFrame(cf[tag]['units']['USD'])
        api = api[api['form'].isin(['10-K', '10-Q'])]
        if conta in ('ativo_total', 'patrimonio_liquido'):
            ref = {q: api[api['end'] == f'{q[:4]}-{["03-31","06-30","09-30","12-31"][int(q[-1])-1]}']['val'].iloc[-1] / 1e6
                   for q in df.index if not api[api['end'] == f'{q[:4]}-{["03-31","06-30","09-30","12-31"][int(q[-1])-1]}'].empty}
            check(f'{conta} (saldos trimestrais)', df[conta].loc[list(ref)], pd.Series(ref))
        else:
            fy = api[(pd.to_datetime(api['end']) - pd.to_datetime(api['start'])).dt.days > 350]
            fy = fy[fy['end'].str.endswith('12-31')].sort_values('filed').drop_duplicates('end', keep='last')
            ref = pd.Series({e[:4]: v / 1e6 for e, v in zip(fy['end'], fy['val'])})
            soma = df[conta].groupby(df.index.str[:4]).sum(min_count=4)
            comum = ref.index.intersection(soma.dropna().index)
            check(f'{conta} (soma dos 4 trimestres = ano do 10-K)', soma.loc[comum], ref.loc[comum])

    linhas += ['', '## 3. Lacunas (valores não divulgados — mantidos vazios, sem preenchimento artificial)']
    lac = df.isna().sum()
    lac = lac[lac > 0]
    linhas += [f'- {c}: {n} trimestre(s) sem dado ({", ".join(df.index[df[c].isna()])})' for c, n in lac.items()] or ['- Nenhuma lacuna.']
    linhas.append('- Assinantes pagos por região: a Netflix deixou de divulgar a partir de 2025T1 (decisão anunciada na carta aos '
                  'acionistas do 1º tri/2024). Último dado avulso: "325 milhões de assinantes pagos" citado na carta do 4º tri/2025.')
    return linhas


def main():
    os.makedirs(SAIDA, exist_ok=True)
    facts = all_facts()
    df, regioes, log = build(facts)
    df.round(3).to_csv(os.path.join(SAIDA, 'base_trimestral_nflx.csv'), encoding='utf-8-sig')
    regioes.round(3).to_csv(os.path.join(SAIDA, 'regioes_nflx.csv'), encoding='utf-8-sig')
    log.to_csv(os.path.join(SAIDA, 'origem_dos_dados.csv'), index=False, encoding='utf-8-sig')
    linhas = validar(df, regioes, facts)
    with open(os.path.join(SAIDA, 'validacao_base.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(linhas) + '\n')
    print('\n'.join(linhas))
    print(f'\n-> Base: {len(df)} trimestres ({df.index[0]} a {df.index[-1]}), {df.shape[1]} contas.')


if __name__ == '__main__':
    main()
