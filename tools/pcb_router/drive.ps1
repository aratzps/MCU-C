# Routing convergence driver: refill -> DRC -> route, until 0 unconnected
# or two consecutive stalls. All board saves are atomic; a rolling backup
# is kept and restored if a router crash damages the file.
$ROOT = if ($env:MCUC_ROOT) { $env:MCUC_ROOT } else { Resolve-Path "$PSScriptRoot\..\.." }
$SP = if ($env:MCUC_ROUTER_WORK) { $env:MCUC_ROUTER_WORK } else { "$env:TEMP\mcuc_router" }
New-Item -ItemType Directory -Force $SP | Out-Null
$PY = 'C:\Program Files\KiCad\9.0\bin\python.exe'
$K = 'C:\Program Files\KiCad\9.0\bin\kicad-cli.exe'
$PCB = "$ROOT\mcuc_inverter\mcuc_inverter.kicad_pcb"

$prev = 999999
$stall = 0
for ($i = 1; $i -le 14; $i++) {
  Write-Output "=== iteration $i : refill + DRC ==="
  Copy-Item $PCB "$SP\board_backup.kicad_pcb" -Force
  & $PY "$PSScriptRoot\refill.py" $PCB
  if ($LASTEXITCODE -ne 0) { Write-Output "=== FATAL: refill failed (exit $LASTEXITCODE), aborting ==="; break }
  if (Test-Path "$SP\drc_cur.json") { Remove-Item "$SP\drc_cur.json" }
  & $K pcb drc --severity-error --format json --output "$SP\drc_cur.json" $PCB | Out-Null
  if (-not (Test-Path "$SP\drc_cur.json")) { Write-Output "=== FATAL: DRC produced no report, aborting ==="; break }
  Copy-Item "$SP\drc_cur.json" "$SP\drc_iter$i.json" -Force
  $j = Get-Content "$SP\drc_cur.json" -Raw | ConvertFrom-Json
  $u = $j.unconnected_items.Count
  $v = $j.violations.Count
  Write-Output "=== iteration $i : violations=$v unconnected=$u (prev $prev) ==="
  if ($u -eq 0) { Write-Output "=== CONVERGED: 0 unconnected ==="; break }
  if ($u -ge $prev -and $i -gt 1) { $stall++ } else { $stall = 0 }
  if ($stall -ge 2) { Write-Output "=== NO PROGRESS (2 stalls), stopping ==="; break }
  $prev = $u
  & $PY "$PSScriptRoot\router.py" "$SP\drc_cur.json" 2>&1 | Out-File "$SP\route_iter$i.log" -Encoding utf8
  Write-Output "=== router exit: $LASTEXITCODE ==="
  if (-not (Test-Path $PCB) -or (Get-Item $PCB).Length -lt 1MB) {
    Write-Output "=== board file damaged, restoring backup ==="
    Copy-Item "$SP\board_backup.kicad_pcb" $PCB -Force
  }
  Get-Content "$SP\route_iter$i.log" | Select-String -Pattern '^routed ' | ForEach-Object { $_.Line }
}
Write-Output "=== driver done ==="
