param([switch]$NoLaunch)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $pinnedPython = (Get-Content -LiteralPath (Join-Path $PSScriptRoot '.python-version') -Raw).Trim()
    $venvDirectory = Join-Path $PSScriptRoot '.venv'
    $pythonExe = Join-Path $venvDirectory 'Scripts\python.exe'
    $existingPython = if (Test-Path -LiteralPath $pythonExe) {
        & $pythonExe -B -c 'import platform; print(platform.python_version())'
    }
    $previousVenv = $null
    $replaceVenv = $existingPython -ne $pinnedPython
    if ($replaceVenv) {
        $runtimeFolder = Join-Path $PSScriptRoot "work\python-nuget-$pinnedPython"
        $runtime = Join-Path $runtimeFolder 'tools\python.exe'
        if (-not (Test-Path -LiteralPath $runtime)) {
            New-Item -ItemType Directory -Path work -Force | Out-Null
            $archive = Join-Path $PSScriptRoot "work\python-$pinnedPython.zip"
            $url = "https://api.nuget.org/v3-flatcontainer/python/$pinnedPython/python.$pinnedPython.nupkg"
            Invoke-WebRequest $url -OutFile $archive
            $expected = 'F54BA67C9951C3D773EA47D2BB095150C037C399F0423A968BCDA22809241784'
            if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expected) {
                throw 'El paquete Python descargado no coincide con el hash registrado.'
            }
            Expand-Archive -LiteralPath $archive -DestinationPath $runtimeFolder -Force
        }
        & $runtime -B tools/check_python_runtime.py
        if ($LASTEXITCODE -ne 0) { throw 'El CPython local no coincide con la versión del proyecto.' }
        if (Test-Path -LiteralPath $venvDirectory) {
            $previousVenv = Join-Path $PSScriptRoot ("work\venv-before-" + [guid]::NewGuid().ToString('N'))
            Move-Item -LiteralPath $venvDirectory -Destination $previousVenv
        }
    }
    try {
        if ($replaceVenv) {
            & $runtime -m venv $venvDirectory
            if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno privado.' }
        }
        & $pythonExe -m pip install -r requirements-lock.txt -r requirements-quality.txt
        if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
    }
    catch {
        if ($null -ne $previousVenv) {
            if (Test-Path -LiteralPath $venvDirectory) {
                $failedVenv = Join-Path $PSScriptRoot ("work\venv-failed-" + [guid]::NewGuid().ToString('N'))
                Move-Item -LiteralPath $venvDirectory -Destination $failedVenv
            }
            Move-Item -LiteralPath $previousVenv -Destination $venvDirectory
        }
        throw
    }
    if ($null -ne $previousVenv) { Write-Host "Entorno anterior guardado en $previousVenv" }
    if (-not $NoLaunch) { & $pythonExe main.py }
}
finally { Pop-Location }
