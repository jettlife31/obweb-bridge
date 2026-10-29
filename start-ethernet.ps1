param([string]$Adapter)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Open PowerShell as Administrator and run this launcher again.'
}
'OBWEB_RUN_MODE','OBWEB_USERNAME','OBWEB_REO_CODE' | ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.10 or newer with the Python launcher.' }
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $python -m pip install --quiet -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python login_web.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($Adapter) { & $python ethernet.py --adapter $Adapter }
else { & $python ethernet.py }
exit $LASTEXITCODE
