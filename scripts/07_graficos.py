"""
Etapa 7 - Gráficos para os slides (16:9, 300 DPI) em graficos_slides/, na ordem do roteiro:
macro e setor primeiro, depois a análise horizontal da Netflix e os indicadores.
Regras: um único eixo Y com título e unidade; eixo X com o ano marcado no 1º trimestre; vírgula decimal;
rótulos só nos pontos que contam a história; paleta validada (dataviz) — azul, laranja, verde-água, amarelo.
"""
import os

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from sec_common import ROOT

D = os.path.join(ROOT, 'dados')
OUT = os.path.join(ROOT, 'graficos_slides')
AZUL, LARANJA, VERDE_AGUA, AMARELO = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
TINTA, TINTA2, MUDO, GRADE, EIXO, FUNDO = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7', '#fcfcfb'

plt.rcParams.update({
    'font.family': ['Segoe UI', 'DejaVu Sans'], 'font.size': 11, 'axes.edgecolor': EIXO, 'axes.labelcolor': TINTA2,
    'xtick.color': TINTA2, 'ytick.color': TINTA2, 'axes.facecolor': FUNDO, 'figure.facecolor': FUNDO,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'axes.grid.axis': 'y',
    'grid.color': GRADE, 'grid.linewidth': 0.8, 'grid.linestyle': '-', 'lines.linewidth': 2.2,
    'legend.frameon': False, 'axes.titleweight': 'bold', 'axes.titlesize': 15, 'axes.titlelocation': 'left',
})


def br(fmt):
    """Formatador com vírgula decimal e ponto de milhar (padrão brasileiro)."""
    return mticker.FuncFormatter(lambda x, _: fmt.format(x).replace(',', 'X').replace('.', ',').replace('X', '.'))


def eixo_y(ax, fmt):
    """Formata o eixo Y e, para rótulos sem casas decimais, força tiques inteiros (evita 2,5 exibido como "2")."""
    ax.yaxis.set_major_formatter(br(fmt))
    if '.0f' in fmt:
        ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=8, integer=True, steps=[1, 2, 5, 10]))
    else:
        ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=8, steps=[1, 2, 2.5, 5, 10]))


def num_br(x, casas=1):
    return f'{x:,.{casas}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def figura(titulo, subtitulo, fonte):
    fig, ax = plt.subplots(figsize=(13.33, 7.0), dpi=300)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.84, bottom=0.17)
    fig.text(0.08, 0.94, titulo, fontsize=18, fontweight='bold', color=TINTA)
    fig.text(0.08, 0.895, subtitulo, fontsize=12, color=TINTA2)
    fig.text(0.08, 0.025, f'Fonte: {fonte}', fontsize=9, color=MUDO)
    return fig, ax


def eixo_trimestral(ax, trimestres):
    """Marca o ano no 1º trimestre e cada trimestre como tique menor — elimina os 26-30 rótulos inclinados."""
    x = np.arange(len(trimestres))
    t1 = [i for i, q in enumerate(trimestres) if q.endswith('T1')]
    ax.set_xticks(t1)
    ax.set_xticklabels([trimestres[i][:4] for i in t1])
    ax.set_xticks(x, minor=True)
    ax.tick_params(axis='x', which='minor', length=3, color=EIXO)
    ax.tick_params(axis='x', which='major', length=7, color=EIXO)
    ax.set_xlim(-0.6, len(trimestres) - 0.4)
    ax.set_xlabel('Trimestre (o rótulo marca o 1º trimestre de cada ano)', fontsize=10, color=MUDO)
    return x


def anotar(ax, x, y, texto, dx=0, dy=30, ha='center', em=None):
    """Rótulo com fio-guia; `em=(x, y)` posiciona o texto em coordenadas do gráfico (para usar espaços vazios)."""
    xytext, coords = (em, 'data') if em else ((dx, dy), 'offset points')
    ax.annotate(texto, (x, y), xytext=xytext, textcoords=coords, ha=ha, fontsize=9.5, color=TINTA2,
                arrowprops=dict(arrowstyle='-', color=MUDO, lw=0.8), bbox=dict(boxstyle='round,pad=0.25', fc=FUNDO, ec='none'))


