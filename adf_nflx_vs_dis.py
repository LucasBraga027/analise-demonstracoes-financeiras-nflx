# ==============================================================================
# ANÁLISE DAS DEMONSTRAÇÕES FINANCEIRAS TRIMESTRAIS (ADF): NETFLIX, INC. (NFLX)
# Coleta Primária via API REST Oficial da SEC EDGAR (Form 10-Q e 10-K JSON XBRL)
# Período Histórico Trimestral: 2020Q1 até o Último Trimestre Disponível (2026Q2)
# ==============================================================================

import requests
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os

warnings.filterwarnings('ignore')

# ------------------------------------------------------------------------------
# 1. SETUP E INGESTÃO TRIMESTRAL DA SEC EDGAR
# ------------------------------------------------------------------------------
print("=" * 85)
print("1. INGESTÃO OFICIAL SEC EDGAR - SÉRIES TRIMESTRAIS NETFLIX (2020Q1 até o mais recente)")
print("=" * 85)

SEC_HEADERS = {
    'User-Agent': 'UniversidadeEstadual/1.0 (analise_financeira_academica@instituicao.edu)'
}

CIK_NFLX = '0001065280'

def fetch_sec_companyfacts(cik: str, headers: dict) -> dict:
    cik_pad = str(cik).zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_pad}.json"
    print(f"-> Conectando à SEC EDGAR para CIK {cik_pad} (Netflix, Inc.)...")
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    entity = data.get('entityName', 'Netflix, Inc.')
    total_tags = len(data.get('facts', {}).get('us-gaap', {}))
    print(f"   [Status 200 OK] {entity}: {total_tags} tags US-GAAP disponíveis.")
    return data

nflx_raw = fetch_sec_companyfacts(CIK_NFLX, SEC_HEADERS)

def extract_quarterly_tag(facts_data: dict, candidate_tags: list, is_duration: bool = True) -> pd.Series:
    """Extrai valores trimestrais (Q1, Q2, Q3, Q4) a partir de 2020 até o último trimestre disponível."""
    gaap = facts_data.get('facts', {}).get('us-gaap', {})
    
    tag_records = None
    for tag in candidate_tags:
        if tag in gaap and 'USD' in gaap[tag].get('units', {}):
            tag_records = gaap[tag]['units']['USD']
            if tag_records:
                break
                
    if not tag_records:
        return pd.Series(dtype=float)
        
    df_raw = pd.DataFrame(tag_records)
    if 'end' not in df_raw.columns:
        return pd.Series(dtype=float)
        
    df_raw['end_dt'] = pd.to_datetime(df_raw['end'], errors='coerce')
    df_raw = df_raw.dropna(subset=['end_dt'])
    
    max_year = df_raw['end_dt'].dt.year.max()
    
    if not is_duration:
        # Posição Patrimonial (Balanço): saldo ao final de cada trimestre
        records = []
        for year in range(2020, max_year + 1):
            q_dates = {
                f"{year}Q1": f"{year}-03-31",
                f"{year}Q2": f"{year}-06-30",
                f"{year}Q3": f"{year}-09-30",
                f"{year}Q4": f"{year}-12-31",
            }
            for q_label, target_date in q_dates.items():
                target_dt = pd.to_datetime(target_date)
                mask = (df_raw['end_dt'] >= target_dt - pd.Timedelta(days=5)) & \
                       (df_raw['end_dt'] <= target_dt + pd.Timedelta(days=5))
                sub = df_raw[mask]
                if not sub.empty:
                    latest = sub.sort_values(by='filed').iloc[-1]
                    records.append({'period': q_label, 'val': latest['val']})
                    
        if not records:
            return pd.Series(dtype=float)
        s = pd.DataFrame(records).drop_duplicates('period').set_index('period')['val']
        return s.ffill().bfill()
        
    else:
        # Duração (DRE e DFC): 3 meses discretos
        if 'start' not in df_raw.columns:
            return pd.Series(dtype=float)
        df_raw['start_dt'] = pd.to_datetime(df_raw['start'], errors='coerce')
        df_raw['days'] = (df_raw['end_dt'] - df_raw['start_dt']).dt.days
        
        q_results = {}
        for year in range(2020, max_year + 1):
            # Q1 (3M terminando em 31/03)
            sub_q1 = df_raw[(df_raw['end_dt'].dt.year == year) & 
                            (df_raw['end_dt'].dt.month.isin([3, 4])) & 
                            (df_raw['days'].between(75, 105))]
            v_q1 = sub_q1.sort_values(by='filed').iloc[-1]['val'] if not sub_q1.empty else np.nan
            
            # Q2 (3M terminando em 30/06)
            sub_q2 = df_raw[(df_raw['end_dt'].dt.year == year) & 
                            (df_raw['end_dt'].dt.month.isin([6, 7])) & 
                            (df_raw['days'].between(75, 105))]
            if not sub_q2.empty:
                v_q2 = sub_q2.sort_values(by='filed').iloc[-1]['val']
            else:
                sub_6m = df_raw[(df_raw['end_dt'].dt.year == year) & 
                                (df_raw['end_dt'].dt.month.isin([6, 7])) & 
                                (df_raw['days'].between(170, 195))]
                v_6m = sub_6m.sort_values(by='filed').iloc[-1]['val'] if not sub_6m.empty else np.nan
                v_q2 = v_6m - v_q1 if pd.notna(v_6m) and pd.notna(v_q1) else np.nan
                
            # Q3 (3M terminando em 30/09)
            sub_q3 = df_raw[(df_raw['end_dt'].dt.year == year) & 
                            (df_raw['end_dt'].dt.month.isin([9, 10])) & 
                            (df_raw['days'].between(75, 105))]
            if not sub_q3.empty:
                v_q3 = sub_q3.sort_values(by='filed').iloc[-1]['val']
            else:
                sub_9m = df_raw[(df_raw['end_dt'].dt.year == year) & 
                                (df_raw['end_dt'].dt.month.isin([9, 10])) & 
                                (df_raw['days'].between(260, 285))]
                v_9m = sub_9m.sort_values(by='filed').iloc[-1]['val'] if not sub_9m.empty else np.nan
                v_q3 = v_9m - (v_q1 + v_q2) if pd.notna(v_9m) and pd.notna(v_q1) and pd.notna(v_q2) else np.nan

            # Q4 (3M terminando em 31/12 ou deduzido de FY - 9M)
            sub_q4 = df_raw[(df_raw['end_dt'].dt.year == year) & 
                            (df_raw['end_dt'].dt.month == 12) & 
                            (df_raw['days'].between(75, 105))]
            if not sub_q4.empty:
                v_q4 = sub_q4.sort_values(by='filed').iloc[-1]['val']
            else:
                sub_fy = df_raw[(df_raw['end_dt'].dt.year == year) & 
                                (df_raw['end_dt'].dt.month == 12) & 
                                (df_raw['days'].between(330, 380))]
                v_fy = sub_fy.sort_values(by='filed').iloc[-1]['val'] if not sub_fy.empty else np.nan
                if pd.notna(v_fy) and pd.notna(v_q1) and pd.notna(v_q2) and pd.notna(v_q3):
                    v_q4 = v_fy - (v_q1 + v_q2 + v_q3)
                else:
                    v_q4 = np.nan
                    
            if pd.notna(v_q1): q_results[f"{year}Q1"] = v_q1
            if pd.notna(v_q2): q_results[f"{year}Q2"] = v_q2
            if pd.notna(v_q3): q_results[f"{year}Q3"] = v_q3
            if pd.notna(v_q4): q_results[f"{year}Q4"] = v_q4
            
        s = pd.Series(q_results)
        return s.bfill().ffill()

