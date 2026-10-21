"""
Etapa 4 - Catálogo das variações bruscas: para cada uma, a "pergunta ruim" (desconfortável para a empresa),
a resposta e o trecho oficial que a sustenta, extraído automaticamente do 10-Q/10-K ou da carta aos acionistas.
Saída: dados/eventos_variacoes.csv (usado na planilha e no roteiro da apresentação).
"""
import os

import pandas as pd

from sec_common import ROOT
from texto_relatorios import search

SAIDA = os.path.join(ROOT, 'dados')

# (trimestre, indicador, pergunta, resposta, documento, padrão de busca do trecho oficial)
EVENTOS = [
    ('2020T2', 'FCO e FCL', 'Como o caixa operacional saltou de US$ 0,26 bi para US$ 1,04 bi no meio da pandemia?',
     'As produções pararam (Covid-19): o gasto de caixa com conteúdo caiu 24% no trimestre e ficou abaixo da '
     'amortização (0,96x), enquanto o confinamento trouxe 26 milhões de novos assinantes no 1º semestre.',
     'q220', r'restart our productions'),
    ('2021T2-2021T4', 'FCL negativo', 'Por que a Netflix lucrou US$ 5,1 bi em 2021 e mesmo assim queimou caixa?',
     'Com a retomada das produções, o pagamento de conteúdo superou a amortização contábil em US$ 5,2 bi. '
     'Lucro (competência) e caixa se descolaram: o conteúdo é pago antes e amortizado ao longo de anos.',
     '2021-12-31', r'Free cash flow was \$5,275 million lower'),
    ('Todo T4', 'Margem operacional', 'Por que a margem operacional despenca em todo 4º trimestre (8% em 2021T4, 7% em 2022T4)?',
     'Sazonalidade planejada: a Netflix concentra os grandes lançamentos (e a amortização e o marketing deles) no fim do ano. '
     'Por isso a comparação correta é contra o mesmo trimestre do ano anterior (AH homóloga).',
     'q421', r'decline in operating margin was expected'),
    ('2022T1-2022T2', 'Assinantes', 'Por que a Netflix perdeu assinantes pela primeira vez em mais de uma década?',
     'Saída da Rússia (-0,7 mi), aquisição fraca em todas as regiões, compartilhamento de senhas e pressão macro '
     '(inflação, guerra). Foram -0,2 mi no 1º tri e -0,97 mi no 2º tri de 2022.',
     'q122', r'suspension of our service in Russia'),
    ('2022T2-2022T4', 'Receita (câmbio)', 'Por que a receita cresceu só 2% no 4º tri/2022 e a receita da EMEA caiu ao longo de 2022?',
     'Dólar forte: o euro chegou à paridade e o índice do dólar contra as moedas das regiões da Netflix subiu ~16% vs. 2019. '
     'Em moeda constante a receita cresceu 10%.',
     'q422', r'10% on a foreign exchange'),
    ('2022T4', 'Lucro líquido', 'Por que o lucro do 4º tri/2022 caiu 96% (US$ 55 mi), se o EBIT foi de US$ 550 mi?',
     'Perda cambial não-caixa de US$ 462 mi na remensuração da dívida em euros (o dólar se desvalorizou no trimestre), '
     'somada à margem sazonalmente baixa do T4.',
     'q422', r'\$462M non-cash unrealized loss'),
    ('2022-2023', 'Despesa de juros', 'O Fed subiu os juros de ~0% para 5,3%: por que a despesa financeira da Netflix não subiu?',
     'Toda a dívida está em notas de taxa fixa emitidas antes do ciclo de alta; a despesa de juros ficou estável '
     '(US$ 170-195 mi por trimestre até 2025T3). O salto pontual em 2025T4-2026T1 (US$ 234-262 mi) coincide com o '
     'empréstimo-ponte de US$ 59 bi contratado em 04/12/2025 para a compra da WBD, e volta ao normal em 2026T2.',
     '2022-12-31', r'fixed rate'),
    ('2023', 'FCO e FCL', 'Como o caixa livre de 2023 (US$ 6,9 bi) superou o lucro, se a receita só cresceu 7%?',
     'As greves de roteiristas (WGA) e atores (SAG-AFTRA) pararam as produções: a amortização superou o gasto de caixa '
     'com conteúdo em US$ 1,06 bi. Caixa reforçado temporariamente, não recorrente.',
     '2023-12-31', r'Free cash flow was \$1,518 million higher'),
    ('2023T3-2023T4', 'Patrimônio líquido', 'Por que o patrimônio líquido encolheu no 2º semestre de 2023, com a empresa lucrando?',
     'Recompra de ações de US$ 5 bi no semestre (US$ 6 bi no ano): devolução de caixa ao acionista maior que o lucro do período.',
     '2023-12-31', r'repurchased [\d,.]+ (million )?shares'),
    ('2023T3-2024T4', 'Receita', 'O que fez a receita voltar a crescer mais de 15% ao ano a partir de 2024?',
     'Compartilhamento pago (bloqueio de senhas, mai/2023 em 100+ países), plano com anúncios (nov/2022) e reajustes de preço. '
     'Os assinantes saltaram de 238 mi (2023T2) para 302 mi (2024T4).',
     'q223', r'launched paid sharing'),
    ('2025T3', 'Margem operacional', 'Por que a margem do 3º tri/2025 (28%) ficou abaixo da meta de 31,5%?',
     'Despesa de ~US$ 619 mi com disputa de tributos (não sobre a renda) no Brasil, reconhecida de uma vez no trimestre.',
     'q325', r'Brazilian tax authorities'),
    ('2026T1', 'Lucro líquido > EBIT', 'Como o lucro líquido do 1º tri/2026 (US$ 5,28 bi) superou o lucro operacional (US$ 3,96 bi)?',
     'Multa rescisória de US$ 2,8 bi paga à Netflix (pela Paramount Skydance, em nome da WBD) quando a WBD desistiu da venda '
     'para a Netflix. Não é recorrente nem operacional.',
     '2026-03-31', r'termination fee received was recorded'),
    ('2026T2', 'FCO', 'Por que o caixa operacional caiu 67% no 2º tri/2026?',
     'Pagamento de impostos sobre a multa rescisória recebida no trimestre anterior; a operação seguiu crescendo (margem 33,4%).',
     'q226', r'higher cash tax payments'),
    ('2019-2020T1, 2021T4, 2024T2', 'Fleuriet (tipo VI)', 'Se a Netflix tem caixa de sobra, por que o modelo Fleuriet a classifica como "alto risco" em alguns trimestres?',
     'Nesses trimestres o CCL ficou negativo (passivo circulante > ativo circulante): o saldo de tesouraria positivo era sustentado '
     'por obrigações de curto prazo — conteúdo a pagar, receita recebida antecipadamente e, em 2024T2, US$ 1,8 bi de dívida vencendo em 12 meses. '
     'Funciona enquanto a empresa cresce e recebe antes de pagar; desde 2024T3 a estrutura é do tipo I (excelente).',
     None, None),
    ('2025 em diante', 'Assinantes', 'Por que a Netflix parou de divulgar o número de assinantes?',
     'Decisão anunciada em abr/2024: com planos e preços diferentes por país, cada assinante tem impacto distinto na receita. '
     'Limitação da análise: a partir de 2025 só há receita por região.',
     'q124', r'stop reporting quarterly membership'),
]