def rotulo_fim(ax, x, y, texto, dy=0):
    ax.annotate(texto, (x, y), xytext=(6, dy), textcoords='offset points', va='center', fontsize=10, fontweight='bold', color=TINTA)


def salvar(fig, nome):
    p = os.path.join(OUT, nome)
    fig.savefig(p, dpi=300, facecolor=FUNDO)
    plt.close(fig)
    print('->', nome)


def main():
    os.makedirs(OUT, exist_ok=True)
    b = pd.read_csv(os.path.join(D, 'base_trimestral_nflx.csv'), index_col=0)
    m = pd.read_csv(os.path.join(D, 'macro_trimestral.csv'), index_col=0).reindex(b.index)
    r = pd.read_csv(os.path.join(D, 'regioes_nflx.csv'), index_col=0)
    s = pd.read_csv(os.path.join(D, 'streaming_concorrentes.csv'))
    se = pd.read_csv(os.path.join(D, 'setor_anual.csv'))
    Q = list(b.index)
    iq = {q: i for i, q in enumerate(Q)}
    ltm = lambda c: b[c].rolling(4).sum()
    fonte_sec = 'SEC EDGAR — 10-Q e 10-K da Netflix (XBRL). Elaboração própria.'

    # ---------------------------------------------------------------- 01 macro: juros e inflação
    fig, ax = figura('Juros e inflação nos EUA: o choque de 2022',
                     'Fed subiu os juros de ~0% para 5,3% para conter a inflação — média trimestral, % ao ano',
                     'Federal Reserve (H.15) e BLS (CPI-U). Elaboração própria.')
    x = eixo_trimestral(ax, Q)
    ax.plot(x, m['fed_funds_pct'], color=AZUL, label='Juro básico (Fed Funds efetivo)')
    ax.plot(x, m['inflacao_cpi_12m_pct'], color=LARANJA, label='Inflação ao consumidor (CPI, 12 meses)')
    ax.set_ylabel('% ao ano')
    eixo_y(ax, '{:.0f}%')
    ax.set_ylim(0, 10)
    anotar(ax, iq['2022T2'], m.loc['2022T2', 'inflacao_cpi_12m_pct'], 'Pico da inflação: 8,6%', dy=18)
    anotar(ax, iq['2023T4'], m.loc['2023T4', 'fed_funds_pct'], 'Pico: 5,33% (jul/2023 a set/2024)', dx=30, dy=40, ha='left')
    ax.legend(loc='upper left')
    salvar(fig, '01_macro_juros_inflacao.png')

    # ---------------------------------------------------------------- 02 macro: dólar x receita
    fig, ax = figura('Dólar forte reduz a receita da Netflix em dólares',
                     '~57% da receita vem de fora dos EUA e Canadá; quando o dólar sobe, a receita convertida cai',
                     'BCE (câmbio), SEC EDGAR (receita). Índice do dólar = média de EUR, BRL, MXN, GBP e JPY por US$.')
    x = eixo_trimestral(ax, Q)
    dol = (m['indice_dolar_cesta_2019T4_100'] / m['indice_dolar_cesta_2019T4_100'].shift(4) - 1) * 100
    rec = (b['receita'] / b['receita'].shift(4) - 1) * 100
    ax.axhline(0, color=EIXO, lw=1)
    ax.plot(x, rec, color=AZUL, label='Netflix: crescimento da receita em 12 meses')
    ax.plot(x, dol, color=LARANJA, label='Valorização do dólar em 12 meses')
    ax.set_ylabel('Variação em 12 meses (%)')
    eixo_y(ax, '{:.0f}%')
    anotar(ax, iq['2022T4'], rec['2022T4'], '2022T4: receita +2%\n(+10% em moeda constante)', dy=-60)
    anotar(ax, iq['2022T3'], dol['2022T3'], 'Euro na paridade', dy=25)
    ax.legend(loc='upper right')
    salvar(fig, '02_macro_dolar_receita.png')

    # ---------------------------------------------------------------- 03 setor: streaming dos rivais
    fig, ax = figura('Enquanto a Netflix lucrava, os rivais de streaming perdiam bilhões',
                     'Resultado operacional do negócio de streaming, por ano fiscal — US$ bilhões',
                     '10-K de Netflix, Disney (DTC), Warner Bros. Discovery (DTC/Streaming, EBITDA ajustado) e Paramount (DTC, OIBDA ajustado).')
    anos = [2021, 2022, 2023, 2024, 2025]
    nf = se[se['empresa'] == 'NFLX'].set_index('ano_fiscal')['ebit_usd_mi']
    series = [('Netflix (lucro operacional total)', AZUL, [nf.get(a, np.nan) for a in anos])]
    for emp, cor in [('Disney (Disney+, Hulu)', LARANJA), ('Warner Bros. Discovery (Max/HBO Max)', VERDE_AGUA),
                     ('Paramount (Paramount+, Pluto TV)', AMARELO)]:
        d = s[s['empresa'] == emp].set_index('ano_fiscal')['valor_usd_mi']
        series.append((emp, cor, [d.get(a, np.nan) for a in anos]))
    w = 0.19
    xa = np.arange(len(anos))
    for k, (nome, cor, vals) in enumerate(series):
        pos = xa + (k - 1.5) * w
        vals = np.array(vals, dtype=float) / 1000
        ax.bar(pos, vals, width=w * 0.92, color=cor, label=nome, zorder=3)
        for p_, v_ in zip(pos, vals):
            if not np.isnan(v_):
                ax.text(p_, v_ + (0.25 if v_ >= 0 else -0.25), num_br(v_), ha='center', va='bottom' if v_ >= 0 else 'top',
                        fontsize=8.5, color=TINTA2)
    ax.axhline(0, color=TINTA2, lw=1)
    ax.set_xticks(xa)
    ax.set_xticklabels([str(a) for a in anos])
    ax.set_xlabel('Ano fiscal (Disney: termina em set/out)', fontsize=10, color=MUDO)
    ax.set_ylabel('US$ bilhões')
    eixo_y(ax, '{:.0f}')
    ax.set_ylim(-5.5, 15.5)
    ax.legend(loc='upper left', ncol=2, fontsize=10)
    fig.text(0.08, 0.06, 'Sem barra = dado não disponível (Paramount 2025: fusão com a Skydance; WBD 2021: antes da fusão). Métricas dos rivais diferem: '
                         'comparar o sinal e a tendência, não o valor exato.', fontsize=9, color=MUDO)
    salvar(fig, '03_setor_streaming_rivais.png')

    # ---------------------------------------------------------------- 04 AH homóloga da receita
    fig, ax = figura('Análise horizontal: crescimento da receita contra o mesmo trimestre do ano anterior',
                     'AH homóloga = (trimestre − mesmo trimestre do ano anterior) / |ano anterior|',
                     fonte_sec)
    x = eixo_trimestral(ax, Q)
    ax.bar(x, rec, width=0.7, color=AZUL, zorder=3)
    ax.axhline(0, color=TINTA2, lw=1)
    ax.set_ylabel('Variação em 12 meses (%)')
    eixo_y(ax, '{:.0f}%')
    ax.set_ylim(0, 32)
    anotar(ax, iq['2020T1'], rec['2020T1'], 'Pandemia:\nconfinamento', dy=12)
    anotar(ax, iq['2022T4'], rec['2022T4'], 'Perda de assinantes\n+ dólar forte', dy=40)
    anotar(ax, iq['2023T4'], rec['2023T4'], 'Compartilhamento pago\n+ plano com anúncios', em=(iq['2023T2'], 22))
    ax.text(iq['2019T2'] + 0.5, 1, '2019: sem ano anterior\npara comparar', ha='center', fontsize=9, color=MUDO)
    rotulo_fim(ax, x[-1], rec.iloc[-1], f'{num_br(rec.iloc[-1])}%', dy=8)
    salvar(fig, '04_ah_receita_homologa.png')

    # ---------------------------------------------------------------- 05 receita, EBIT e lucro
    fig, ax = figura('Receita, lucro operacional e lucro líquido por trimestre',
                     'O lucro líquido se descola do EBIT em eventos não operacionais — US$ bilhões', fonte_sec)
    x = eixo_trimestral(ax, Q)
    ax.plot(x, b['receita'] / 1000, color=AZUL, label='Receita líquida')
    ax.plot(x, b['ebit'] / 1000, color=LARANJA, label='Lucro operacional (EBIT)')
    ax.plot(x, b['lucro_liquido'] / 1000, color=VERDE_AGUA, label='Lucro líquido')
    ax.set_ylabel('US$ bilhões')
    eixo_y(ax, '{:.0f}')
    ax.set_ylim(0, 14)
    anotar(ax, iq['2022T4'], b.loc['2022T4', 'lucro_liquido'] / 1000, 'Perda cambial na dívida\nem euro (US$ 462 mi)', dy=55)
    anotar(ax, iq['2026T1'], b.loc['2026T1', 'lucro_liquido'] / 1000, 'Multa rescisória\nda WBD (US$ 2,8 bi)', dx=-60, dy=40)
    for col, dy in [('receita', 0), ('ebit', 6), ('lucro_liquido', -6)]:
        rotulo_fim(ax, x[-1], b[col].iloc[-1] / 1000, num_br(b[col].iloc[-1] / 1000, 2), dy=dy)
    ax.legend(loc='upper left')
    salvar(fig, '05_receita_ebit_lucro.png')

    # ---------------------------------------------------------------- 06 margens
    mg = pd.DataFrame({'bruta': (b['receita'] - b['custo_servicos']) / b['receita'] * 100,
                       'ebit': b['ebit'] / b['receita'] * 100, 'liq': b['lucro_liquido'] / b['receita'] * 100})
    fig, ax = figura('Análise vertical: margens trimestrais',
                     'Cada linha é a conta dividida pela receita do trimestre — % da receita', fonte_sec)
    x = eixo_trimestral(ax, Q)
    ax.plot(x, mg['bruta'], color=AZUL, label='Margem bruta')
    ax.plot(x, mg['ebit'], color=LARANJA, label='Margem operacional (EBIT)')
    ax.plot(x, mg['liq'], color=VERDE_AGUA, label='Margem líquida')
    ax.set_ylabel('% da receita')
    eixo_y(ax, '{:.0f}%')
    ax.set_ylim(0, 60)
    anotar(ax, iq['2022T4'], mg.loc['2022T4', 'ebit'], 'Todo 4º tri a margem cai:\ngrandes lançamentos de fim de ano', em=(iq['2022T4'], 52))
    anotar(ax, iq['2025T3'], mg.loc['2025T3', 'ebit'], 'Imposto no Brasil\n(US$ 619 mi)', em=(iq['2025T2'], 8))
    ax.legend(loc='upper left', ncol=3)
    salvar(fig, '06_margens.png')

    # ---------------------------------------------------------------- 07 conteúdo: caixa x amortização
    fig, ax = figura('Por que o caixa oscila: pagamento de conteúdo x amortização',
                     'Conteúdo é pago antes e amortizado depois; quando o pagamento supera a amortização, o caixa sofre — US$ bilhões',
                     'SEC EDGAR — contas próprias da Netflix (nflx:AdditionsToStreamingContentAssets e amortização). Elaboração própria.')
    x = eixo_trimestral(ax, Q)
    ax.plot(x, b['gasto_caixa_conteudo'] / 1000, color=AZUL, label='Pagamentos de conteúdo (caixa)')
    ax.plot(x, b['amort_conteudo'] / 1000, color=LARANJA, label='Amortização de conteúdo (DRE)')
    ax.set_ylabel('US$ bilhões')
    eixo_y(ax, '{:.0f}')
    ax.set_ylim(0, 6.5)
    anotar(ax, iq['2020T2'], b.loc['2020T2', 'gasto_caixa_conteudo'] / 1000, 'Covid: produções\nparadas', dy=-55)
    anotar(ax, iq['2021T4'], b.loc['2021T4', 'gasto_caixa_conteudo'] / 1000, 'Retomada: pagamento\n1,5x a amortização', dy=20)
    anotar(ax, iq['2023T1'], b.loc['2023T1', 'gasto_caixa_conteudo'] / 1000, 'Greves de roteiristas\ne atores (2023)', dy=-55)
    ax.legend(loc='upper left')
    salvar(fig, '07_conteudo_caixa_amortizacao.png')

    # ---------------------------------------------------------------- 08 FCL
    fcl = (b['fco'] - b['capex']) / 1000
    fig, ax = figura('Fluxo de caixa livre por trimestre',
                     'FCL = fluxo de caixa operacional − compras de imobilizado — US$ bilhões', fonte_sec)
    x = eixo_trimestral(ax, Q)
    ax.bar(x, fcl, width=0.7, color=[AZUL if v >= 0 else LARANJA for v in fcl], zorder=3)
    ax.axhline(0, color=TINTA2, lw=1)
    ax.set_ylabel('US$ bilhões')
    eixo_y(ax, '{:.0f}')
    anotar(ax, iq['2021T4'], fcl['2021T4'], 'Queima de caixa\nem 2021', dy=-45)
    anotar(ax, iq['2026T1'], fcl['2026T1'], 'Multa da WBD', dx=-40, dy=10)
    anotar(ax, iq['2026T2'], fcl['2026T2'], 'Impostos\nsobre a multa', dx=15, dy=35)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=AZUL, label='Positivo (gera caixa)'), Patch(color=LARANJA, label='Negativo (queima caixa)')],
              loc='upper left')
    salvar(fig, '08_fluxo_caixa_livre.png')

    # ---------------------------------------------------------------- 09 assinantes
    ass = r['assinantes_total']
    adic = ass.diff()
    fig, ax = figura('Assinantes pagos: adições líquidas por trimestre',
                     'Milhões de assinantes adicionados no trimestre (a Netflix parou de divulgar em 2025)',
                     'SEC EDGAR — notas dos 10-Q/10-K (assinantes por região). Elaboração própria.')
    x = eixo_trimestral(ax, Q)
    ax.bar(x, adic, width=0.7, color=[AZUL if v >= 0 else LARANJA for v in adic.fillna(0)], zorder=3)
    ax.axhline(0, color=TINTA2, lw=1)
    ax.set_ylabel('Milhões de assinantes')
    eixo_y(ax, '{:.0f}')
    anotar(ax, iq['2020T1'], adic['2020T1'], 'Confinamento:\n+15,8 mi', dy=5)
    ax.annotate('1ª perda em mais de 10 anos\n(−0,2 e −1,0 mi)', (iq['2022T2'], adic['2022T2']), xytext=(iq['2022T1'], 13),
                textcoords='data', ha='center', fontsize=9.5, color=TINTA2,
                arrowprops=dict(arrowstyle='-', color=MUDO, lw=0.8), bbox=dict(boxstyle='round,pad=0.25', fc=FUNDO, ec='none'))
    anotar(ax, iq['2024T4'], adic['2024T4'], '+18,9 mi (recorde)', dx=-70, dy=8, ha='right')
    ultimo = ass.last_valid_index()
    ax.axvspan(iq[ultimo] + 0.5, len(Q) - 0.4, color=GRADE, alpha=0.5, lw=0)
    ax.text((iq[ultimo] + len(Q)) / 2, 2, 'Não\ndivulgado', ha='center', fontsize=9.5, color=TINTA2)
    salvar(fig, '09_assinantes.png')

    # ---------------------------------------------------------------- 10 Fleuriet
    ccl = b['ativo_circulante'] - b['passivo_circulante']
    ncg = b['outros_ativos_circ'] - (b['passivo_circulante'] - b['divida_cp'])
    st = ccl - ncg
    fig, ax = figura('Modelo Fleuriet: a NCG é negativa — clientes e fornecedores financiam a operação',
                     'CCL = AC − PC; NCG = ativo − passivo circulante operacional; ST = CCL − NCG — US$ bilhões', fonte_sec)
    x = eixo_trimestral(ax, Q)
    ax.axhline(0, color=TINTA2, lw=1)
    ax.plot(x, ccl / 1000, color=AZUL, label='CCL (capital circulante líquido)')
    ax.plot(x, ncg / 1000, color=LARANJA, label='NCG (necessidade de capital de giro)')
    ax.plot(x, st / 1000, color=VERDE_AGUA, label='ST (saldo de tesouraria)')
    ax.set_ylabel('US$ bilhões')
    eixo_y(ax, '{:.0f}')
    for serie, dy in [(ccl, 0), (ncg, 0), (st, 0)]:
        rotulo_fim(ax, x[-1], serie.iloc[-1] / 1000, num_br(serie.iloc[-1] / 1000), dy=dy)
    ax.legend(loc='upper left', ncol=3)
    salvar(fig, '10_fleuriet.png')

    # ---------------------------------------------------------------- 11 DL/EBITDA
    dl = b['divida_cp'] + b['divida_lp'] - b['caixa'] - b['aplicacoes_cp']
    dl_eb = dl / ltm('ebit').add(ltm('depreciacao_amort'))
    fig, ax = figura('Endividamento: dívida líquida / EBITDA dos últimos 12 meses',
                     'Quantos anos de geração operacional pagariam a dívida líquida — múltiplo (x)', fonte_sec)
    x = eixo_trimestral(ax, Q)
    ax.plot(x, dl_eb, color=AZUL, marker='o', markersize=4)
    ax.set_ylabel('Múltiplo (x)')
    eixo_y(ax, '{:.1f}x')
    ax.set_ylim(0, max(4.0, dl_eb.max() * 1.15))
    i0 = dl_eb.first_valid_index()
    anotar(ax, iq[i0], dl_eb[i0], f'{i0}: {num_br(dl_eb[i0], 2)}x', dx=25, dy=15, ha='left')
    rotulo_fim(ax, x[-1], dl_eb.iloc[-1], f'{num_br(dl_eb.iloc[-1], 2)}x', dy=10)
    ax.text(0.99, 0.95, 'Primeiros 3 trimestres sem valor: o EBITDA de 12 meses exige 4 trimestres de dados.',
            transform=ax.transAxes, ha='right', fontsize=9, color=MUDO)
    salvar(fig, '11_divida_liquida_ebitda.png')

    # ---------------------------------------------------------------- 12 ROE DuPont
    roe = ltm('lucro_liquido') / b['patrimonio_liquido'] * 100
    roa = ltm('lucro_liquido') / b['ativo_total'] * 100
    fig, ax = figura('Retorno: ROE e ROA (DuPont), lucro dos últimos 12 meses',
                     'ROE = ROA × (Ativo/PL); lucro de 12 meses evita multiplicar o trimestre por 4 — %', fonte_sec)
    x = eixo_trimestral(ax, Q)
    ax.plot(x, roe, color=AZUL, label='ROE (lucro 12m / patrimônio líquido)')
    ax.plot(x, roa, color=LARANJA, label='ROA (lucro 12m / ativo total)')
    ax.set_ylabel('% (12 meses)')
    eixo_y(ax, '{:.0f}%')
    ax.set_ylim(0, 60)
    rotulo_fim(ax, x[-1], roe.iloc[-1], f'{num_br(roe.iloc[-1])}%')
    rotulo_fim(ax, x[-1], roa.iloc[-1], f'{num_br(roa.iloc[-1])}%')
    anotar(ax, iq['2026T1'], roe['2026T1'], 'Inclui a multa\nda WBD', dx=-50, dy=20)
    ax.legend(loc='upper left')
    salvar(fig, '12_roe_roa.png')

    # ---------------------------------------------------------------- 13 liquidez corrente
    lc = b['ativo_circulante'] / b['passivo_circulante']
    fig, ax = figura('Liquidez corrente', 'Ativo circulante / passivo circulante — índice (x)', fonte_sec)
    x = eixo_trimestral(ax, Q)
    ax.axhline(1, color=TINTA2, lw=1)
    ax.text(0, 1.02, 'AC = PC (1,0x)', fontsize=9, color=TINTA2, va='bottom')
    ax.plot(x, lc, color=AZUL, marker='o', markersize=4)
    ax.set_ylabel('Índice (x)')
    eixo_y(ax, '{:.1f}x')
    ax.set_ylim(0, 2)
    rotulo_fim(ax, x[-1], lc.iloc[-1], f'{num_br(lc.iloc[-1], 2)}x', dy=10)
    salvar(fig, '13_liquidez_corrente.png')


if __name__ == '__main__':
    main()