def build_quarterly_dataframe(facts_data: dict, company_name: str = 'Netflix') -> pd.DataFrame:
    dre_mapping = {
        'Revenues': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'],
        'CostOfRevenue': ['CostOfRevenue', 'CostOfGoodsAndServicesSold', 'CostsAndExpenses'],
        'OperatingIncome': ['OperatingIncomeLoss'],
        'InterestExpense': ['InterestExpenseNonoperating', 'InterestExpense', 'InterestAndDebtExpense', 'InterestPaidNet'],
        'TaxExpense': ['IncomeTaxExpenseBenefit'],
        'NetIncome': ['NetIncomeLoss']
    }
    bs_mapping = {
        'Assets': ['Assets'],
        'AssetsCurrent': ['AssetsCurrent'],
        'Cash': ['CashAndCashEquivalentsAtCarryingValue'],
        'LiabilitiesCurrent': ['LiabilitiesCurrent'],
        'Liabilities': ['Liabilities'],
        'ShortTermDebt': ['ShortTermBorrowings', 'LongTermDebtCurrent', 'CommercialPaper'],
        'LongTermDebt': ['LongTermDebtNoncurrent', 'LongTermDebt'],
        'Equity': ['StockholdersEquity'],
        'PPE': ['PropertyPlantAndEquipmentNet']
    }
    cf_mapping = {
        'OperatingCashFlow': ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'],
        'Capex': ['PaymentsToAcquirePropertyPlantAndEquipment', 'PaymentsToAcquireProductiveAssets'],
        'Depreciation': ['DepreciationDepletionAndAmortization']
    }
    
    extracted = {}
    for col, tags in dre_mapping.items():
        extracted[col] = extract_quarterly_tag(facts_data, tags, is_duration=True)
    for col, tags in bs_mapping.items():
        extracted[col] = extract_quarterly_tag(facts_data, tags, is_duration=False)
    for col, tags in cf_mapping.items():
        extracted[col] = extract_quarterly_tag(facts_data, tags, is_duration=True)
        
    df = pd.DataFrame(extracted).sort_index()
    
    # Preenchimentos e consistência contábil
    df['CostOfRevenue'] = df['CostOfRevenue'].fillna(df['Revenues'] * 0.52)
    df['GrossProfit'] = df['Revenues'] - df['CostOfRevenue']
        
    if df['Liabilities'].isna().any() or (df['Liabilities'] == 0).any():
        df['Liabilities'] = df['Assets'] - df['Equity']
        
    df['ShortTermDebt'] = df['ShortTermDebt'].fillna(0)
    df['LongTermDebt'] = df['LongTermDebt'].fillna(0)
    df['InterestExpense'] = df['InterestExpense'].fillna(0).abs()
    df['TaxExpense'] = df['TaxExpense'].fillna(0).abs()
    df['Capex'] = df['Capex'].fillna(0).abs()
    df['Depreciation'] = df['Depreciation'].fillna(0).abs()
    df['Company'] = company_name
    return df

df_nflx = build_quarterly_dataframe(nflx_raw, 'Netflix')
print(f"-> Base de dados trimestral construída: {df_nflx.shape[0]} trimestres ({df_nflx.index[0]} a {df_nflx.index[-1]}) e {df_nflx.shape[1]} colunas.")

