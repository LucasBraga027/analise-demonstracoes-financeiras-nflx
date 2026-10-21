# Abre a planilha no Excel (oculto), recalcula todas as fórmulas, lista células com erro e salva com os valores em cache.
param([string]$Arquivo = (Join-Path (Split-Path $PSScriptRoot -Parent) 'Analise_Netflix_ECO057.xlsx'))
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false
try {
  $wb = $xl.Workbooks.Open($Arquivo)
  $xl.CalculateFull()
  $erros = 0
  foreach ($ws in $wb.Worksheets) {
    foreach ($c in $ws.UsedRange.Cells) {
      if ($c.HasFormula -and $c.Text -like '#*' -and $c.Text -notmatch '^#+$') {
        $erros++
        if ($erros -le 15) { Write-Output ("ERRO {0}!{1} {2} -> {3}" -f $ws.Name, $c.Address(0,0), $c.Formula, $c.Text) }
      }
    }
  }
  Write-Output "Células com erro de fórmula: $erros"
  $wb.Save(); $wb.Close($false)
} finally { $xl.Quit(); [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null }