def main():
    linhas = []
    for tri, ind, perg, resp, ref, padrao in EVENTOS:
        if ref is None:  # evidência é o próprio cálculo da planilha
            linhas.append({'trimestre': tri, 'indicador': ind, 'pergunta_ruim': perg, 'resposta': resp,
                           'trecho_oficial': '', 'documento': 'Cálculo próprio — aba Indicadores (Fleuriet)', 'accession_sec': ''})
            continue
        f, hits = search(ref, padrao, width=220, limit=1)
        trecho = hits[0].strip() if hits else ''
        if not trecho:
            print(f'!! Trecho não encontrado: {ref} / {padrao}')
        linhas.append({'trimestre': tri, 'indicador': ind, 'pergunta_ruim': perg, 'resposta': resp,
                       'trecho_oficial': trecho, 'documento': f"{f['form']} {f['report']}", 'accession_sec': f['acc']})
    df = pd.DataFrame(linhas)
    df.to_csv(os.path.join(SAIDA, 'eventos_variacoes.csv'), index=False, encoding='utf-8-sig')
    print(f'-> {len(df)} eventos; {sum(df["trecho_oficial"] != "")} com trecho oficial localizado '
          f'({sum(df["accession_sec"] == "")} baseados em cálculo próprio).')


if __name__ == '__main__':
    main()