# Funções para gerar relatórios estruturados
def get_dre(df: pd.DataFrame) -> pd.DataFrame:
    df_b = df.select_dtypes(include='number') / 1e9
    dre_dict = {
        '(=) Receita Operacional Líquida (Revenues)': df_b['Revenues'],
        '(-) Custo dos Bens/Serviços Vendidos (CostOfRevenue)': df_b['CostOfRevenue'],
        '(=) Lucro Bruto (GrossProfit)': df_b['GrossProfit'],
        '(-) Despesas Operacionais (SG&A / Marketing / P&D)': df_b['GrossProfit'] - df_b['OperatingIncome'],
        '(=) Lucro Operacional / EBIT (OperatingIncome)': df_b['OperatingIncome'],
        '(-) Despesas com Juros / Financeiras (InterestExpense)': df_b['InterestExpense'],
        '(-) Provisão Imposto de Renda (TaxExpense)': df_b['TaxExpense'],
        '(=) Lucro Líquido do Trimestre (NetIncome)': df_b['NetIncome']
    }
    return pd.DataFrame(dre_dict, index=df.index).T.round(2)

def get_balanco(df: pd.DataFrame) -> pd.DataFrame:
    df_b = df.select_dtypes(include='number') / 1e9
    bp_dict = {
        '1. ATIVO CIRCULANTE (AssetsCurrent)': df_b['AssetsCurrent'],
        '   - Caixa e Equivalentes (Cash)': df_b['Cash'],
        '   - Outros Ativos Circulantes': df_b['AssetsCurrent'] - df_b['Cash'],
        '2. ATIVO NÃO CIRCULANTE': df_b['Assets'] - df_b['AssetsCurrent'],
        '   - Imobilizado Líquido (PPE)': df_b['PPE'],
        '   - Intangíveis / Conteúdo LP / Outros': (df_b['Assets'] - df_b['AssetsCurrent'] - df_b['PPE']).clip(lower=0),
        '(=) ATIVO TOTAL (Assets)': df_b['Assets'],
        '3. PASSIVO CIRCULANTE (LiabilitiesCurrent)': df_b['LiabilitiesCurrent'],
        '   - Dívida de Curto Prazo (ShortTermDebt)': df_b['ShortTermDebt'],
        '   - Outros Passivos Circulantes': df_b['LiabilitiesCurrent'] - df_b['ShortTermDebt'],
        '4. PASSIVO NÃO CIRCULANTE': df_b['Liabilities'] - df_b['LiabilitiesCurrent'],
        '   - Dívida de Longo Prazo (LongTermDebt)': df_b['LongTermDebt'],
        '   - Outros Passivos LP': (df_b['Liabilities'] - df_b['LiabilitiesCurrent'] - df_b['LongTermDebt']).clip(lower=0),
        '(=) PASSIVO TOTAL (Liabilities)': df_b['Liabilities'],
        '(=) PATRIMÔNIO LÍQUIDO (Equity)': df_b['Equity'],
        '(=) TOTAL PASSIVO + PL (Liabilities + Equity)': df_b['Liabilities'] + df_b['Equity']
    }
    return pd.DataFrame(bp_dict, index=df.index).T.round(2)

def get_dfc(df: pd.DataFrame) -> pd.DataFrame:
    df_b = df.select_dtypes(include='number') / 1e9
    dfc_dict = {
        '(+) Fluxo de Caixa Operacional (FCO / OperatingCashFlow)': df_b['OperatingCashFlow'],
        '(-) Investimentos em Capital / Capex (Payments for PPE)': df_b['Capex'],
        '(+) Depreciação e Amortização (Depreciation)': df_b['Depreciation'],
        '(=) Fluxo de Caixa Livre (FCF = FCO - Capex)': df_b['OperatingCashFlow'] - df_b['Capex']
    }
    return pd.DataFrame(dfc_dict, index=df.index).T.round(2)

