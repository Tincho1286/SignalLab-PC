param([switch]$NoLaunch)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        $runtime = Join-Path $PSScriptRoot 'work\python-nuget\tools\python.exe'
        if (-not (Test-Path -LiteralPath $runtime)) {
            New-Item -ItemType Directory -Path work -Force | Out-Null
            $archive = Join-Path $PSScriptRoot 'work\python312.zip'
            Invoke-WebRequest 'https://www.nuget.org/api/v2/package/python/3.12.10' -OutFile $archive
            $expected = '0EB85C2DFCCCCF1B17352DE4C397F69194035B7D37149EACC16F1147D93DE3B8'
            if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expected) {
                throw 'El paquete Python descargado no coincide con el hash registrado.'
            }
            Expand-Archive -LiteralPath $archive -DestinationPath work\python-nuget -Force
        }
        & $runtime -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno privado.' }
    }
    & $pythonExe -m pip install -r requirements-lock.txt -r requirements-quality.txt
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
    if (-not $NoLaunch) { & $pythonExe main.py }
}
finally { Pop-Location }
