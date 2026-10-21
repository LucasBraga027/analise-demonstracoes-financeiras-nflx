"""
Etapa 5 - Gera a planilha "Analise_Netflix_ECO057.xlsx" com TODAS as análises em fórmulas do Excel.
Convenção: números em azul = dados oficiais (SEC/Fed/Tesouro/BLS/BCE); números em preto = fórmulas.
Metodologia espelhada na planilha da disciplina (Planilhas ECO057.xlsx, aba 'AV AH Indices', 'GAO', 'GAF', 'GAT'):
  AV = conta / base (Receita na DRE; Ativo Total no BP); AH = (Atual - Anterior) / ABS(Anterior);
  DuPont: ROA = Margem Líquida x Giro; ROE = ROA x MAF; NCG = ACO - PCO; ST = CCL - NCG;
  GAO = Δ%EBIT/Δ%Receita, GAF = Δ%LL/Δ%EBIT, GAT = GAO x GAF ("fórmula 1").
"""
import json
import os

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.line import LineProperties
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from sec_common import DADOS, ROOT

SAIDA = os.path.join(ROOT, 'Analise_Netflix_ECO057.xlsx')
D = os.path.join(ROOT, 'dados')

# Paleta validada (dataviz: slots 1-3 passam CVD em todos os pares) e tinta/superfície
AZUL, LARANJA, VERDE_AGUA = '2A78D6', 'EB6834', '1BAF7A'
TINTA, TINTA2, MUDO, GRADE = '0B0B0B', '52514E', '898781', 'E1E0D9'
INPUT = Font(name='Calibri', size=10, color='1F4FB4')
FORM = Font(name='Calibri', size=10, color=TINTA)
NEGRITO = Font(name='Calibri', size=10, bold=True, color=TINTA)
TITULO = Font(name='Calibri', size=14, bold=True, color=TINTA)
SUB = Font(name='Calibri', size=9, italic=True, color=TINTA2)
NOTA = Font(name='Calibri', size=8, color=MUDO)
SECAO = PatternFill('solid', fgColor='F0EFEC')
CABEC = PatternFill('solid', fgColor='1E293B')
CHECK = PatternFill('solid', fgColor='EAF6EE')
LINHA = Border(bottom=Side(style='thin', color=GRADE))

F_MI, F_PCT, F_X, F_NUM = '#,##0.0;[Red]-#,##0.0', '0.0%;[Red]-0.0%', '0.00"x"', '#,##0.00'


class Aba:
    """Aba com contas nas linhas e períodos nas colunas (C em diante), como na planilha da disciplina."""

    registro = {}
    pendentes = []

    @staticmethod
    def resolver_formulas():
        for cel, formula, i in Aba.pendentes:
            f = formula(i)
            cel.value = f'={f}' if f else None
        Aba.pendentes.clear()

    def __init__(self, wb, nome, titulo, subtitulo, periodos, largura_rotulo=52):
        self.ws = wb.create_sheet(nome)
        self.nome, self.periodos, self.linhas, self.r = nome, list(periodos), {}, 5
        Aba.registro[nome] = self
        ws = self.ws
        ws['A1'], ws['A1'].font = titulo, TITULO
        ws['A2'], ws['A2'].font = subtitulo, SUB
        ws['A4'], ws['B4'] = 'Conta / indicador', 'Fonte ou fórmula'
        for i, p in enumerate(self.periodos):
            ws.cell(4, 3 + i, p)
        for c in ws[4]:
            c.font, c.fill, c.alignment = Font(bold=True, color='FFFFFF', size=10), CABEC, Alignment(horizontal='center')
        ws.column_dimensions['A'].width = largura_rotulo
        ws.column_dimensions['B'].width = 30
        for i in range(len(self.periodos)):
            ws.column_dimensions[get_column_letter(3 + i)].width = 10.5
        ws.freeze_panes = 'C5'
        ws.sheet_view.showGridLines = False

    def col(self, i):
        return get_column_letter(3 + i)

    def ref(self, chave, i, absoluto=False):
        aba = Aba.registro[chave[0]] if isinstance(chave, tuple) else self
        k = chave[1] if isinstance(chave, tuple) else chave
        c, r = aba.col(i), aba.linhas[k]
        cel = f'${c}${r}' if absoluto else f'{c}{r}'
        return cel if aba is self else f"'{aba.nome}'!{cel}"

    def secao(self, texto):
        self.r += 1
        c = self.ws.cell(self.r, 1, texto)
        c.font = NEGRITO
        for j in range(1, 3 + len(self.periodos)):
            self.ws.cell(self.r, j).fill = SECAO
        self.r += 1

    def linha(self, chave, rotulo, valores=None, formula=None, fmt=F_MI, fonte='', negrito=False, check=False, inicio=0):
        """`valores`: lista de números (insumo); `formula`: função i -> texto da fórmula (sem '=') ou None."""
        ws, r = self.ws, self.r
        self.linhas[chave] = r
        ws.cell(r, 1, rotulo).font = NEGRITO if negrito else FORM
        ws.cell(r, 2, fonte).font = NOTA
        for i in range(len(self.periodos)):
            cel = ws.cell(r, 3 + i)
            if valores is not None:
                v = valores[i]
                cel.value = None if v is None or pd.isna(v) else float(v)
                cel.font = INPUT
            elif formula is not None and i >= inicio:
                # Resolvida só no fim (resolver_formulas), pois pode citar linhas definidas mais abaixo
                Aba.pendentes.append((cel, formula, i))
                cel.font = NEGRITO if negrito else FORM
            elif formula is not None:
                cel.value, cel.font = 'n.d.', NOTA
                cel.alignment = Alignment(horizontal='center')
            cel.number_format = fmt
            cel.border = LINHA
            if check:
                cel.fill = CHECK
        self.r += 1
        return r

    def nota(self, texto):
        self.r += 1
        self.ws.cell(self.r, 1, texto).font = NOTA
        self.r += 1

    def faixa(self, chave):
        r = self.linhas[chave]
        return f"'{self.nome}'!$C${r}:${self.col(len(self.periodos) - 1)}${r}"


def ah(aba, origem, chave, i, defas):
    """Fórmula da disciplina: (Atual - Anterior) / ABS(Anterior)."""
    a, b = aba.ref((origem, chave), i), aba.ref((origem, chave), i - defas)
    return f'IFERROR(({a}-{b})/ABS({b}),"")'


def soma_ltm(aba, origem, chave, i):
    return '+'.join(aba.ref((origem, chave), j) for j in range(i - 3, i + 1))