def get_dre_av(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna a Análise Vertical (AV) da DRE (% sobre a Receita Líquida) para todos os trimestres."""
    dre = get_dre(df)
    receita = dre.loc['(=) Receita Operacional Líquida (Revenues)']
    return (dre.div(receita, axis=1) * 100).round(2)

def get_balanco_av(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna a Análise Vertical (AV) do Balanço Patrimonial (% sobre o Ativo Total) para todos os trimestres."""
    bp = get_balanco(df)
    ativo_total = bp.loc['(=) ATIVO TOTAL (Assets)']
    return (bp.div(ativo_total, axis=1) * 100).round(2)

def display_separated_statements(df: pd.DataFrame, company_title: str = "Netflix, Inc. (NFLX)", last_n: int = None, show_av: bool = True):
    """Exibe as demonstrações financeiras e a análise vertical de todos os trimestres (ou últimos n)."""
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    
    periodo_str = f"ÚLTIMOS {last_n} TRIMESTRES" if last_n else f"TODOS OS {len(df)} TRIMESTRES ({df.index[0]} a {df.index[-1]})"
    print("=" * 100)
    print(f"DEMONSTRAÇÕES FINANCEIRAS TRIMESTRAIS: {company_title.upper()} - {periodo_str}")
    print("=" * 100)
    
    dre = get_dre(df)
    bp = get_balanco(df)
    dfc = get_dfc(df)
    
    if last_n is not None:
        dre = dre.iloc[:, -last_n:]
        bp = bp.iloc[:, -last_n:]
        dfc = dfc.iloc[:, -last_n:]
    
    print("\n[1] DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO (DRE TRIMESTRAL - US$ BI)")
    print(dre.to_string())
    
    if show_av:
        print("\n[1.1] ANÁLISE VERTICAL DA DRE (% DA RECEITA LÍQUIDA)")
        dre_av = get_dre_av(df)
        if last_n is not None:
            dre_av = dre_av.iloc[:, -last_n:]
        print(dre_av.to_string())
    
    print("\n[2] BALANÇO PATRIMONIAL (BP TRIMESTRAL - US$ BI)")
    print(bp.to_string())
    
    if show_av:
        print("\n[2.1] ANÁLISE VERTICAL DO BALANÇO PATRIMONIAL (% DO ATIVO TOTAL / PASSIVO+PL)")
        bp_av = get_balanco_av(df)
        if last_n is not None:
            bp_av = bp_av.iloc[:, -last_n:]
        print(bp_av.to_string())
    
    print("\n[3] DEMONSTRAÇÃO DO FLUXO DE CAIXA (DFC TRIMESTRAL - US$ BI)")
    print(dfc.to_string())

# Exibição de TODOS os trimestres (Valores e Análise Vertical)
display_separated_statements(df_nflx, "Netflix, Inc. (NFLX)", last_n=None, show_av=True)

# ------------------------------------------------------------------------------
# 2. ANÁLISE VERTICAL (AV) E HORIZONTAL (AH) TRIMESTRAL
# ------------------------------------------------------------------------------
print("\n" + "=" * 100)
print("2. ANÁLISE VERTICAL E HORIZONTAL TRIMESTRAL (SÉRIE COMPLETA)")
print("=" * 100)

colunas_dre = {
    'CostOfRevenue': 'Custo dos Serviços (CostOfRevenue) %',
    'GrossProfit': 'Lucro Bruto (GrossProfit) %',
    'OperatingIncome': 'Lucro Operacional / EBIT (OperatingIncome) %',
    'NetIncome': 'Lucro Líquido (NetIncome) %'
}
colunas_ah = {
    'Revenues': 'Receita Líquida (Revenues) %',
    'GrossProfit': 'Lucro Bruto (GrossProfit) %',
    'OperatingIncome': 'Lucro Operacional / EBIT (OperatingIncome) %',
    'NetIncome': 'Lucro Líquido (NetIncome) %'
}

# AV da DRE (Formato Série Temporal com trimestres nas linhas)
av_dre_nflx = (df_nflx[['CostOfRevenue', 'GrossProfit', 'OperatingIncome', 'NetIncome']]
               .div(df_nflx['Revenues'], axis=0) * 100).round(2).rename(columns=colunas_dre)

# AH Trimestral: QoQ (Variação em relação ao trimestre imediatamente anterior: t vs t-1)
ah_qoq = (df_nflx[['Revenues', 'GrossProfit', 'OperatingIncome', 'NetIncome']]
          .pct_change(1) * 100).round(2).rename(columns=colunas_ah)

# AH Homóloga: YoY (Variação em relação ao mesmo trimestre do ano anterior: t vs t-4)
ah_yoy = (df_nflx[['Revenues', 'GrossProfit', 'OperatingIncome', 'NetIncome']]
          .pct_change(4) * 100).round(2).rename(columns=colunas_ah)

print(f"\nAV DRE Netflix (% da Receita - Todos os {len(df_nflx)} Trimestres de {df_nflx.index[0]} a {df_nflx.index[-1]}):")
print(av_dre_nflx.to_string())

print(f"\nAH QoQ Netflix (% Variação Trimestre Anterior - Todos os Trimestres):")
print("Nota explicativa: 2020Q1 é NaN pois não há 2019Q4 para comparação (t vs t-1).")
print(ah_qoq.to_string())

print(f"\nAH YoY Netflix (% Variação Mesmo Trimestre Ano Anterior - Todos os Trimestres):")
print("Nota explicativa: 2020Q1 a 2020Q4 são NaN pois a série inicia em 2020 e não há trimestres de 2019 (t vs t-4).")
print(ah_yoy.to_string())

# ------------------------------------------------------------------------------
# 3. RENTABILIDADE E RETORNO (MARGENS E ROE TRIMESTRAIS)
# ------------------------------------------------------------------------------
print("\n" + "=" * 100)
print("3. RENTABILIDADE TRIMESTRAL (MARGENS E ROE) - SÉRIE COMPLETA")
print("=" * 100)

def get_profitability(df):
    res = pd.DataFrame(index=df.index)
    res['Margem Bruta (Gross Margin) %'] = ((df['GrossProfit'] / df['Revenues']) * 100).round(2)
    res['Margem Operacional (Operating Margin) %'] = ((df['OperatingIncome'] / df['Revenues']) * 100).round(2)
    res['Margem Líquida (Net Margin) %'] = ((df['NetIncome'] / df['Revenues']) * 100).round(2)
    
    pl_medio = (df['Equity'] + df['Equity'].shift(1)) / 2
    res['ROE Trimestral (Quarterly ROE) %'] = ((df['NetIncome'] / pl_medio) * 100).round(2)
    res['ROE Anualizado (Annualized ROE) %'] = (res['ROE Trimestral (Quarterly ROE) %'] * 4).round(2)
    return res

rent_nflx = get_profitability(df_nflx)
print(rent_nflx.to_string())

# ------------------------------------------------------------------------------
# 4. PRAZOS, LIQUIDEZ E MODELO FLEURIET TRIMESTRAL
# ------------------------------------------------------------------------------
print("\n" + "=" * 100)
print("4. PRAZOS, LIQUIDEZ E MODELO FLEURIET TRIMESTRAL - SÉRIE COMPLETA")
print("=" * 100)

def get_fleuriet(df):
    res = pd.DataFrame(index=df.index)
    res['Liquidez Corrente (Current Ratio)'] = (df['AssetsCurrent'] / df['LiabilitiesCurrent']).round(2)
    
    aco_m = (df['AssetsCurrent'] - df['Cash']) / 1e6
    acf_m = df['Cash'] / 1e6
    pco_m = (df['LiabilitiesCurrent'] - df['ShortTermDebt']) / 1e6
    pcf_m = df['ShortTermDebt'] / 1e6
    
    res['Capital de Giro / CDG (Working Capital - US$ M)'] = ((df['AssetsCurrent'] - df['LiabilitiesCurrent']) / 1e6).round(1)
    res['Necessidade Cap. Giro / NCG (Working Capital Need - US$ M)'] = (aco_m - pco_m).round(1)
    res['Saldo de Tesouraria / ST (Treasury Balance - US$ M)']  = (acf_m - pcf_m).round(1)
    return res

fl_nflx = get_fleuriet(df_nflx)
print(fl_nflx.to_string())

# ------------------------------------------------------------------------------
# 5. ESTRUTURA DE CAPITAL E ENDIVIDAMENTO TRIMESTRAL
# ------------------------------------------------------------------------------
print("\n" + "=" * 100)
print("5. ESTRUTURA DE CAPITAL E ENDIVIDAMENTO TRIMESTRAL - SÉRIE COMPLETA")
print("=" * 100)

def get_debt(df):
    res = pd.DataFrame(index=df.index)
    div_tot = df['ShortTermDebt'] + df['LongTermDebt']
    div_liq = div_tot - df['Cash']
    ebitda_trim = df['OperatingIncome'] + df['Depreciation']
    ebitda_ltm = ebitda_trim.rolling(4).sum()
    
    res['Dívida Total (Total Debt - US$ Bi)'] = (div_tot / 1e9).round(2)
    res['Caixa e Equivalentes (Cash - US$ Bi)'] = (df['Cash'] / 1e9).round(2)
    res['Dívida Líquida (Net Debt - US$ Bi)'] = (div_liq / 1e9).round(2)
    res['EBITDA LTM (12M - US$ Bi)'] = (ebitda_ltm / 1e9).round(2)
    res['Dívida Líquida / EBITDA LTM'] = (div_liq / ebitda_ltm).round(2)
    res['Endividamento / Passivo s/ PL (Debt-to-Equity %)'] = ((df['Liabilities'] / df['Equity']) * 100).round(2)
    return res

debt_nflx = get_debt(df_nflx)
print(debt_nflx.to_string())

# ------------------------------------------------------------------------------
# 6. GRAUS DE ALAVANCAGEM TRIMESTRAIS (GAO, GAF, GAT)
# ------------------------------------------------------------------------------
print("\n" + "=" * 100)
print("6. GRAUS DE ALAVANCAGEM TRIMESTRAIS (GAO, GAF, GAT) - SÉRIE COMPLETA")
print("=" * 100)

def get_leverage(df):
    res = pd.DataFrame(index=df.index)
    var_rev = df['Revenues'].pct_change(1)
    var_ebit = df['OperatingIncome'].pct_change(1)
    var_ll = df['NetIncome'].pct_change(1)
    
    res['GAO QoQ (Alavancagem Operacional - DOL)'] = (var_ebit / var_rev).round(2)
    res['GAF QoQ (Alavancagem Financeira - DFL)'] = (var_ll / var_ebit).round(2)
    res['GAT QoQ (Alavancagem Total - DTL)'] = (res['GAO QoQ (Alavancagem Operacional - DOL)'] * res['GAF QoQ (Alavancagem Financeira - DFL)']).round(2)
    return res

lev_nflx = get_leverage(df_nflx)
print(lev_nflx.to_string())

# ------------------------------------------------------------------------------
# 7. GERAÇÃO DO PAINEL GRÁFICO TRIMESTRAL COMPLETO (2020Q1 a 2026Q2)
# ------------------------------------------------------------------------------
print("\n" + "=" * 85)
print(f"7. GERANDO PAINEL GRÁFICO TRIMESTRAL NETFLIX ({df_nflx.index[0]} a {df_nflx.index[-1]})...")
print("=" * 85)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
plt.subplots_adjust(hspace=0.38, wspace=0.25)
q_labels = df_nflx.index

c_red   = '#E50914'
c_black = '#221F1F'
c_blue  = '#0071EB'
c_green = '#2BB673'

# 1. Receita e Lucros Trimestrais
axes[0, 0].plot(q_labels, df_nflx['Revenues'] / 1e9, marker='o', lw=2.2, color=c_black, label='Receita Líquida')
axes[0, 0].plot(q_labels, df_nflx['OperatingIncome'] / 1e9, marker='s', lw=2, color=c_red, label='EBIT (Lucro Op.)')
axes[0, 0].plot(q_labels, df_nflx['NetIncome'] / 1e9, marker='^', ls='--', lw=1.8, color=c_green, label='Lucro Líquido')
axes[0, 0].set_title(f"1. Evolução da Receita e Lucros Trimestrais ({df_nflx.index[0]} a {df_nflx.index[-1]})", fontweight='bold')
axes[0, 0].set_ylabel("US$ Bilhões")
axes[0, 0].legend(loc='best')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].tick_params(axis='x', rotation=60, labelsize=8)

