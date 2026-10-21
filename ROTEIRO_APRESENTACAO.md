# Roteiro da apresentação: análise horizontal da Netflix (ECO057)

**Período analisado:** 2019T1 a 2026T2 (30 trimestres).
**Fontes:** só oficiais: SEC EDGAR (10-Q, 10-K e cartas aos acionistas), Federal Reserve, Tesouro dos EUA, BLS e Banco Central Europeu.
**Onde estão os números:** todos estão na planilha `Analise_Netflix_ECO057.xlsx`, em fórmulas. Os gráficos estão em `graficos_slides/`.

A lógica da história é **contexto → crescimento → o que quebrou o padrão → saúde financeira → conclusão**. O macro e o setor abrem a apresentação para que cada variação brusca apareça já explicada pelo ambiente.

---

## Bloco 1: contexto macroeconômico e setorial (abertura)

### Slide 1: a empresa em uma frase
- **Mensagem:** a Netflix é a maior plataforma de streaming por assinatura.
  - A receita foi de US$ 20,2 bi em 2019 para US$ 45,2 bi em 2025, ou seja, 2,2 vezes.
  - Por região: 43% vem de EUA e Canadá, 32% da EMEA, 13% da América Latina e 12% da Ásia-Pacífico (2026T2).
  - Em 2019 os EUA e o Canadá eram 50% e a Ásia-Pacífico só 7%: a empresa ficou mais global.
- **Planilha:** aba `Regioes`, linhas "Participação na receita (AV)".

### Slide 2: juros e inflação (`01_macro_juros_inflacao.png`)
- **Mensagem:** de 2022 a 2024 o custo do dinheiro saiu de ~0% para 5,3% ao ano, com a inflação dos EUA no pico de 8,6% em 2022T2.
- **Ponte para a Netflix:** mesmo assim a **despesa de juros não subiu**. Ela ficou em US$ 170–195 mi por trimestre, porque a dívida é toda em notas de taxa fixa. O choque chegou pelo consumidor e pelo câmbio, não pelos juros da empresa.
- **Planilha:** aba `Macro`, com Fed Funds, Treasury de 10 anos, inflação e desemprego, mais a linha "despesa de juros".

### Slide 3: câmbio (`02_macro_dolar_receita.png`)
- **Mensagem:** ~57% da receita vem de fora dos EUA e do Canadá. Quando o dólar se valoriza, a receita convertida encolhe.
- **O caso mais forte é o 2022T4:** a receita cresceu só 2% em dólares, mas 10% em moeda constante, segundo a carta aos acionistas. Em 2022 o euro chegou à paridade com o dólar.
- **Planilha:** aba `Macro` (índice do dólar e variação em 12 meses) e aba `Regioes` (AH da receita da EMEA).

### Slide 4: setor, a "guerra do streaming" (`03_setor_streaming_rivais.png`)
- **Mensagem:** entre 2021 e 2023 os rivais **perdiam bilhões** no streaming, enquanto a Netflix lucrava de US$ 5,6 a 7,0 bi por ano.
  - **Disney** (Disney+ e Hulu): −1,3 bi (2021), −3,4 bi (2022) e −2,5 bi (2023).
  - **Paramount+:** −1,0 bi (2021), −1,8 bi (2022), −1,7 bi (2023) e −0,5 bi (2024).
  - **WBD:** −1,6 bi em 2022.
- **Quando os rivais viraram:** só em 2024–25 eles chegaram perto de zero ou ao lucro, e mesmo assim por volta de US$ 1,3–1,4 bi, contra US$ 13,3 bi da Netflix.
- **Ressalva para dizer em voz alta:** as métricas dos rivais diferem (resultado operacional, EBITDA ajustado ou OIBDA ajustado). O que vale comparar é o **sinal e a tendência**.
- **Planilha:** aba `Setor`, com receita, EBIT, crescimento e margem das 5 empresas e a tabela dos segmentos de streaming com a fonte de cada número.

---

## Bloco 2: análise horizontal (o núcleo do trabalho)