def main():
    base = pd.read_csv(os.path.join(D, 'base_trimestral_nflx.csv'), index_col=0)
    reg = pd.read_csv(os.path.join(D, 'regioes_nflx.csv'), index_col=0)
    mac = pd.read_csv(os.path.join(D, 'macro_trimestral.csv'), index_col=0).reindex(base.index)
    setor = pd.read_csv(os.path.join(D, 'setor_anual.csv'))
    stream = pd.read_csv(os.path.join(D, 'streaming_concorrentes.csv')).fillna('')
    eventos = pd.read_csv(os.path.join(D, 'eventos_variacoes.csv')).fillna('')
    manifest = json.load(open(os.path.join(DADOS, 'manifest_filings.json')))
    Q = list(base.index)
    n = len(Q)
    v = lambda c: base[c].tolist()

    wb = Workbook()
    leia = wb.active
    leia.title = 'LEIA-ME'

    # ------------------------------------------------------------------ DRE
    dre = Aba(wb, 'DRE', 'Netflix, Inc. — Demonstração do Resultado (trimestral)',
              'US$ milhões · Fonte: SEC EDGAR, 10-Q e 10-K (XBRL). 4º tri = ano (10-K) − 9 meses (10-Q).', Q)
    dre.secao('Demonstração do resultado')
    dre.linha('receita', '(=) Receita líquida', v('receita'), fonte='us-gaap:Revenues', negrito=True)
    dre.linha('custo', '(−) Custo dos serviços (inclui amortização de conteúdo)', v('custo_servicos'), fonte='us-gaap:CostOfRevenue')
    dre.linha('lucro_bruto', '(=) Lucro bruto', formula=lambda i: f"{dre.ref('receita', i)}-{dre.ref('custo', i)}", fonte='Receita − Custo', negrito=True)
    dre.linha('marketing', '(−) Marketing', v('marketing'), fonte='SellingAndMarketing / Marketing')
    dre.linha('tecnologia', '(−) Tecnologia e desenvolvimento', v('tecnologia'), fonte='T&D / ResearchAndDevelopment')
    dre.linha('ga', '(−) Gerais e administrativas', v('gerais_admin'), fonte='GeneralAndAdministrative')
    dre.linha('desp_op', '(=) Despesas operacionais', formula=lambda i: f"{dre.ref('marketing', i)}+{dre.ref('tecnologia', i)}+{dre.ref('ga', i)}", fonte='Soma')
    dre.linha('ebit', '(=) Lucro operacional (EBIT / LAJIR)', formula=lambda i: f"{dre.ref('lucro_bruto', i)}-{dre.ref('desp_op', i)}", fonte='Lucro bruto − Desp. operacionais', negrito=True)
    dre.linha('juros', '(−) Despesa de juros', v('despesa_juros'), fonte='InterestExpense(Nonoperating)')
    dre.linha('outras_fin', '(+/−) Juros e outras receitas/despesas (inclui câmbio)', v('outras_rec_desp_fin'), fonte='NonoperatingIncomeExpense')
    dre.linha('lair', '(=) Lucro antes do IR (LAIR)', formula=lambda i: f"{dre.ref('ebit', i)}-{dre.ref('juros', i)}+{dre.ref('outras_fin', i)}", fonte='EBIT − Juros + Outras', negrito=True)
    dre.linha('ir', '(−) Imposto de renda (sinal original; benefício = negativo)', v('ir_csll'), fonte='IncomeTaxExpenseBenefit')
    dre.linha('ll', '(=) Lucro líquido', formula=lambda i: f"{dre.ref('lair', i)}-{dre.ref('ir', i)}", fonte='LAIR − IR', negrito=True)
    dre.secao('Conferência com os valores informados à SEC (deve dar zero)')
    dre.linha('chk_ebit', 'EBIT calculado − EBIT informado', formula=lambda i: f"{dre.ref('ebit', i)}-{base['ebit'].iloc[i]:.3f}", fonte='OperatingIncomeLoss', check=True)
    dre.linha('chk_lair', 'LAIR calculado − LAIR informado', formula=lambda i: f"{dre.ref('lair', i)}-{base['lair'].iloc[i]:.3f}", fonte='IncomeBeforeIncomeTaxes', check=True)
    dre.linha('chk_ll', 'Lucro líquido calculado − informado', formula=lambda i: f"{dre.ref('ll', i)}-{base['lucro_liquido'].iloc[i]:.3f}", fonte='NetIncomeLoss', check=True)
    dre.secao('Itens de memória')
    dre.linha('cambio', 'Ganho (perda) cambial — incluso em "outras"', v('ganho_perda_cambial'), fonte='ForeignCurrencyTransactionGainLoss')
    dre.linha('amort_cont', 'Amortização de conteúdo — inclusa no custo', v('amort_conteudo'), fonte='nflx:CostofServicesAmortization...')
    dre.linha('da', 'Depreciação e amortização (imobilizado e intangíveis)', v('depreciacao_amort'), fonte='DepreciationDepletionAndAmortization')
    dre.linha('ebitda', '(=) EBITDA (EBIT + D&A; conteúdo NÃO é somado de volta)', formula=lambda i: f"{dre.ref('ebit', i)}+{dre.ref('da', i)}", fonte='EBIT + D&A', negrito=True)
    dre.nota('Na Netflix a amortização de conteúdo é custo operacional recorrente (substitui o "estoque" de filmes e séries); por isso não é adicionada ao EBITDA.')

    # ------------------------------------------------------------------ BP
    bp = Aba(wb, 'BP', 'Netflix, Inc. — Balanço Patrimonial (fim de cada trimestre)',
             'US$ milhões · Fonte: SEC EDGAR, 10-Q e 10-K (XBRL).', Q)
    bp.secao('Ativo')
    bp.linha('caixa', 'Caixa e equivalentes', v('caixa'), fonte='CashAndCashEquivalents')
    bp.linha('aplic', 'Aplicações financeiras de curto prazo', v('aplicacoes_cp'), fonte='ShortTermInvestments')
    bp.linha('outros_ac', 'Outros ativos circulantes (recebíveis, adiantamentos)', v('outros_ativos_circ'), fonte='OtherAssetsCurrent')
    bp.linha('ac', 'ATIVO CIRCULANTE', formula=lambda i: f"{bp.ref('caixa', i)}+{bp.ref('aplic', i)}+{bp.ref('outros_ac', i)}", fonte='Soma', negrito=True)
    bp.linha('conteudo', 'Ativos de conteúdo (líquidos)', v('ativos_conteudo'), fonte='nflx:ContentAssetsNet')
    bp.linha('imob', 'Imobilizado líquido', v('imobilizado'), fonte='PropertyPlantAndEquipmentNet')
    bp.linha('outros_anc', 'Outros ativos não circulantes', formula=lambda i: f"{bp.ref('at', i)}-{bp.ref('ac', i)}-{bp.ref('conteudo', i)}-{bp.ref('imob', i)}", fonte='Ativo total − demais')
    bp.linha('anc', 'ATIVO NÃO CIRCULANTE', formula=lambda i: f"{bp.ref('conteudo', i)}+{bp.ref('imob', i)}+{bp.ref('outros_anc', i)}", fonte='Soma', negrito=True)
    bp.linha('at', 'ATIVO TOTAL', v('ativo_total'), fonte='us-gaap:Assets', negrito=True)
    bp.secao('Passivo e patrimônio líquido')
    bp.linha('pass_cont_cp', 'Passivos de conteúdo (curto prazo)', v('passivo_conteudo_cp'), fonte='nflx:ContentLiabilitiesCurrent')
    bp.linha('fornec', 'Fornecedores', v('fornecedores'), fonte='AccountsPayableCurrent')
    bp.linha('provisoes', 'Despesas a pagar e provisões', v('contas_a_pagar_provisoes'), fonte='AccruedLiabilitiesCurrent')
    bp.linha('rec_dif', 'Receita diferida (assinaturas pagas antecipadamente)', v('receita_diferida'), fonte='ContractWithCustomerLiability')
    bp.linha('div_cp', 'Dívida de curto prazo', v('divida_cp'), fonte='ShortTermBorrowings')
    bp.linha('arred_pc', 'Arredondamento entre balanço e notas (resíduo, < US$ 1 mi)',
             formula=lambda i: f"{bp.ref('pc', i)}-(" + '+'.join(bp.ref(k, i) for k in ['pass_cont_cp', 'fornec', 'provisoes', 'rec_dif', 'div_cp']) + ')',
             fonte='PC informado − soma das linhas')
    bp.linha('pc', 'PASSIVO CIRCULANTE', v('passivo_circulante'), fonte='LiabilitiesCurrent', negrito=True)
    bp.linha('pass_cont_lp', 'Passivos de conteúdo (longo prazo)', v('passivo_conteudo_lp'), fonte='nflx:ContentLiabilitiesNoncurrent')
    bp.linha('div_lp', 'Dívida de longo prazo', v('divida_lp'), fonte='LongTermDebtNoncurrent')
    bp.linha('outros_plp', 'Outros passivos de longo prazo', v('outros_passivos_lp'), fonte='OtherLiabilitiesNoncurrent')
    bp.linha('arred_pnc', 'Arredondamento entre balanço e notas (resíduo, < US$ 1 mi)',
             formula=lambda i: f"{bp.ref('pnc', i)}-({bp.ref('pass_cont_lp', i)}+{bp.ref('div_lp', i)}+{bp.ref('outros_plp', i)})",
             fonte='PNC − soma das linhas')
    bp.linha('pnc', 'PASSIVO NÃO CIRCULANTE', formula=lambda i: f"{bp.ref('pt', i)}-{bp.ref('pc', i)}", fonte='Passivo total − PC', negrito=True)
    bp.linha('pt', 'PASSIVO TOTAL (exigível)', v('passivo_total'), fonte='us-gaap:Liabilities', negrito=True)
    bp.linha('pl', 'PATRIMÔNIO LÍQUIDO', v('patrimonio_liquido'), fonte='StockholdersEquity', negrito=True)
    bp.linha('pt_pl', 'PASSIVO TOTAL + PL', formula=lambda i: f"{bp.ref('pt', i)}+{bp.ref('pl', i)}", fonte='Soma', negrito=True)
    bp.secao('Conferências (devem dar zero)')
    bp.linha('chk_bp', 'Ativo total − (Passivo + PL)', formula=lambda i: f"{bp.ref('at', i)}-{bp.ref('pt_pl', i)}", fonte='Identidade contábil', check=True)
    bp.linha('chk_ac', 'AC calculado − AC informado', formula=lambda i: f"{bp.ref('ac', i)}-{base['ativo_circulante'].iloc[i]:.3f}", fonte='AssetsCurrent', check=True)
    bp.linha('chk_pc', 'Resíduo de arredondamento do PC (tolerância US$ 1 mi)', formula=lambda i: bp.ref('arred_pc', i), fonte='Ver linha do resíduo', check=True)
    bp.linha('chk_pt', 'Resíduo de arredondamento do PNC (tolerância US$ 1 mi)', formula=lambda i: bp.ref('arred_pnc', i), fonte='Ver linha do resíduo', check=True)

    # ------------------------------------------------------------------ DFC
    dfc = Aba(wb, 'DFC', 'Netflix, Inc. — Fluxo de Caixa (trimestral)',
              'US$ milhões · Fonte: SEC EDGAR. 10-Q traz o acumulado do ano; trimestre = acumulado − acumulado anterior.', Q)
    dfc.secao('Fluxos de caixa')
    dfc.linha('fco', 'Fluxo de caixa operacional (FCO)', v('fco'), fonte='NetCashProvidedByOperating', negrito=True)
    dfc.linha('capex', '(−) Compras de imobilizado (Capex)', v('capex'), fonte='PaymentsToAcquirePP&E')
    dfc.linha('fcl', '(=) Fluxo de caixa livre simplificado (FCO − Capex)', formula=lambda i: f"{dfc.ref('fco', i)}-{dfc.ref('capex', i)}", fonte='FCO − Capex', negrito=True)
    dfc.linha('fci', 'Fluxo de caixa de investimento', v('fci'), fonte='NetCashInvesting')
    dfc.linha('fcf', 'Fluxo de caixa de financiamento', v('fcf_financiamento'), fonte='NetCashFinancing')
    dfc.linha('recompra', 'Recompra de ações (saída de caixa)', v('recompra_acoes'), fonte='PaymentsForRepurchaseOfCommonStock')
    dfc.secao('Conteúdo: competência x caixa (a chave para entender o caixa da Netflix)')
    dfc.linha('gasto_cont', 'Pagamentos de conteúdo (caixa)', v('gasto_caixa_conteudo'), fonte='nflx:AdditionsToStreamingContentAssets')
    dfc.linha('amort_cont', 'Amortização de conteúdo (DRE)', formula=lambda i: dfc.ref(('DRE', 'amort_cont'), i), fonte='Igual à DRE')
    dfc.linha('razao_cont', 'Razão pagamento / amortização', formula=lambda i: f"IFERROR({dfc.ref('gasto_cont', i)}/{dfc.ref('amort_cont', i)},\"\")", fmt=F_X, fonte='> 1 = investe mais do que amortiza', negrito=True)
    dfc.linha('sbc', 'Remuneração em ações (não-caixa)', v('remuneracao_acoes'), fonte='ShareBasedCompensation')
    dfc.nota('A Netflix define FCL como FCO − Capex − variação de outros ativos; a versão simplificada daqui difere em poucos milhões.')

    # ------------------------------------------------------------------ AV
    av = Aba(wb, 'AV', 'Análise Vertical (AV)', 'DRE: % da Receita líquida · BP: % do Ativo total — fórmula da disciplina: conta / base', Q)
    av.secao('DRE — % da receita líquida')
    for k, rot in [('receita', 'Receita líquida'), ('custo', 'Custo dos serviços'), ('lucro_bruto', 'Lucro bruto'),
                   ('marketing', 'Marketing'), ('tecnologia', 'Tecnologia'), ('ga', 'Gerais e administrativas'),
                   ('ebit', 'EBIT'), ('juros', 'Despesa de juros'), ('outras_fin', 'Outras receitas/despesas financeiras'),
                   ('lair', 'LAIR'), ('ir', 'Imposto de renda'), ('ll', 'Lucro líquido'), ('amort_cont', 'Amortização de conteúdo'),
                   ('ebitda', 'EBITDA')]:
        av.linha(k, rot, formula=lambda i, k=k: f"IFERROR({av.ref(('DRE', k), i)}/{av.ref(('DRE', 'receita'), i)},\"\")", fmt=F_PCT,
                 negrito=k in ('lucro_bruto', 'ebit', 'll'))
    av.secao('Balanço — % do ativo total')
    for k, rot in [('caixa', 'Caixa'), ('aplic', 'Aplicações CP'), ('outros_ac', 'Outros AC'), ('ac', 'Ativo circulante'),
                   ('conteudo', 'Ativos de conteúdo'), ('imob', 'Imobilizado'), ('outros_anc', 'Outros ANC'), ('at', 'Ativo total'),
                   ('pass_cont_cp', 'Passivo de conteúdo CP'), ('fornec', 'Fornecedores'), ('provisoes', 'Provisões'),
                   ('rec_dif', 'Receita diferida'), ('div_cp', 'Dívida CP'), ('pc', 'Passivo circulante'),
                   ('pass_cont_lp', 'Passivo de conteúdo LP'), ('div_lp', 'Dívida LP'), ('outros_plp', 'Outros PLP'),
                   ('pnc', 'Passivo não circulante'), ('pl', 'Patrimônio líquido'), ('pt_pl', 'Passivo + PL')]:
        av.linha('bp_' + k, rot, formula=lambda i, k=k: f"IFERROR({av.ref(('BP', k), i)}/{av.ref(('BP', 'at'), i)},\"\")", fmt=F_PCT,
                 negrito=k in ('ac', 'at', 'pc', 'pl', 'pt_pl', 'conteudo'))

    # ------------------------------------------------------------------ AH
    ah_aba = Aba(wb, 'AH', 'Análise Horizontal (AH) — trimestral',
                 'Fórmula da disciplina: (Atual − Anterior) / ABS(Anterior). Cores: azul = alta, vermelho = queda; '
                 'borda laranja = variação brusca (|AH| ≥ 50%).', Q)
    itens_ah = [('DRE', 'receita', 'Receita líquida'), ('DRE', 'custo', 'Custo dos serviços'), ('DRE', 'lucro_bruto', 'Lucro bruto'),
                ('DRE', 'desp_op', 'Despesas operacionais'), ('DRE', 'ebit', 'EBIT'), ('DRE', 'ebitda', 'EBITDA'),
                ('DRE', 'juros', 'Despesa de juros'), ('DRE', 'll', 'Lucro líquido'),
                ('DFC', 'fco', 'Fluxo de caixa operacional'), ('DFC', 'fcl', 'Fluxo de caixa livre'),
                ('DFC', 'gasto_cont', 'Pagamentos de conteúdo'), ('BP', 'caixa', 'Caixa e equivalentes'),
                ('BP', 'ac', 'Ativo circulante'), ('BP', 'conteudo', 'Ativos de conteúdo'), ('BP', 'at', 'Ativo total'),
                ('BP', 'pc', 'Passivo circulante'), ('BP', 'div_lp', 'Dívida de longo prazo'), ('BP', 'pl', 'Patrimônio líquido')]
    ah_aba.secao('AH homóloga — trimestre contra o mesmo trimestre do ano anterior (t vs t−4): elimina a sazonalidade')
    for orig, k, rot in itens_ah:
        ah_aba.linha('yoy_' + k, rot, formula=lambda i, o=orig, k=k: ah(ah_aba, o, k, i, 4), fmt=F_PCT, inicio=4, fonte=f'{orig}', negrito=k in ('receita', 'ebit', 'll'))
    ah_aba.secao('AH sequencial — trimestre contra o trimestre imediatamente anterior (t vs t−1)')
    for orig, k, rot in itens_ah:
        ah_aba.linha('qoq_' + k, rot, formula=lambda i, o=orig, k=k: ah(ah_aba, o, k, i, 1), fmt=F_PCT, inicio=1, fonte=f'{orig}', negrito=k in ('receita', 'ebit', 'll'))
    ah_aba.secao('AH com base fixa — índice 2019T4 = 100 (evolução acumulada)')
    i0 = Q.index('2019T4')
    for orig, k, rot in itens_ah[:6] + [itens_ah[7], itens_ah[14], itens_ah[17]]:
        ah_aba.linha('idx_' + k, rot, formula=lambda i, o=orig, k=k: f"IFERROR({ah_aba.ref((o, k), i)}/{ah_aba.ref((o, k), i0, True)}*100,\"\")", fmt='0', inicio=i0, fonte=f'{orig}')
    ultima = get_column_letter(2 + n)
    faixa_ah = f'C7:{ultima}{ah_aba.r}'
    ah_aba.ws.conditional_formatting.add(faixa_ah, ColorScaleRule(start_type='num', start_value=-0.5, start_color='F2B8B5',
                                                                  mid_type='num', mid_value=0, mid_color='FFFFFF',
                                                                  end_type='num', end_value=0.5, end_color='B7D3F6'))
    lim = f'{ah_aba.linhas["idx_" + itens_ah[0][1]] - 2}'
    ah_aba.ws.conditional_formatting.add(f'C7:{ultima}{lim}', CellIsRule(operator='notBetween', formula=['-0.5', '0.5'],
                                                                          font=Font(bold=True, color='B23A0E')))

    # ------------------------------------------------------------------ AH anual
    anos = sorted({q[:4] for q in Q if Q.count(q[:4] + 'T4') or q[:4] + 'T4' in Q})
    anos = [a for a in anos if f'{a}T4' in Q]
    ult_ano = Q[-1][:4]
    tem_semestre = f'{ult_ano}T2' in Q and f'{int(ult_ano) - 1}T2' in Q
    periodos_anuais = anos + ([f'1S{int(ult_ano) - 1}', f'1S{ult_ano}'] if tem_semestre else [])
    an = Aba(wb, 'AH_Anual', 'Análise Horizontal — anual (e 1º semestre)',
             'Fluxos: soma dos 4 trimestres (1S = T1+T2) · Saldos: posição no fim do período · AH = (Atual − Anterior)/ABS(Anterior)', periodos_anuais)

    def cols_periodo(p):
        if p.startswith('1S'):
            a = p[2:]
            return [Q.index(f'{a}T1'), Q.index(f'{a}T2')]
        return [Q.index(f'{p}T{t}') for t in range(1, 5)]

    def anual_fluxo(o, k):
        return lambda j: f"SUM({an.ref((o, k), cols_periodo(periodos_anuais[j])[0])}:{Aba.registro[o].col(cols_periodo(periodos_anuais[j])[-1])}{Aba.registro[o].linhas[k]})"

    def anual_saldo(o, k):
        return lambda j: an.ref((o, k), cols_periodo(periodos_anuais[j])[-1])

    an.secao('Valores (US$ milhões)')
    fluxos = [('DRE', 'receita', 'Receita líquida'), ('DRE', 'custo', 'Custo dos serviços'), ('DRE', 'lucro_bruto', 'Lucro bruto'),
              ('DRE', 'desp_op', 'Despesas operacionais'), ('DRE', 'ebit', 'EBIT'), ('DRE', 'ebitda', 'EBITDA'),
              ('DRE', 'juros', 'Despesa de juros'), ('DRE', 'outras_fin', 'Outras receitas/despesas financeiras'), ('DRE', 'll', 'Lucro líquido'),
              ('DFC', 'fco', 'FCO'), ('DFC', 'fcl', 'FCL (FCO − Capex)'), ('DFC', 'gasto_cont', 'Pagamentos de conteúdo'),
              ('DRE', 'amort_cont', 'Amortização de conteúdo'), ('DFC', 'recompra', 'Recompra de ações')]
    saldos = [('BP', 'caixa', 'Caixa (fim do período)'), ('BP', 'ac', 'Ativo circulante'), ('BP', 'conteudo', 'Ativos de conteúdo'),
              ('BP', 'at', 'Ativo total'), ('BP', 'pc', 'Passivo circulante'), ('BP', 'div_lp', 'Dívida de longo prazo'),
              ('BP', 'pt', 'Passivo total'), ('BP', 'pl', 'Patrimônio líquido')]
    for o, k, rot in fluxos:
        an.linha(k, rot, formula=anual_fluxo(o, k), fonte=f'Σ {o}', negrito=k in ('receita', 'ebit', 'll'))
    for o, k, rot in saldos:
        an.linha('s_' + k, rot, formula=anual_saldo(o, k), fonte=f'{o} fim do período', negrito=k in ('at', 'pl'))
    an.secao('AH ano contra ano (1S contra 1S)')
    comparavel = lambda j: j >= 1 and not (periodos_anuais[j].startswith('1S') and not periodos_anuais[j - 1].startswith('1S'))
    for o, k, rot in fluxos:
        an.linha('ah_' + k, rot, formula=lambda j, k=k: f'IFERROR(({an.ref(k, j)}-{an.ref(k, j - 1)})/ABS({an.ref(k, j - 1)}),"")' if comparavel(j) else None,
                 fmt=F_PCT, inicio=1, negrito=k in ('receita', 'ebit', 'll'))
    for o, k, rot in saldos:
        an.linha('ah_s_' + k, rot, formula=lambda j, k=k: f'IFERROR(({an.ref("s_" + k, j)}-{an.ref("s_" + k, j - 1)})/ABS({an.ref("s_" + k, j - 1)}),"")' if comparavel(j) else None,
                 fmt=F_PCT, inicio=1)
    an.secao('Margens e alavancagens anuais (fórmula 1 da disciplina: elasticidades)')
    an.linha('mg_ebit', 'Margem EBIT', formula=lambda j: f'{an.ref("ebit", j)}/{an.ref("receita", j)}', fmt=F_PCT)
    an.linha('mg_ll', 'Margem líquida', formula=lambda j: f'{an.ref("ll", j)}/{an.ref("receita", j)}', fmt=F_PCT)
    an.linha('gao', 'GAO = Δ%EBIT / Δ%Receita', formula=lambda j: f'IFERROR({an.ref("ah_ebit", j)}/{an.ref("ah_receita", j)},"")' if comparavel(j) else None, fmt=F_NUM, inicio=1, negrito=True)
    an.linha('gaf', 'GAF = Δ%Lucro líquido / Δ%EBIT', formula=lambda j: f'IFERROR({an.ref("ah_ll", j)}/{an.ref("ah_ebit", j)},"")' if comparavel(j) else None, fmt=F_NUM, inicio=1, negrito=True)
    an.linha('gat', 'GAT = GAO × GAF', formula=lambda j: f'IFERROR({an.ref("gao", j)}*{an.ref("gaf", j)},"")' if comparavel(j) else None, fmt=F_NUM, inicio=1, negrito=True)
    an.nota('A disciplina usa Δ%LPA no GAF; aqui usa-se Δ%Lucro líquido porque o desdobramento de ações 10:1 (nov/2025) distorce o LPA histórico.')
    an.nota('Em 2026 o lucro líquido inclui a multa rescisória da WBD (US$ 2,8 bi), o que infla o GAF do 1S2026 — ler junto com a aba Variacoes_Bruscas.')

    # ------------------------------------------------------------------ Indicadores
    ind = Aba(wb, 'Indicadores', 'Índices econômico-financeiros (trimestrais)',
              'Valores "LTM" = últimos 12 meses (soma de 4 trimestres): evita multiplicar o trimestre por 4 e ignorar a sazonalidade.', Q)
    R = lambda o, k, i: ind.ref((o, k), i)
    ind.secao('Rentabilidade do trimestre')
    for k, rot, num_ in [('mg_bruta', 'Margem bruta', 'lucro_bruto'), ('mg_ebit', 'Margem EBIT (operacional)', 'ebit'),
                         ('mg_ebitda', 'Margem EBITDA', 'ebitda'), ('mg_liq', 'Margem líquida', 'll')]:
        ind.linha(k, rot, formula=lambda i, num_=num_: f"IFERROR({R('DRE', num_, i)}/{R('DRE', 'receita', i)},\"\")", fmt=F_PCT, negrito=k == 'mg_ebit')
    ind.secao('Últimos 12 meses (LTM) — US$ milhões')
    for k, o, src, rot in [('rec_ltm', 'DRE', 'receita', 'Receita LTM'), ('ebit_ltm', 'DRE', 'ebit', 'EBIT LTM'),
                           ('ebitda_ltm', 'DRE', 'ebitda', 'EBITDA LTM'), ('ll_ltm', 'DRE', 'll', 'Lucro líquido LTM'),
                           ('juros_ltm', 'DRE', 'juros', 'Despesa de juros LTM'), ('custo_ltm', 'DRE', 'custo', 'Custo dos serviços LTM')]:
        ind.linha(k, rot, formula=lambda i, o=o, src=src: soma_ltm(ind, o, src, i), inicio=3)
    ind.secao('DuPont (modelo da disciplina): ROA = Margem líquida × Giro; ROE = ROA × MAF')
    ind.linha('ml_ltm', 'Margem líquida LTM (LL/Receitas)', formula=lambda i: f"{ind.ref('ll_ltm', i)}/{ind.ref('rec_ltm', i)}", fmt=F_PCT, inicio=3)
    ind.linha('giro', 'Giro do ativo (Receitas LTM / Ativo total)', formula=lambda i: f"{ind.ref('rec_ltm', i)}/{R('BP', 'at', i)}", fmt=F_NUM, inicio=3)
    ind.linha('roa', 'ROA = Margem líquida × Giro', formula=lambda i: f"{ind.ref('ml_ltm', i)}*{ind.ref('giro', i)}", fmt=F_PCT, inicio=3, negrito=True)
    ind.linha('maf', 'MAF — multiplicador de alavancagem (AT / PL)', formula=lambda i: f"{R('BP', 'at', i)}/{R('BP', 'pl', i)}", fmt=F_NUM)
    ind.linha('roe', 'ROE = ROA × MAF', formula=lambda i: f"{ind.ref('roa', i)}*{ind.ref('maf', i)}", fmt=F_PCT, inicio=3, negrito=True)
    ind.linha('roe_chk', 'Conferência: LL LTM / PL', formula=lambda i: f"{ind.ref('ll_ltm', i)}/{R('BP', 'pl', i)}", fmt=F_PCT, inicio=3, check=True)
    ind.secao('Liquidez')
    ind.linha('lc', 'Liquidez corrente (AC / PC)', formula=lambda i: f"{R('BP', 'ac', i)}/{R('BP', 'pc', i)}", fmt=F_NUM, negrito=True)
    ind.linha('ls', 'Liquidez seca ((AC − Estoques) / PC) — sem estoques, = LC', formula=lambda i: f"({R('BP', 'ac', i)}-0)/{R('BP', 'pc', i)}", fmt=F_NUM)
    ind.linha('li', 'Liquidez imediata ((Caixa + Aplicações) / PC)', formula=lambda i: f"({R('BP', 'caixa', i)}+{R('BP', 'aplic', i)})/{R('BP', 'pc', i)}", fmt=F_NUM)
    ind.secao('Modelo Fleuriet (capital de giro) — US$ milhões')
    ind.linha('ccl', 'CCL / CDG = AC − PC', formula=lambda i: f"{R('BP', 'ac', i)}-{R('BP', 'pc', i)}", negrito=True)
    ind.linha('aco', 'ACO — ativo circulante operacional (outros AC)', formula=lambda i: R('BP', 'outros_ac', i))
    ind.linha('pco', 'PCO — passivo circulante operacional (PC − dívida CP)', formula=lambda i: f"{R('BP', 'pc', i)}-{R('BP', 'div_cp', i)}")
    ind.linha('ncg', 'NCG = ACO − PCO', formula=lambda i: f"{ind.ref('aco', i)}-{ind.ref('pco', i)}", negrito=True)
    ind.linha('st', 'Saldo de tesouraria ST = CCL − NCG', formula=lambda i: f"{ind.ref('ccl', i)}-{ind.ref('ncg', i)}", negrito=True)
    ind.linha('st_chk', 'Conferência: ST = (Caixa + Aplicações) − Dívida CP', formula=lambda i: f"{ind.ref('st', i)}-({R('BP', 'caixa', i)}+{R('BP', 'aplic', i)}-{R('BP', 'div_cp', i)})", check=True)
    def tipo_fleuriet(i):
        # Classificação de Fleuriet/Braga pelos sinais de CCL (CDG), NCG e ST
        c, g, t = (f'{ind.ref(k, i)}>0' for k in ('ccl', 'ncg', 'st'))
        return (f'IF(AND({c},NOT({g}),{t}),"I - Excelente",IF(AND({c},{g},{t}),"II - Sólida",'
                f'IF(AND({c},{g},NOT({t})),"III - Insatisfatória",IF(AND(NOT({c}),{g},NOT({t})),"IV - Péssima",'
                f'IF(AND(NOT({c}),NOT({g}),NOT({t})),"V - Muito ruim",IF(AND(NOT({c}),NOT({g}),{t}),"VI - Alto risco","Outra"))))))')
    ind.linha('tipo', 'Tipo de estrutura (Fleuriet/Braga: sinais de CCL, NCG e ST)', formula=tipo_fleuriet, fmt='@', negrito=True)
    ind.nota('Tipo VI (CCL < 0, NCG < 0, ST > 0): o caixa existe, mas é sustentado por passivos operacionais de curto prazo (conteúdo a pagar, '
             'receita antecipada) — depende de a empresa continuar crescendo e recebendo antes de pagar.')
    ind.secao('Estrutura de capital e endividamento')
    ind.linha('ct_pl', 'CT/PL — capital de terceiros / PL', formula=lambda i: f"{R('BP', 'pt', i)}/{R('BP', 'pl', i)}", fmt=F_NUM)
    ind.linha('div_bruta', 'Dívida bruta (CP + LP) — US$ mi', formula=lambda i: f"{R('BP', 'div_cp', i)}+{R('BP', 'div_lp', i)}")
    ind.linha('div_liq', 'Dívida líquida (bruta − caixa − aplicações) — US$ mi', formula=lambda i: f"{ind.ref('div_bruta', i)}-{R('BP', 'caixa', i)}-{R('BP', 'aplic', i)}", negrito=True)
    ind.linha('dl_ebitda', 'Dívida líquida / EBITDA LTM', formula=lambda i: f"{ind.ref('div_liq', i)}/{ind.ref('ebitda_ltm', i)}", fmt=F_X, inicio=3, negrito=True)
    ind.linha('cobertura', 'Cobertura de juros (EBIT LTM / Juros LTM)', formula=lambda i: f"{ind.ref('ebit_ltm', i)}/{ind.ref('juros_ltm', i)}", fmt=F_X, inicio=3)
    ind.linha('pmpc', 'PMPC — prazo médio de pagamento (Fornecedores / Custo LTM × 365), dias', formula=lambda i: f"{R('BP', 'fornec', i)}/{ind.ref('custo_ltm', i)}*365", fmt='0', inicio=3)
    ind.secao('Conteúdo')
    ind.linha('cont_at', 'Ativos de conteúdo / Ativo total', formula=lambda i: f"{R('BP', 'conteudo', i)}/{R('BP', 'at', i)}", fmt=F_PCT)
    ind.linha('amort_rec', 'Amortização de conteúdo / Receita', formula=lambda i: f"{R('DRE', 'amort_cont', i)}/{R('DRE', 'receita', i)}", fmt=F_PCT)
    ind.linha('razao', 'Pagamentos / amortização de conteúdo', formula=lambda i: R('DFC', 'razao_cont', i), fmt=F_X)
    ind.secao('Graus de alavancagem — fórmula 1 da disciplina, base homóloga (t vs t−4)')
    ind.linha('gao', 'GAO = Δ%EBIT / Δ%Receita', formula=lambda i: f"IFERROR({R('AH', 'yoy_ebit', i)}/{R('AH', 'yoy_receita', i)},\"\")", fmt=F_NUM, inicio=4, negrito=True)
    ind.linha('gaf', 'GAF = Δ%Lucro líquido / Δ%EBIT', formula=lambda i: f"IFERROR({R('AH', 'yoy_ll', i)}/{R('AH', 'yoy_ebit', i)},\"\")", fmt=F_NUM, inicio=4, negrito=True)
    ind.linha('gat', 'GAT = GAO × GAF', formula=lambda i: f"IFERROR({ind.ref('gao', i)}*{ind.ref('gaf', i)},\"\")", fmt=F_NUM, inicio=4, negrito=True)
    ind.nota('Elasticidades explodem quando a variação do denominador é próxima de zero (ex.: EBIT 2022T1 +1%): ler sempre junto com a AH. '
             'Base homóloga evita a sazonalidade do T4; a versão anual está na aba AH_Anual.')

    # ------------------------------------------------------------------ Regiões
    rg = Aba(wb, 'Regioes', 'Receita e assinantes por região',
             'Receita em US$ milhões; assinantes pagos em milhões (divulgação encerrada após 2024T4). Fonte: notas dos 10-Q/10-K (XBRL).', Q)
    regs = [('EUA_Canada', 'EUA e Canadá'), ('EMEA', 'Europa, Oriente Médio e África'), ('America_Latina', 'América Latina'), ('Asia_Pacifico', 'Ásia-Pacífico')]
    rg.secao('Receita por região (US$ milhões)')
    for k, rot in regs:
        rg.linha('rec_' + k, rot, reg[f'receita_{k}'].tolist(), fonte='Revenues × região')
    rg.linha('rec_DVD', 'DVD (encerrado em set/2023)', formula=lambda i: f"{R('DRE', 'receita', i)}-" + '-'.join(rg.ref('rec_' + k, i) for k, _ in regs), fonte='Total − streaming')
    rg.secao('Participação na receita (AV)')
    for k, rot in regs:
        rg.linha('av_' + k, rot, formula=lambda i, k=k: f"{rg.ref('rec_' + k, i)}/{R('DRE', 'receita', i)}", fmt=F_PCT)
    rg.secao('AH homóloga da receita por região (t vs t−4)')
    for k, rot in regs:
        rg.linha('ah_' + k, rot, formula=lambda i, k=k: f'IFERROR(({rg.ref("rec_" + k, i)}-{rg.ref("rec_" + k, i - 4)})/ABS({rg.ref("rec_" + k, i - 4)}),"")', fmt=F_PCT, inicio=4)
    rg.secao('Assinantes pagos (milhões, fim do trimestre)')
    for k, rot in regs:
        rg.linha('ass_' + k, rot, reg[f'assinantes_{k}'].tolist(), fmt='#,##0.0', fonte='NumberOfPaidMemberships')
    rg.linha('ass_total', 'Total', formula=lambda i: f'IF(COUNT({",".join(rg.ref("ass_" + k, i) for k, _ in regs)})=4,{"+".join(rg.ref("ass_" + k, i) for k, _ in regs)},"")', fmt='#,##0.0', negrito=True)
    rg.linha('adicoes', 'Adições líquidas no trimestre', formula=lambda i: f'IFERROR(IF({rg.ref("ass_total", i)}="","",{rg.ref("ass_total", i)}-{rg.ref("ass_total", i - 1)}),"")', fmt='#,##0.0', inicio=1, negrito=True)
    rg.secao('ARM — receita média mensal por assinante (US$/mês) = receita / média de assinantes / 3')
    for k, rot in regs:
        rg.linha('arm_' + k, rot, formula=lambda i, k=k: f'IFERROR({rg.ref("rec_" + k, i)}/AVERAGE({rg.ref("ass_" + k, i)},{rg.ref("ass_" + k, i - 1)})/3,"")', fmt='0.00', inicio=1)
    rg.nota('A Netflix deixou de divulgar assinantes a partir de 2025 (anúncio na carta do 1º tri/2024); carta do 4º tri/2025 cita "325 milhões".')

    # ------------------------------------------------------------------ Macro
    mc = Aba(wb, 'Macro', 'Contexto macroeconômico (médias trimestrais)',
             'Fontes oficiais: Federal Reserve (H.15), U.S. Treasury, BLS (CPI-U e desemprego), Banco Central Europeu (câmbio).', Q)
    mc.secao('Estados Unidos')
    for k, rot, fonte in [('fed_funds_pct', 'Juro básico — Fed Funds efetivo (% a.a.)', 'Fed H.15'),
                          ('treasury_10a_pct', 'Título do Tesouro de 10 anos (% a.a.)', 'U.S. Treasury'),
                          ('inflacao_cpi_12m_pct', 'Inflação ao consumidor CPI-U (% em 12 meses)', 'BLS CUUR0000SA0'),
                          ('desemprego_pct', 'Taxa de desemprego (%)', 'BLS LNS14000000')]:
        mc.linha(k, rot, (mac[k] / 100).tolist(), fmt='0.00%', fonte=fonte)
    mc.secao('Câmbio — unidades de moeda local por 1 US$ (alta = dólar mais forte = receita em US$ menor)')
    for k, rot in [('EUR_por_USD', 'Euro'), ('BRL_por_USD', 'Real brasileiro'), ('MXN_por_USD', 'Peso mexicano'),
                   ('GBP_por_USD', 'Libra esterlina'), ('JPY_por_USD', 'Iene')]:
        mc.linha(k, rot, mac[k].tolist(), fmt='0.000', fonte='BCE (via EUR)')
    mc.linha('idx_dolar', 'Índice do dólar vs. cesta das 5 moedas (2019T4 = 100)', mac['indice_dolar_cesta_2019T4_100'].tolist(), fmt='0.0', fonte='Média simples das 5 moedas', negrito=True)
    mc.secao('Ligação com a Netflix')
    mc.linha('ah_dolar', 'Variação do índice do dólar em 12 meses', formula=lambda i: f'IFERROR({mc.ref("idx_dolar", i)}/{mc.ref("idx_dolar", i - 4)}-1,"")', fmt=F_PCT, inicio=4)
    mc.linha('ah_rec', 'Netflix: crescimento da receita em 12 meses (AH homóloga)', formula=lambda i: R('AH', 'yoy_receita', i), fmt=F_PCT, inicio=4, negrito=True)
    mc.linha('ah_emea', 'Netflix: crescimento da receita EMEA em 12 meses', formula=lambda i: R('Regioes', 'ah_EMEA', i), fmt=F_PCT, inicio=4)
    mc.linha('juros_nf', 'Netflix: despesa de juros (US$ mi)', formula=lambda i: R('DRE', 'juros', i))
    mc.nota('Leitura: dólar forte (2022, 2024T4-2025T1) reduz a receita convertida; juros altos (2023-24) não elevaram a despesa de juros porque a dívida é de taxa fixa.')
    mc.nota('CPI de out/2025 não foi coletado pelo BLS (paralisação do governo dos EUA); a média do 4º tri/2025 usa os meses disponíveis.')

    Aba.resolver_formulas()

    # ------------------------------------------------------------------ Setor
    st = wb.create_sheet('Setor')
    st.sheet_view.showGridLines = False
    st['A1'], st['A1'].font = 'Análise setorial — streaming e mídia (dados anuais, SEC EDGAR)', TITULO
    st['A2'], st['A2'].font = 'US$ milhões · Disney: ano fiscal termina em set/out · Netflix, WBD, Paramount e Comcast: ano-calendário', SUB
    emp_nome = {'NFLX': 'Netflix', 'DIS': 'Disney', 'WBD': 'Warner Bros. Discovery', 'PARA': 'Paramount Global', 'CMCSA': 'Comcast (NBCU/Peacock)'}
    anos_s = sorted(setor['ano_fiscal'].unique())
    blocos = [('receita_usd_mi', 'Receita (US$ mi)', F_MI), ('ebit_usd_mi', 'Lucro operacional (US$ mi)', F_MI)]
    r = 4
    pos = {}
    for chave, titulo, fmt in blocos:
        st.cell(r, 1, titulo).font = NEGRITO
        for j, a in enumerate(anos_s):
            c = st.cell(r, 2 + j, int(a))
            c.font, c.fill, c.alignment = Font(bold=True, color='FFFFFF'), CABEC, Alignment(horizontal='center')
        r += 1
        for tk in ['NFLX', 'DIS', 'WBD', 'PARA', 'CMCSA']:
            st.cell(r, 1, emp_nome[tk]).font = NEGRITO if tk == 'NFLX' else FORM
            for j, a in enumerate(anos_s):
                x = setor[(setor['empresa'] == tk) & (setor['ano_fiscal'] == a)][chave]
                if len(x) and pd.notna(x.iloc[0]):
                    cel = st.cell(r, 2 + j, float(x.iloc[0]))
                    cel.font, cel.number_format = INPUT, fmt
            pos[(chave, tk)] = r
            r += 1
        r += 1
    for titulo, form, fmt in [('Crescimento da receita (AH anual)', lambda tk, j: f'IFERROR(({get_column_letter(2 + j)}{pos[("receita_usd_mi", tk)]}-{get_column_letter(1 + j)}{pos[("receita_usd_mi", tk)]})/ABS({get_column_letter(1 + j)}{pos[("receita_usd_mi", tk)]}),"")', F_PCT),
                              ('Margem operacional (AV: EBIT / Receita)', lambda tk, j: f'IFERROR({get_column_letter(2 + j)}{pos[("ebit_usd_mi", tk)]}/{get_column_letter(2 + j)}{pos[("receita_usd_mi", tk)]},"")', F_PCT)]:
        st.cell(r, 1, titulo).font = NEGRITO
        for j, a in enumerate(anos_s):
            c = st.cell(r, 2 + j, int(a))
            c.font, c.fill, c.alignment = Font(bold=True, color='FFFFFF'), CABEC, Alignment(horizontal='center')
        r += 1
        for tk in ['NFLX', 'DIS', 'WBD', 'PARA', 'CMCSA']:
            st.cell(r, 1, emp_nome[tk]).font = NEGRITO if tk == 'NFLX' else FORM
            for j in range(len(anos_s)):
                if titulo.startswith('Cresc') and j == 0:
                    continue
                cel = st.cell(r, 2 + j, '=' + form(tk, j))
                cel.number_format = fmt
            r += 1
        r += 1
    st.cell(r, 1, 'WBD 2022: fusão Discovery + WarnerMedia (abr/2022) explica o salto de receita — não é crescimento orgânico. '
                  'Prejuízos operacionais de WBD e Paramount incluem baixas contábeis (impairments) de TV linear.').font = NOTA
    r += 1
    st.cell(r, 1, 'ATENÇÃO — Disney: a linha de lucro operacional acima é o "lucro operacional dos segmentos" (a Disney não divulga uma linha '
                  'de resultado operacional GAAP). Para comparar com as demais, use a linha reconstruída abaixo.').font = Font(size=8, bold=True, color='B23A0E')
    r += 1
    # Lucro dos segmentos − despesas corporativas − reestruturação/impairments − amortização TFCF/Hulu (reconciliações dos 10-K da Disney)
    disney_comparavel = {2019: 11082, 2020: -1290, 2021: 3766, 2022: 7349, 2023: 5882, 2024: 8894, 2025: 13510}
    st.cell(r, 1, 'Disney — resultado operacional comparável (US$ mi)').font = NEGRITO
    for j, a in enumerate(anos_s):
        if int(a) in disney_comparavel:
            c = st.cell(r, 2 + j, disney_comparavel[int(a)])
            c.font, c.number_format = INPUT, F_MI
    r += 1
    st.cell(r, 1, 'Disney — margem operacional comparável').font = FORM
    for j, a in enumerate(anos_s):
        if int(a) in disney_comparavel:
            cl = get_column_letter(2 + j)
            c = st.cell(r, 2 + j, f'=IFERROR({cl}{r - 1}/{cl}{pos[("receita_usd_mi", "DIS")]},"")')
            c.number_format = F_PCT
    r += 1
    st.cell(r, 1, 'Fonte: reconciliação "segment operating income" → resultado antes de juros nos 10-K da Disney (AF2020, AF2022, AF2024, AF2025): '
                  'lucro dos segmentos − despesas corporativas − reestruturação e impairments − amortização TFCF/Hulu.').font = NOTA
    r += 2
    st.cell(r, 1, 'Resultado dos negócios de streaming dos concorrentes (US$ milhões) — enquanto a Netflix lucrava, os rivais perdiam').font = NEGRITO
    r += 1
    for j, h in enumerate(['Empresa', 'Ano fiscal', 'Métrica', 'Valor (US$ mi)', 'Fonte (documento SEC)', 'Nota']):
        c = st.cell(r, 1 + j, h)
        c.font, c.fill = Font(bold=True, color='FFFFFF'), CABEC
    r += 1
    for _, x in stream.iterrows():
        vals = [x['empresa'], int(x['ano_fiscal']), x['metrica'], float(x['valor_usd_mi']), x['fonte'], x['nota']]
        for j, val in enumerate(vals):
            c = st.cell(r, 1 + j, val)
            c.font = INPUT if j == 3 else FORM
            if j == 3:
                c.number_format = F_MI
        r += 1
    r += 1
    st.cell(r, 1, 'Netflix (para comparação): EBIT anual na tabela acima — US$ 4,6 bi (2020) → US$ 13,3 bi (2025).').font = NOTA
    st.column_dimensions['A'].width = 40
    for j in range(2, 12):
        st.column_dimensions[get_column_letter(j)].width = 13
    st.column_dimensions['C'].width = 40
    st.column_dimensions['E'].width = 38
    st.column_dimensions['F'].width = 60

    # ------------------------------------------------------------------ Variações bruscas
    vb = wb.create_sheet('Variacoes_Bruscas')
    vb.sheet_view.showGridLines = False
    vb['A1'], vb['A1'].font = 'Variações bruscas — "perguntas ruins" e as respostas oficiais', TITULO
    vb['A2'], vb['A2'].font = 'Cada resposta é sustentada por um trecho do documento arquivado na SEC (10-Q, 10-K ou carta aos acionistas, Ex. 99.1 do 8-K).', SUB
    cols = ['Trimestre', 'Indicador', 'Pergunta ruim', 'Resposta', 'Trecho oficial (inglês)', 'Documento', 'Accession SEC']
    for j, h in enumerate(cols):
        c = vb.cell(4, 1 + j, h)
        c.font, c.fill = Font(bold=True, color='FFFFFF'), CABEC
    for i, (_, x) in enumerate(eventos.iterrows()):
        for j, k in enumerate(['trimestre', 'indicador', 'pergunta_ruim', 'resposta', 'trecho_oficial', 'documento', 'accession_sec']):
            c = vb.cell(5 + i, 1 + j, x[k])
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.font = NEGRITO if k == 'pergunta_ruim' else (NOTA if k in ('trecho_oficial', 'accession_sec') else FORM)
            c.border = LINHA
    for j, w in enumerate([14, 18, 45, 60, 70, 24, 24]):
        vb.column_dimensions[get_column_letter(1 + j)].width = w
    vb.freeze_panes = 'C5'

    # ------------------------------------------------------------------ Validação
    va = wb.create_sheet('Validacao')
    va.sheet_view.showGridLines = False
    va['A1'], va['A1'].font = 'Validação — conferências contábeis', TITULO
    va['A2'], va['A2'].font = 'Maior desvio absoluto em um trimestre (US$ milhões). Tolerância: 1 (arredondamento entre balanço e notas na SEC).', SUB
    checks = [('DRE', 'chk_ebit', 'EBIT montado (receita − custos − despesas) = EBIT informado'),
              ('DRE', 'chk_lair', 'LAIR montado = LAIR informado'), ('DRE', 'chk_ll', 'Lucro líquido montado = informado'),
              ('BP', 'chk_bp', 'Ativo = Passivo + PL'), ('BP', 'chk_ac', 'Ativo circulante montado = informado'),
              ('BP', 'chk_pc', 'Passivo circulante: soma das linhas = total informado (resíduo de arredondamento)'),
              ('BP', 'chk_pt', 'Passivo não circulante: soma das linhas = PT − PC (resíduo de arredondamento)'),
              ('Indicadores', 'st_chk', 'Fleuriet: ST = CCL − NCG = disponibilidades − dívida CP')]
    for j, h in enumerate(['Conferência', 'Maior |desvio|', 'Status']):
        c = va.cell(4, 1 + j, h)
        c.font, c.fill = Font(bold=True, color='FFFFFF'), CABEC
    for i, (aba, k, rot) in enumerate(checks):
        va.cell(5 + i, 1, rot).font = FORM
        fx = Aba.registro[aba].faixa(k)
        c = va.cell(5 + i, 2, f'=MAX(MAX({fx}),-MIN({fx}))')
        c.number_format = '0.00'
        va.cell(5 + i, 3, f'=IF(B{5 + i}<=1,"OK","VERIFICAR")').font = NEGRITO
    r = 6 + len(checks)
    for linha in open(os.path.join(D, 'validacao_base.md'), encoding='utf-8').read().splitlines():
        va.cell(r, 1, linha.replace('**', '').replace('#', '').strip()).font = NOTA if not linha.startswith('#') else NEGRITO
        r += 1
    va.column_dimensions['A'].width = 110
    va.column_dimensions['B'].width = 14

    # ------------------------------------------------------------------ Fontes
    fo = wb.create_sheet('Fontes')
    fo.sheet_view.showGridLines = False
    fo['A1'], fo['A1'].font = 'Documentos oficiais usados (SEC EDGAR)', TITULO
    for j, h in enumerate(['Formulário', 'Período', 'Arquivado em', 'Accession', 'Link']):
        c = fo.cell(3, 1 + j, h)
        c.font, c.fill = Font(bold=True, color='FFFFFF'), CABEC
    for i, f in enumerate(manifest):
        url = f"https://www.sec.gov/Archives/edgar/data/1065280/{f['acc'].replace('-', '')}/{f['doc']}"
        for j, val in enumerate([f['form'], f['report'], f['filed'], f['acc'], url]):
            fo.cell(4 + i, 1 + j, val).font = FORM
    r = 5 + len(manifest)
    for t in ['Macro: Federal Reserve H.15 (federalreserve.gov/datadownload) · U.S. Treasury Daily Par Yield Curve (home.treasury.gov) · '
              'BLS API (api.bls.gov: CUUR0000SA0, LNS14000000) · Banco Central Europeu (data-api.ecb.europa.eu, EXR mensal).',
              'Concorrentes: 10-K de Disney (CIK 1744489), Warner Bros. Discovery (1437107), Paramount Global (813828), Comcast (1166691).',
              'Cartas aos acionistas da Netflix: Exhibit 99.1 dos 8-K de resultados (item 2.02), 2019-2026.']:
        fo.cell(r, 1, t).font = NOTA
        r += 1
    for j, w in enumerate([12, 12, 14, 24, 100]):
        fo.column_dimensions[get_column_letter(1 + j)].width = w

    # ------------------------------------------------------------------ Gráficos (nativos do Excel)
    gr = wb.create_sheet('Graficos', 1)
    gr.sheet_view.showGridLines = False
    gr['A1'], gr['A1'].font = 'Gráficos da análise (atualizam com as fórmulas)', TITULO
    gr['A2'], gr['A2'].font = 'Eixo X: trimestres · Um único eixo Y por gráfico, com unidade no título do eixo.', SUB

    def grafico(tipo, titulo, eixo_y, series, ancora, fmt_eixo='General', largura=24, altura=9):
        ch = LineChart() if tipo == 'linha' else BarChart()
        ch.title, ch.y_axis.title, ch.x_axis.title = titulo, eixo_y, 'Trimestre'
        # Sem overlay: título, títulos de eixo e legenda ocupam espaço próprio (não cobrem o gráfico)
        for t in (ch.title, ch.y_axis.title, ch.x_axis.title):
            t.overlay = False
        ch.width, ch.height = largura, altura
        if len(series) > 1:
            ch.legend.position, ch.legend.overlay = 'b', False
        else:
            ch.legend = None  # série única: o título já diz o que está plotado
        ch.varyColors = False
        ch.y_axis.number_format = fmt_eixo
        ch.y_axis.majorGridlines.spPr = GraphicalProperties(ln=LineProperties(solidFill=GRADE, w=6350))
        ch.x_axis.delete = False
        ch.y_axis.delete = False
        ch.x_axis.tickLblPos = 'low'
        for (aba, chave, cor, inicio) in series:
            a = Aba.registro[aba]
            rr = a.linhas[chave]
            dados = Reference(a.ws, min_col=3 + inicio, max_col=2 + n, min_row=rr, max_row=rr)
            ch.add_data(dados, from_rows=True, titles_from_data=False)
            s = ch.series[-1]
            from openpyxl.chart.series import SeriesLabel
            nome = a.ws.cell(rr, 1).value
            for prefixo in ('(=) ', '(−) ', '(+/−) '):
                nome = nome.removeprefix(prefixo)
            s.tx = SeriesLabel(v=nome.split(' (')[0] if len(nome) > 40 else nome)
            if tipo == 'linha':
                s.graphicalProperties.line.solidFill = cor
                s.graphicalProperties.line.width = 28575
                s.smooth = False
            else:
                s.graphicalProperties.solidFill = cor
                s.graphicalProperties.line.noFill = True
                s.invertIfNegative = False  # padrão do Excel pinta barras negativas de branco
        cats = Reference(Aba.registro[series[0][0]].ws, min_col=3 + series[0][3], max_col=2 + n, min_row=4, max_row=4)
        ch.set_categories(cats)
        if tipo == 'barra':
            ch.gapWidth = 60
        gr.add_chart(ch, ancora)

    grafico('linha', 'Receita líquida e EBIT', 'US$ milhões', [('DRE', 'receita', AZUL, 0), ('DRE', 'ebit', LARANJA, 0)], 'A4', '#,##0')
    grafico('barra', 'AH homóloga: crescimento da receita (t vs t−4)', 'Variação %', [('AH', 'yoy_receita', AZUL, 4)], 'A23', '0%')
    grafico('linha', 'Margens trimestrais (AV)', '% da receita', [('Indicadores', 'mg_bruta', AZUL, 0), ('Indicadores', 'mg_ebit', LARANJA, 0), ('Indicadores', 'mg_liq', VERDE_AGUA, 0)], 'A42', '0%')
    grafico('linha', 'Conteúdo: pagamentos em caixa x amortização na DRE', 'US$ milhões', [('DFC', 'gasto_cont', AZUL, 0), ('DFC', 'amort_cont', LARANJA, 0)], 'A61', '#,##0')
    grafico('barra', 'Fluxo de caixa livre (FCO − Capex)', 'US$ milhões', [('DFC', 'fcl', AZUL, 0)], 'A80', '#,##0')
    grafico('linha', 'Dívida líquida / EBITDA LTM', 'Múltiplo (x)', [('Indicadores', 'dl_ebitda', AZUL, 3)], 'A99', '0.0"x"')
    grafico('linha', 'Fleuriet: CCL, NCG e Saldo de Tesouraria', 'US$ milhões', [('Indicadores', 'ccl', AZUL, 0), ('Indicadores', 'ncg', LARANJA, 0), ('Indicadores', 'st', VERDE_AGUA, 0)], 'A118', '#,##0')
    grafico('linha', 'Dólar x receita: variação em 12 meses', 'Variação %', [('Macro', 'ah_dolar', AZUL, 4), ('Macro', 'ah_rec', LARANJA, 4)], 'A137', '0%')

    # ------------------------------------------------------------------ LEIA-ME
    leia.sheet_view.showGridLines = False
    textos = [
        ('Análise das Demonstrações Financeiras — Netflix, Inc. (NFLX) · ECO057', TITULO),
        (f'Período: {Q[0]} a {Q[-1]} ({n} trimestres) · Valores em US$ milhões, salvo indicação.', SUB),
        ('', None),
        ('Como ler esta planilha', NEGRITO),
        ('• Números em AZUL são dados oficiais (insumos). Números em PRETO são fórmulas — clique na célula para ver o cálculo.', FORM),
        ('• Linhas verdes são conferências: devem dar zero. O resumo está na aba Validacao.', FORM),
        ('• "n.d." = não disponível (ex.: indicador LTM precisa de 4 trimestres; AH homóloga precisa do mesmo trimestre do ano anterior).', FORM),
        ('', None),
        ('Abas (ordem sugerida para a apresentação)', NEGRITO),
        ('1. Macro e Setor — contexto: juros, inflação, câmbio e a situação dos concorrentes de streaming.', FORM),
        ('2. DRE, BP, DFC — demonstrações montadas a partir dos 10-Q/10-K, com conferência contra os totais informados à SEC.', FORM),
        ('3. AV — análise vertical (base: receita na DRE e ativo total no BP).', FORM),
        ('4. AH e AH_Anual — análise horizontal sequencial (t vs t−1), homóloga (t vs t−4), base fixa e anual.', FORM),
        ('5. Indicadores — margens, DuPont (ROA/ROE), liquidez, Fleuriet (CCL/NCG/ST), endividamento, GAO/GAF/GAT.', FORM),
        ('6. Regioes — receita, assinantes e ARM por região.', FORM),
        ('7. Variacoes_Bruscas — as "perguntas ruins", com resposta e trecho do documento oficial.', FORM),
        ('8. Graficos — gráficos nativos (eixos com título e unidade).', FORM),
        ('9. Validacao e Fontes — conferências e lista dos documentos usados (com links).', FORM),
        ('', None),
        ('Metodologia (igual à planilha da disciplina, "Planilhas ECO057.xlsx")', NEGRITO),
        ('• AV = conta / base.  AH = (Atual − Anterior) / ABS(Anterior) — o ABS evita inverter o sinal quando a base é negativa.', FORM),
        ('• DuPont: ROA = Margem líquida × Giro do ativo; ROE = ROA × MAF (Ativo/PL). Usa-se lucro e receita dos últimos 12 meses (LTM).', FORM),
        ('• Fleuriet: CCL = AC − PC; NCG = ACO − PCO; ST = CCL − NCG. Caixa e aplicações = ativo financeiro; dívida CP = passivo financeiro.', FORM),
        ('• Alavancagem (fórmula 1): GAO = Δ%EBIT/Δ%Receita; GAF = Δ%LL/Δ%EBIT; GAT = GAO × GAF.', FORM),
        ('', None),
        ('Tratamento dos dados (correções em relação à versão anterior do projeto)', NEGRITO),
        ('• Nenhum valor é estimado ou copiado do trimestre vizinho; lacunas ficam vazias. Antes havia preenchimento automático e "custo = 52% da receita" como reserva.', FORM),
        ('• 4º trimestre = ano do 10-K − 9 meses do 10-Q; Q2/Q3 do fluxo de caixa = acumulado − acumulado anterior.', FORM),
        ('• Imposto com sinal original; aplicações financeiras separadas do capital de giro operacional; contas de conteúdo incluídas.', FORM),
        ('• ROE e Dívida/EBITDA usam 12 meses reais (LTM), em vez de multiplicar o trimestre por 4.', FORM),
        ('• O lucro de 2026T1 é explicado pela multa rescisória da WBD (US$ 2,8 bi) — e não por "créditos fiscais", como constava antes.', FORM),
    ]
    for i, (t, f) in enumerate(textos):
        c = leia.cell(1 + i, 1, t)
        if f:
            c.font = f
    leia.column_dimensions['A'].width = 140

    wb.calculation.fullCalcOnLoad = True
    wb.save(SAIDA)
    print(f'-> Planilha salva: {SAIDA}')


if __name__ == '__main__':
    main()