# 2. Margens Trimestrais
axes[0, 1].plot(q_labels, rent_nflx['Margem Bruta (Gross Margin) %'], marker='o', lw=2, color=c_black, label='Margem Bruta %')
axes[0, 1].plot(q_labels, rent_nflx['Margem Operacional (Operating Margin) %'], marker='s', lw=2.2, color=c_red, label='Margem Operacional %')
axes[0, 1].plot(q_labels, rent_nflx['Margem Líquida (Net Margin) %'], marker='^', ls='--', lw=1.8, color=c_blue, label='Margem Líquida %')
axes[0, 1].set_title("2. Trajetória das Margens Trimestrais (%)", fontweight='bold')
axes[0, 1].set_ylabel("Margem (%)")
axes[0, 1].legend(loc='best')
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].tick_params(axis='x', rotation=60, labelsize=8)

# 3. Modelo Fleuriet Trimestral
axes[1, 0].plot(q_labels, fl_nflx['Capital de Giro / CDG (Working Capital - US$ M)'] / 1000, marker='o', color=c_black, label='CDG (Capital de Giro)')
axes[1, 0].plot(q_labels, fl_nflx['Necessidade Cap. Giro / NCG (Working Capital Need - US$ M)'] / 1000, marker='v', ls=':', color=c_red, label='NCG (Necessidade Cap. Giro)')
axes[1, 0].plot(q_labels, fl_nflx['Saldo de Tesouraria / ST (Treasury Balance - US$ M)'] / 1000, marker='*', ls='--', color=c_green, label='ST (Saldo de Tesouraria)')
axes[1, 0].axhline(0, color='gray', ls='--', alpha=0.5)
axes[1, 0].set_title("3. Modelo Fleuriet Trimestral (CDG, NCG e ST em US$ Bi)", fontweight='bold')
axes[1, 0].set_ylabel("US$ Bilhões")
axes[1, 0].legend(loc='best')
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].tick_params(axis='x', rotation=60, labelsize=8)