### Slide 5: crescimento da receita, AH homóloga (`04_ah_receita_homologa.png`)
- **Por que homóloga (t vs t−4):** a Netflix tem sazonalidade forte, com o 4º tri sempre diferente. Comparar com o mesmo trimestre do ano anterior isola a tendência.
- **Fórmula (igual à da disciplina):** (Atual − Anterior) / ABS(Anterior).
- **As três fases:**
  1. **2020:** crescimento de 21% a 28% (pandemia).
  2. **2022:** desaceleração até 2% (perda de assinantes e dólar forte).
  3. **2024 em diante:** volta a 12%–18% (compartilhamento pago e plano com anúncios).
- **Planilha:** aba `AH`, blocos "AH homóloga", "AH sequencial" e "base fixa 2019T4 = 100". As cores destacam variações acima de 50%.

### Slide 6: AH anual, a visão de longo prazo
- **Planilha:** aba `AH_Anual`. A tabela a levar:

| Ano | Receita | AH Receita | EBIT | AH EBIT | Lucro líquido | AH LL |
|---|---|---|---|---|---|---|
| 2020 | 25,0 | +24,0% | 4,6 | +76,1% | 2,8 | +47,9% |
| 2021 | 29,7 | +18,8% | 6,2 | +35,1% | 5,1 | +85,3% |
| 2022 | 31,6 | +6,5% | 5,6 | −9,1% | 4,5 | −12,2% |
| 2023 | 33,7 | +6,7% | 7,0 | +23,5% | 5,4 | +20,4% |
| 2024 | 39,0 | +15,6% | 10,4 | +49,8% | 8,7 | +61,1% |
| 2025 | 45,2 | +15,9% | 13,3 | +27,9% | 11,0 | +26,1% |
| 1S2026 vs 1S2025 | 24,8 | +14,7% | 8,1 | +14,4% | 8,7 | +44,4%* |

Valores em US$ bilhões. *Inclui a multa rescisória da WBD (US$ 2,8 bi).

- **Leitura:** o EBIT cresce mais rápido que a receita, o que é alavancagem operacional. A exceção é 2022, quando a receita subiu 6,5% e o EBIT caiu 9,1%.

### Slide 7: receita, EBIT e lucro (`05_receita_ebit_lucro.png`)
- **Mensagem:** a receita sobe quase em linha reta. O lucro líquido se descola do EBIT em **dois eventos não operacionais**:
  - **2022T4:** perda cambial de US$ 462 mi na dívida em euro.
  - **2026T1:** multa rescisória de US$ 2,8 bi da WBD.

### Slide 8: análise vertical, margens (`06_margens.png`)
- **Mensagem:**
  - **Tendência:** a margem operacional subiu de 12,9% (2019) para 29,5% (2025) e 32,9% no 1S2026. É escala: o conteúdo é custo quase fixo, diluído por mais receita.
  - **Quebras de padrão:** **todo 4º tri** (grandes lançamentos de fim de ano) e o **2025T3** (imposto no Brasil, US$ 619 mi).
- **Planilha:** aba `AV`, com a DRE em % da receita e o BP em % do ativo total.

### Slide 9: graus de alavancagem (GAO, GAF, GAT)
- **Planilha:** aba `AH_Anual` para a versão anual e aba `Indicadores` para a trimestral homóloga. As fórmulas são as da disciplina:
  - GAO = Δ%EBIT / Δ%Receita
  - GAF = Δ%LL / Δ%EBIT
  - GAT = GAO × GAF

| Ano | GAO | GAF | Como ler |
|---|---|---|---|
| 2020 | 3,17 | 0,63 | Escala forte; lucro contido por perda cambial (−US$ 618 mi em "outras") |
| 2021 | 1,87 | 2,43 | Ganho cambial de US$ 411 mi turbinou o lucro líquido |
| 2022 | −1,40 | 1,35 | Receita +6,5%, mas amortização de conteúdo +14,7% e tecnologia +19,2%: EBIT caiu |
| 2023 | 3,52 | 0,87 | Volta da alavancagem operacional |
| 2024 | 3,18 | 1,23 | Compartilhamento pago: receita nova com custo quase fixo |
| 2025 | 1,76 | 0,93 | Alavancagem menor (o imposto do Brasil pesou) |

