# Análise das Demonstrações Financeiras: Netflix, Inc. (NFLX)

Análise horizontal, vertical e por índices da **Netflix** de **2019T1 a 2026T2** (30 trimestres), para a disciplina **ECO057 — Elaboração e Análise de Projetos (UFJF)**. Todos os números vêm de **fontes oficiais**, foram **validados** e estão numa planilha Excel com fórmulas vivas.

## Entregáveis

| Arquivo | Conteúdo |
|---|---|
| [`Analise_Netflix_ECO057.xlsx`](Analise_Netflix_ECO057.xlsx) | **Todas as análises em fórmulas**, organizadas por aba (lista abaixo) |
| [`CONTEXTO_MACRO_SETORIAL.html`](CONTEXTO_MACRO_SETORIAL.html) | Nota técnica que explica a análise macro (juros, inflação, câmbio) e setorial (concorrentes de streaming), com cada número verificado e a fonte oficial |
| [`ROTEIRO_APRESENTACAO.md`](ROTEIRO_APRESENTACAO.md) | Storyline slide a slide (macro e setor primeiro), perguntas ruins, perguntas da banca e checklist dos pontos da professora |
| [`graficos_slides/`](graficos_slides/) | 13 gráficos 16:9 a 300 DPI, na ordem do roteiro |
| [`dados/`](dados/) | Bases em CSV (trimestral, regiões, macro, setor, eventos) e o relatório de validação |

Abas da planilha:
- `Macro` e `Setor`
- `DRE`, `BP` e `DFC`
- `AV`, `AH` e `AH_Anual`
- `Indicadores` (DuPont, Fleuriet, endividamento, GAO/GAF/GAT)
- `Regioes`
- `Variacoes_Bruscas`
- `Graficos`
- `Validacao` e `Fontes`

## Fontes de dados (somente oficiais)

| Fonte | Uso |
|---|---|
| **SEC EDGAR**: instâncias XBRL dos 10-Q e 10-K (2019–2026) | DRE, balanço, fluxo de caixa, contas de conteúdo, receita e assinantes por região |
| **SEC EDGAR**: cartas aos acionistas (Ex. 99.1 dos 8-K) e texto dos 10-Q/10-K | Explicação oficial de cada variação brusca, com o trecho citado |
| **SEC EDGAR**: 10-K de Disney, Warner Bros. Discovery, Paramount e Comcast | Comparação setorial e resultado dos negócios de streaming dos rivais |
| **Federal Reserve** (H.15), **U.S. Treasury**, **BLS**, **Banco Central Europeu** | Juros, Treasury de 10 anos, inflação, desemprego e câmbio |

## Metodologia

A metodologia é a mesma da planilha da disciplina (`Planilhas ECO057.xlsx`):
- **AV:** conta / base. A base é a receita na DRE e o ativo total no balanço.
- **AH:** (Atual − Anterior) / ABS(Anterior), em três versões: sequencial (t vs t−1), homóloga (t vs t−4) e base fixa (2019T4 = 100). A versão anual fica na aba `AH_Anual`.
- **DuPont:** ROA = Margem líquida × Giro; ROE = ROA × MAF. Usa lucro e receita dos últimos 12 meses.
- **Fleuriet:**
  - CCL = AC − PC; NCG = ACO − PCO; ST = CCL − NCG.
  - Classificação de tipo I a VI.
- **Alavancagem ("fórmula 1"):** GAO = Δ%EBIT/Δ%Receita, GAF = Δ%LL/Δ%EBIT e GAT = GAO × GAF.

## Validação

Todas as checagens são automáticas.
- **Na base:**
  - **Identidades contábeis:** ativo = passivo + PL, e EBIT, LAIR e LL montados batem com os valores informados à SEC em todos os trimestres.
  - **Cruzamento com a API `companyfacts` da SEC:** a soma dos 4 trimestres é igual ao 10-K do ano.
  - **Regiões:** receita das regiões + DVD = receita total.
  - O relatório completo está em [`dados/validacao_base.md`](dados/validacao_base.md).
- **Na planilha:** o Excel recalcula todas as fórmulas (zero erros). Depois, 12 indicadores são comparados com um cálculo independente em pandas (diferença < 10⁻⁶).

## Como reproduzir

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
.\rodar_tudo.ps1
```

O pipeline em [`scripts/`](scripts/) roda nesta ordem:
1. Baixa os relatórios e cartas da SEC (cache em `dados_sec/`, fora do Git).
2. Monta e valida a base trimestral.
3. Baixa os dados macro e setoriais.
4. Monta o catálogo de eventos.
5. Gera a planilha.
6. Recalcula a planilha no Excel e confere os valores.
7. Gera os gráficos.

A etapa 6 precisa do Microsoft Excel instalado.

## Correções em relação à versão anterior

A versão original está em [`versao_anterior/`](versao_anterior/). As mudanças:
- **Nenhum dado inventado.** Saíram o preenchimento automático de lacunas (`bfill`/`ffill`) e a reserva "custo = 52% da receita". Lacunas ficam vazias e são reportadas.
- **Sinal do imposto preservado.** Antes era usado `abs()`.
- **Fleuriet corrigido.** As aplicações financeiras foram separadas do capital de giro operacional.
- **Contas de conteúdo incluídas.** São elas que explicam as oscilações de caixa.
- **ROE e Dívida/EBITDA com 12 meses reais (LTM),** em vez de multiplicar o trimestre por 4.
- **Série estendida até 2019,** o que dá AH homóloga desde 2020T1. A tabela antiga mostrava Dívida/EBITDA em 2020T1, o que era impossível sem os 12 meses anteriores.
- **Explicação do 2026T1 corrigida:** o lucro acima do EBIT vem da multa rescisória de US$ 2,8 bi da WBD, e não de "créditos fiscais".
- **Gráficos refeitos:**
  - um eixo Y com título e unidade;
  - eixo X marcado por ano;
  - vírgula decimal;
  - tiques "redondos";
  - paleta validada para daltonismo.
- **Contexto macro e setorial adicionado.**

## Autoria

- **Versão original:** Eurico Júnior ([@Euricojr](https://github.com/Euricojr)).
- **Revisão, validação e extensão:** Lucas Braga.