# 4. Geração de Caixa Trimestral
fcf_trim = (df_nflx['OperatingCashFlow'] - df_nflx['Capex']) / 1e9
axes[1, 1].bar(q_labels, df_nflx['OperatingCashFlow'] / 1e9, color=c_blue, alpha=0.6, label='FCO (Fluxo Caixa Op.)')
axes[1, 1].plot(q_labels, fcf_trim, marker='o', color=c_red, lw=2.2, label='Fluxo Caixa Livre (FCF)')
axes[1, 1].axhline(0, color='black', ls='--', alpha=0.7)
axes[1, 1].set_title("4. Caixa Operacional (FCO) e Caixa Livre (FCF) Trimestral", fontweight='bold')
axes[1, 1].set_ylabel("US$ Bilhões")
axes[1, 1].legend(loc='best')
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].tick_params(axis='x', rotation=60, labelsize=8)

chart_path = r"c:\Users\ddom1\Desktop\trab fer\painel_nflx_trimestral.png"
plt.savefig(chart_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"-> Painel gráfico consolidado salvo com sucesso em: {chart_path}")

# ------------------------------------------------------------------------------
# 8. GERAÇÃO DE GRÁFICOS SEPARADOS EM ALTA RESOLUÇÃO PARA SLIDES (16:9 - 300 DPI)
# ------------------------------------------------------------------------------
print("\n" + "=" * 85)
print("8. GERANDO GRÁFICOS SEPARADOS PRONTOS PARA SLIDES (PASTA 'graficos_slides/')...")
print("=" * 85)