- **Cuidado ao explicar:** a elasticidade "explode" quando a variação do denominador é perto de zero. Por isso usamos a base anual ou a homóloga, nunca a sequencial.

---

## Bloco 3: as perguntas ruins (variações bruscas)

A aba `Variacoes_Bruscas` traz 15 casos, cada um com a pergunta, a resposta e o **trecho oficial** do documento (com número de accession da SEC). Os seis mais fortes para a apresentação:

| # | Pergunta ruim | Resposta curta | Gráfico |
|---|---|---|---|
| 1 | Por que a Netflix lucrou US$ 5,1 bi em 2021 e queimou caixa? | Produções retomadas: pagou US$ 5,2 bi a mais de conteúdo do que amortizou | `07`, `08` |
| 2 | Como o caixa explodiu em 2023 (FCL de US$ 6,9 bi) com a receita crescendo só 7%? | Greves de roteiristas e atores pararam produções; caixa temporário, não recorrente | `07` |
| 3 | Por que a Netflix perdeu assinantes em 2022, pela 1ª vez em mais de 10 anos? | Saída da Rússia (−0,7 mi), concorrência, senhas compartilhadas e inflação | `09` |
| 4 | Por que o lucro do 2022T4 caiu 96% (US$ 55 mi) com EBIT de US$ 550 mi? | Perda cambial não-caixa de US$ 462 mi na dívida em euro | `05` |
| 5 | Como o lucro do 2026T1 (5,28 bi) superou o EBIT (3,96 bi)? | Multa rescisória de US$ 2,8 bi quando a WBD trocou a Netflix pela Paramount Skydance | `05`, `08` |
| 6 | Se sobra caixa, por que o Fleuriet aponta "alto risco" em 2019, 2021T4 e 2024T2? | CCL negativo: o caixa era sustentado por obrigações de curto prazo | `10` |

### Slide 10: conteúdo, caixa x amortização (`07_conteudo_caixa_amortizacao.png`)
- **Este é o slide-chave para explicar o caixa.**
  - **O mecanismo:** a Netflix **paga** o conteúdo antes e o **amortiza** na DRE ao longo de anos. Quando a linha azul (pagamento) fica acima da laranja (amortização), o lucro é maior que o caixa.
  - **2020:** pagamentos caíram (produções paradas).
  - **2021:** pagamentos chegaram a 1,5x a amortização.
  - **2023:** pagamentos caíram de novo (greves).

### Slide 11: fluxo de caixa livre (`08_fluxo_caixa_livre.png`)
- **De 2019 a 2021:** a empresa queimava caixa (FCL de −US$ 3,1 bi em 2019).
- **De 2023 em diante:** passou a gerar US$ 6,9 bi a 9,5 bi por ano.
- **Destino do caixa:** recompra de ações de US$ 6,0 bi (2023), 6,3 bi (2024) e 9,1 bi (2025).

### Slide 12: assinantes (`09_assinantes.png`)
- **Picos:** o confinamento de 2020T1 (+15,8 mi) e o recorde de 2024T4 (+18,9 mi).
- **Vale:** as perdas de 2022.
- **Limitação a declarar:** a Netflix parou de divulgar assinantes em 2025. A empresa justificou que, com preços diferentes por país, cada assinante pesa diferente na receita.

---

## Bloco 4: saúde financeira

### Slide 13: Fleuriet (`10_fleuriet.png`)
- **NCG negativa em todos os 30 trimestres** (entre −US$ 4,7 bi e −6,4 bi): clientes pagam antes e fornecedores de conteúdo recebem depois. A operação **gera** capital de giro em vez de consumi-lo.
- **Tipo de estrutura:**
  - **Tipo I (excelente)** na maior parte do período.
  - **Tipo VI (alto risco)** quando o CCL ficou negativo. É a pergunta ruim nº 6.
