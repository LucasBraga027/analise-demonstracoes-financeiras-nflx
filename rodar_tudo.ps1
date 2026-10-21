# Executa todo o pipeline: coleta oficial -> base validada -> macro/setor -> eventos -> planilha -> gráficos.
# Pré-requisito: python -m venv venv; venv\Scripts\pip install -r requirements.txt  (e Microsoft Excel para a etapa 6)
$env:PYTHONIOENCODING = 'utf-8'
$py = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'
Push-Location $PSScriptRoot
try {
  $etapas = @('01_baixar_relatorios.py', '01b_baixar_cartas.py', '02_base_trimestral.py', '03_macro_setor.py',
              '04_eventos.py', '05_planilha_excel.py', 'recalcular_excel.ps1', '06_verificar_planilha.py', '07_graficos.py')
  foreach ($e in $etapas) {
    Write-Output "=== $e"
    # Avisos no stderr não interrompem; só o código de saída de cada etapa decide
    if ($e.EndsWith('.ps1')) { powershell -ExecutionPolicy Bypass -File "scripts\$e" } else { & $py "scripts\$e" }
    if ($LASTEXITCODE -ne 0) { throw "Etapa $e falhou (código $LASTEXITCODE)" }
  }
  Write-Output '=== Pipeline concluído sem erros.'
} finally { Pop-Location }
