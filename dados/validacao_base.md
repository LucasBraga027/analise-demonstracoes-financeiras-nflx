# Validação da base trimestral (gerado por scripts/02_base_trimestral.py)

## 1. Identidades contábeis
- Ativo = Passivo + PL: OK (maior diferença 0.00 US$ mi)
- Passivo + PL informado = Ativo: OK (maior diferença 0.00 US$ mi)
- EBIT = Receita - Custos - Marketing - Tecnologia - G&A: OK (maior diferença 0.00 US$ mi)
- LAIR = EBIT - Juros + Outras receitas/despesas financeiras: OK (maior diferença 0.00 US$ mi)
- Lucro líquido = LAIR - IR: OK (maior diferença 0.00 US$ mi)
- AC = Caixa + Aplicações CP + Outros AC: OK (maior diferença 0.00 US$ mi)
- PC = Passivo conteúdo CP + Fornecedores + Provisões + Receita diferida + Dívida CP: OK (maior diferença 0.63 US$ mi)
- Receita DVD (total - 4 regiões de streaming) = DVD informado no 10-Q: OK (maior diferença 0.50 US$ mi)
- Receita DVD nunca negativa e zerada após 2023T3: OK

## 2. Conferência cruzada com a API companyfacts da SEC (fonte independente do XBRL bruto)
- receita (soma dos 4 trimestres = ano do 10-K): OK (maior diferença 0.00 US$ mi)
- lucro_liquido (soma dos 4 trimestres = ano do 10-K): OK (maior diferença 0.00 US$ mi)
- ativo_total (saldos trimestrais): OK (maior diferença 0.00 US$ mi)
- fco (soma dos 4 trimestres = ano do 10-K): OK (maior diferença 0.00 US$ mi)
- patrimonio_liquido (saldos trimestrais): OK (maior diferença 0.00 US$ mi)

## 3. Lacunas (valores não divulgados — mantidos vazios, sem preenchimento artificial)
- Nenhuma lacuna.
- Assinantes pagos por região: a Netflix deixou de divulgar a partir de 2025T1 (decisão anunciada na carta aos acionistas do 1º tri/2024). Último dado avulso: "325 milhões de assinantes pagos" citado na carta do 4º tri/2025.