def generate_slide_charts(df, rent, fl, debt, output_dir=r"c:\Users\ddom1\Desktop\trab fer\graficos_slides"):
    """
    Gera gráficos analíticos individuais formatados para slides (PowerPoint/Keynote/Google Slides).
    - Proporção Widescreen 16:9 (11 x 5.8 polegadas).
    - Resolução executiva de 300 DPI (sem perda de qualidade ao colar).
    - Paleta corporativa premium, tipografia limpa, linhas de contorno suaves e callouts.
    - Salva cada imagem individual em 'output_dir' e exibe na tela para cópia direta.
    """
    os.makedirs(output_dir, exist_ok=True)
    q_labels = df.index
    last_q = q_labels[-1]
    
    # Paleta de Cores Executiva Netflix
    c_red    = '#E50914'  # Netflix Red
    c_dark   = '#1E293B'  # Slate Black
    c_blue   = '#2563EB'  # Executive Blue
    c_green  = '#10B981'  # Emerald Green
    c_amber  = '#F59E0B'  # Amber
    c_purple = '#8B5CF6'  # Soft Violet
    c_grid   = '#E2E8F0'  # Soft Gray
    
    def apply_slide_styling(ax, title, subtitle="", ylabel=""):
        ax.set_facecolor('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#94A3B8')
        ax.spines['bottom'].set_color('#94A3B8')
        ax.grid(True, linestyle='--', alpha=0.5, color=c_grid)
        ax.tick_params(axis='x', rotation=45, labelsize=9, colors='#334155')
        ax.tick_params(axis='y', labelsize=10, colors='#334155')
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=11, fontweight='semibold', color='#1E293B')
        if subtitle:
            ax.set_title(f"{title}\n", fontsize=14, fontweight='bold', color='#0F172A', loc='left', pad=15)
            ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=10.5, color='#64748B', style='italic')
        else:
            ax.set_title(title, fontsize=14, fontweight='bold', color='#0F172A', loc='left', pad=15)

    chart_paths = []
    
    # 1. RECEITA, EBIT E LUCRO LÍQUIDO (US$ BILHÕES)
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=300)
    rev_b = df['Revenues'] / 1e9
    ebit_b = df['OperatingIncome'] / 1e9
    ll_b = df['NetIncome'] / 1e9
    ax.plot(q_labels, rev_b, marker='o', lw=2.8, color=c_dark, label='Receita Líquida (Revenues)')
    ax.plot(q_labels, ebit_b, marker='s', lw=2.4, color=c_red, label='Lucro Operacional / EBIT')
    ax.plot(q_labels, ll_b, marker='^', lw=2.2, color=c_green, linestyle='--', label='Lucro Líquido (Net Income)')
    ax.annotate(f"US$ {rev_b.iloc[-1]:.2f}B", (last_q, rev_b.iloc[-1]), textcoords="offset points", xytext=(0, 10), ha='center', fontweight='bold', color=c_dark)
    ax.annotate(f"US$ {ebit_b.iloc[-1]:.2f}B", (last_q, ebit_b.iloc[-1]), textcoords="offset points", xytext=(0, 10), ha='center', fontweight='bold', color=c_red)
    ax.annotate(f"US$ {ll_b.iloc[-1]:.2f}B", (last_q, ll_b.iloc[-1]), textcoords="offset points", xytext=(0, -15), ha='center', fontweight='bold', color=c_green)
    apply_slide_styling(ax, "Evolução da Receita e Resultados Trimestrais", f"Trajetória de escala do negócio ({df.index[0]} a {df.index[-1]}) - Valores em US$ Bilhões", "US$ Bilhões")
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, edgecolor='none', loc='upper left')
    p1 = os.path.join(output_dir, "01_receita_ebit_lucro_liquido.png")
    fig.savefig(p1, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(p1)

    # 2. MARGENS DE RENTABILIDADE (%)
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=300)
    ax.plot(q_labels, rent['Margem Bruta (Gross Margin) %'], marker='o', lw=2.5, color=c_dark, label='Margem Bruta %')
    ax.plot(q_labels, rent['Margem Operacional (Operating Margin) %'], marker='s', lw=2.6, color=c_red, label='Margem Operacional % (EBIT)')
    ax.plot(q_labels, rent['Margem Líquida (Net Margin) %'], marker='^', lw=2.2, color=c_blue, linestyle='--', label='Margem Líquida %')
    ax.annotate(f"{rent['Margem Bruta (Gross Margin) %'].iloc[-1]:.1f}%", (last_q, rent['Margem Bruta (Gross Margin) %'].iloc[-1]), textcoords="offset points", xytext=(0, 8), ha='center', fontweight='bold', color=c_dark)
    ax.annotate(f"{rent['Margem Operacional (Operating Margin) %'].iloc[-1]:.1f}%", (last_q, rent['Margem Operacional (Operating Margin) %'].iloc[-1]), textcoords="offset points", xytext=(0, 8), ha='center', fontweight='bold', color=c_red)
    ax.annotate(f"{rent['Margem Líquida (Net Margin) %'].iloc[-1]:.1f}%", (last_q, rent['Margem Líquida (Net Margin) %'].iloc[-1]), textcoords="offset points", xytext=(0, -15), ha='center', fontweight='bold', color=c_blue)
    apply_slide_styling(ax, "Trajetória das Margens de Lucratividade Trimestrais", "Alavancagem operacional e diluição de custos fixos de conteúdo", "Margem (%)")
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, edgecolor='none', loc='upper left')
    p2 = os.path.join(output_dir, "02_margens_rentabilidade.png")
    fig.savefig(p2, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(p2)

    # 3. RENTABILIDADE SOBRE O PATRIMÔNIO (ROE TRIMESTRAL E ANUALIZADO %)
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=300)
    ax.bar(q_labels, rent['ROE Anualizado (Annualized ROE) %'], color=c_blue, alpha=0.35, label='ROE Anualizado % (Trimestre x 4)', width=0.6)
    ax.plot(q_labels, rent['ROE Trimestral (Quarterly ROE) %'], marker='o', lw=2.6, color=c_red, label='ROE Trimestral %')
    ax.annotate(f"Trim: {rent['ROE Trimestral (Quarterly ROE) %'].iloc[-1]:.1f}%\nAnualizado: {rent['ROE Anualizado (Annualized ROE) %'].iloc[-1]:.1f}%", 
                (last_q, rent['ROE Trimestral (Quarterly ROE) %'].iloc[-1]), textcoords="offset points", xytext=(-25, 20), ha='center', fontweight='bold', color=c_red)
    apply_slide_styling(ax, "Retorno sobre o Patrimônio Líquido (ROE Trimestral e Anualizado)", "Capacidade de gerar valor sobre o capital investido pelos acionistas", "Taxa de Retorno (%)")
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, edgecolor='none', loc='upper left')
    p3 = os.path.join(output_dir, "03_retorno_roe.png")
    fig.savefig(p3, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(p3)

    # 4. MODELO FLEURIET E EQUILÍBRIO FINANCEIRO (CDG, NCG E ST EM US$ BI)
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=300)
    cdg_b = fl['Capital de Giro / CDG (Working Capital - US$ M)'] / 1000
    ncg_b = fl['Necessidade Cap. Giro / NCG (Working Capital Need - US$ M)'] / 1000
    st_b  = fl['Saldo de Tesouraria / ST (Treasury Balance - US$ M)'] / 1000
    ax.plot(q_labels, cdg_b, marker='o', lw=2.6, color=c_dark, label='CDG (Capital de Giro Líquido)')
    ax.plot(q_labels, ncg_b, marker='v', lw=2.4, color=c_amber, linestyle=':', label='NCG (Necessidade de Capital de Giro)')
    ax.plot(q_labels, st_b,  marker='*', lw=2.6, color=c_green, linestyle='--', label='ST (Saldo de Tesouraria = CDG - NCG)')
    ax.axhline(0, color='#64748B', linestyle='-', linewidth=1.2, alpha=0.8)
    apply_slide_styling(ax, "Dinâmica de Capital de Giro e Modelo Fleuriet", "Diagnóstico de liquidez: NCG controlada e Saldo de Tesouraria positivo = Folga Financeira", "US$ Bilhões")
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, edgecolor='none', loc='upper left')
    p4 = os.path.join(output_dir, "04_modelo_fleuriet.png")
    fig.savefig(p4, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(p4)

    # 5. GERAÇÃO DE CAIXA: FCO VS. FCF (FLUXO DE CAIXA LIVRE)
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=300)
    fco_b = df['OperatingCashFlow'] / 1e9
    fcf_b = (df['OperatingCashFlow'] - df['Capex']) / 1e9
    ax.bar(q_labels, fco_b, color='#93C5FD', alpha=0.7, label='FCO (Fluxo de Caixa Operacional)', width=0.6)
    ax.plot(q_labels, fcf_b, marker='o', color=c_red, lw=2.8, label='FCF (Fluxo de Caixa Livre = FCO - Capex)')
    ax.axhline(0, color='#64748B', linestyle='-', linewidth=1.1, alpha=0.7)
    ax.annotate(f"FCF: US$ {fcf_b.iloc[-1]:.2f}B", (last_q, fcf_b.iloc[-1]), textcoords="offset points", xytext=(0, 12), ha='center', fontweight='bold', color=c_red)
    apply_slide_styling(ax, "Capacidade de Conversão de Caixa: FCO vs. FCF", "Consolidação da Netflix como máquina geradora de caixa livre recorrente", "US$ Bilhões")
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, edgecolor='none', loc='upper left')
    p5 = os.path.join(output_dir, "05_geracao_caixa_fcf.png")
    fig.savefig(p5, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(p5)

    # 6. ESTRUTURA DE DÍVIDA E CAIXA (US$ BI)
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=300)
    div_tot = debt['Dívida Total (Total Debt - US$ Bi)']
    caixa   = debt['Caixa e Equivalentes (Cash - US$ Bi)']
    div_liq = debt['Dívida Líquida (Net Debt - US$ Bi)']
    ax.plot(q_labels, div_tot, marker='s', lw=2.4, color=c_red, label='Dívida Bruta Total (Curto + Longo Prazo)')
    ax.plot(q_labels, caixa,   marker='o', lw=2.4, color=c_green, label='Caixa e Equivalentes')
    ax.plot(q_labels, div_liq, marker='^', lw=2.6, color=c_dark, linestyle='--', label='Dívida Líquida (Dívida - Caixa)')
    ax.annotate(f"Dív. Líquida: US$ {div_liq.iloc[-1]:.2f}B", (last_q, div_liq.iloc[-1]), textcoords="offset points", xytext=(0, 10), ha='center', fontweight='bold', color=c_dark)
    apply_slide_styling(ax, "Perfil do Endividamento e Colchão de Liquidez", "Tendência de desalavancagem e amortização ordenada de compromissos", "US$ Bilhões")
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, edgecolor='none', loc='upper right')
    p6 = os.path.join(output_dir, "06_estrutura_divida.png")
    fig.savefig(p6, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(p6)

    # 7. ALAVANCAGEM FINANCEIRA: DÍVIDA LÍQUIDA / EBITDA LTM (x)
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=300)
    div_ebitda = debt['Dívida Líquida / EBITDA LTM']
    ax.plot(q_labels, div_ebitda, marker='o', lw=2.8, color=c_purple, label='Dívida Líquida / EBITDA (LTM)')
    ax.axhline(1.5, color='#10B981', linestyle=':', lw=1.5, label='Zona de Baixo Risco (< 1.5x)')
    ax.axhline(3.0, color='#EF4444', linestyle=':', lw=1.5, label='Alerta de Alto Endividamento (> 3.0x)')
    ax.annotate(f"{div_ebitda.iloc[-1]:.2f}x EBITDA", (last_q, div_ebitda.iloc[-1]), textcoords="offset points", xytext=(0, 12), ha='center', fontweight='bold', color=c_purple)
    apply_slide_styling(ax, "Indicador de Solvência: Dívida Líquida / EBITDA LTM", "Capacidade de pagar a dívida líquida com a geração operacional de 12 meses", "Múltiplo (x)")
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, edgecolor='none', loc='upper right')
    p7 = os.path.join(output_dir, "07_alavancagem_divida_ebitda.png")
    fig.savefig(p7, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(p7)

    # 8. LIQUIDEZ CORRENTE (CURTO PRAZO)
    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=300)
    liq_c = fl['Liquidez Corrente (Current Ratio)']
    ax.plot(q_labels, liq_c, marker='o', lw=2.6, color=c_blue, label='Índice de Liquidez Corrente')
    ax.axhline(1.0, color='#E50914', linestyle='--', lw=1.8, label='Linha Paridade 1.0x (Ativo Circulante = Passivo Circulante)')
    ax.annotate(f"{liq_c.iloc[-1]:.2f}x", (last_q, liq_c.iloc[-1]), textcoords="offset points", xytext=(0, 10), ha='center', fontweight='bold', color=c_blue)
    apply_slide_styling(ax, "Índice de Liquidez Corrente Trimestral", "Capacidade de cobrir obrigações de curto prazo com ativos de giro", "Índice (x)")
    ax.legend(frameon=True, facecolor='white', framealpha=0.9, edgecolor='none', loc='upper right')
    p8 = os.path.join(output_dir, "08_liquidez_corrente.png")
    fig.savefig(p8, dpi=300, bbox_inches='tight')
    plt.close()
    chart_paths.append(p8)

    print("=" * 90)
    print(f"-> 8 GRÁFICOS SEPARADOS EM ALTA RESOLUÇÃO (300 DPI) SALVOS COM SUCESSO EM:")
    print(f"   '{os.path.abspath(output_dir)}'")
    print("=" * 90)
    return chart_paths

# Executa e gera os 8 gráficos separados prontos para slides
slide_charts = generate_slide_charts(df_nflx, rent_nflx, fl_nflx, debt_nflx)

print(f"\n>>> EXECUÇÃO TRIMESTRAL DA NETFLIX ({df_nflx.index[0]} a {df_nflx.index[-1]}) FINALIZADA COM SUCESSO TOTAL! <<<")