- **Planilha:** aba `Indicadores`, linhas CCL, NCG, ST e "Tipo de estrutura".

### Slide 14: endividamento (`11_divida_liquida_ebitda.png`)
- **Dívida líquida / EBITDA:** caiu de **3,60x (2019T4) para 0,35x (2026T2)**.
- **De onde veio a queda:** a dívida bruta ficou praticamente igual (US$ 14,8 bi em 2019T4 e 14,3 bi em 2026T2). Quem mudou foi o EBITDA, que multiplicou.
- **Patrimônio líquido:** foi de US$ 7,6 bi (2019T4) para 30,2 bi (2026T2), mesmo com as recompras.

### Slide 15: retorno (`12_roe_roa.png`) e liquidez (`13_liquidez_corrente.png`)
- **ROE (lucro de 12 meses / PL):** ~25% em 2019–20, mínimo de ~19% em 2023 e 45% em 2026T2 (este último inflado pela multa da WBD).
- **DuPont:** ROA × MAF, com a decomposição na aba `Indicadores`.
- **Liquidez corrente:** oscila entre 0,6x e 1,4x. Para a Netflix um valor abaixo de 1 não é sinal de aperto, porque a NCG negativa financia a operação.

---

## Bloco 5: conclusão (slide 16)
1. **A análise horizontal mostra três ciclos:** pandemia (2020), crise e ajuste (2022) e retomada com escala (2024 em diante).
2. **As variações bruscas têm explicação identificável e documentada.** Cada uma se encaixa em uma de três categorias:
   - **Conteúdo:** greves e retomada das produções.
   - **Câmbio:** dívida em euro e receita externa.
   - **Eventos únicos:** imposto no Brasil e multa da WBD.
3. **O que está em jogo agora:** a empresa saiu de queima de caixa e dívida de 3,6x o EBITDA para uma estrutura de caixa forte. O risco a acompanhar é a tentativa frustrada de compra da Warner Bros., com o empréstimo-ponte de US$ 59 bi já contratado em dez/2025, e o que a Netflix fará com o caixa.

---

## Perguntas que a banca pode fazer (e as respostas)

- **"Por que trimestral e não anual?"**
  - São 30 observações em vez de 7.
  - Os eventos ficam visíveis (2022T4, 2025T3, 2026T1).
  - A AH homóloga elimina a sazonalidade. A anual está em `AH_Anual`.
- **"O EBITDA está certo? Não somaram a amortização de conteúdo?"**
  - Não somamos, de propósito: conteúdo é custo operacional recorrente da Netflix.
  - Somar inflaria o EBITDA artificialmente. A nota está na aba `DRE`.
- **"De onde vieram os dados?"**
  - Dos 10-Q e 10-K oficiais na SEC, lidos no formato XBRL.
  - A aba `Fontes` lista os 30 relatórios com link.
  - A aba `Validacao` mostra que ativo = passivo + PL e que os totais da DRE fecham com os valores informados.
- **"O 4º trimestre aparece na SEC?"**
  - Não diretamente. Ele é 10-K (ano) − 9 meses do 10-Q.
  - A soma dos 4 trimestres confere com o 10-K em todos os anos.

---

## Checklist dos pontos da professora

| Ponto | Onde está atendido |
|---|---|
| Análise exploratória | Abas DRE/BP/DFC/AV/AH; slides 5–8 |
| Por que houve variações bruscas | Aba `Variacoes_Bruscas` (15 casos com fonte); bloco 3 |
| Variabilidade | 30 trimestres; AH sequencial, homóloga, base fixa e anual |
| Perguntas ruins | Bloco 3 (6 em destaque, 15 na planilha) |
| Macro e setor no início | Bloco 1 (slides 2–4); abas `Macro` e `Setor` |
| Todas as análises na planilha | `Analise_Netflix_ECO057.xlsx`: tudo em fórmulas, com gráficos nativos |
| Eixos dos gráficos | Um eixo Y por gráfico, com título e unidade; ano marcado no eixo X; vírgula decimal |
