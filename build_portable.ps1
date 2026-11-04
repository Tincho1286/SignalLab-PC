param(
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')]
    [string]$Name = "",
    [switch]$KeepBuildFiles
)
$ErrorActionPreference = 'Stop'
$originalPath = $env:PATH
$originalOpenblas = $env:OPENBLAS_NUM_THREADS
$originalOmp = $env:OMP_NUM_THREADS
$originalBytecode = $env:PYTHONDONTWRITEBYTECODE
Push-Location $PSScriptRoot
try {
    $pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        throw 'Primero ejecutá setup_windows.ps1 para preparar el entorno del proyecto.'
    }
    if ([string]::IsNullOrWhiteSpace($Name)) {
        $Name = & $pythonExe -B -c 'from tools.windows_version import version_metadata; print(version_metadata()[1]["filename"][:-4])'
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Name)) { throw 'No se pudo obtener el nombre portable de la versión de origen.' }
        $Name = $Name.Trim()
        if ($Name -notmatch '^SignalLab-PC-[A-Za-z0-9._-]+$') { throw 'Nombre portable generado inválido.' }
    }
    $env:PATH = ((Split-Path $pythonExe), (Join-Path $env:SystemRoot 'System32'), $env:SystemRoot) -join ';'
    $env:OPENBLAS_NUM_THREADS = '1'
    $env:OMP_NUM_THREADS = '1'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & $pythonExe -B tools/check_static.py
    if ($LASTEXITCODE -ne 0) { throw 'Falló la detección de errores de código; no se construyó el portable.' }
    & $pythonExe -B tools/check_math.py
    if ($LASTEXITCODE -ne 0) { throw 'Falló el control matemático; no se construyó el portable.' }
    & $pythonExe -B tools/check_workflows.py
    if ($LASTEXITCODE -ne 0) { throw 'Falló la reutilización entre herramientas; no se construyó el portable.' }
    $workBase = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'work\pyinstaller'))
    $stagingOutput = Join-Path $PSScriptRoot 'work\portable-output'
    $versionFile = Join-Path $PSScriptRoot 'work\windows-version.txt'
    $versionMetadata = Join-Path $PSScriptRoot 'work\windows-version.json'
    & $pythonExe -B tools/windows_version.py --filename "$Name.exe" --output $versionFile --metadata-output $versionMetadata
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron generar los metadatos de producto y versión.' }
    & $pythonExe -B -m PyInstaller --noconfirm --clean --onefile --windowed --icon "$PSScriptRoot/signallab_pc/assets/signallab.ico" --name $Name --version-file $versionFile --distpath $stagingOutput --workpath $workBase --specpath work --add-data "$PSScriptRoot/signallab_pc/assets;signallab_pc/assets" --add-data "$PSScriptRoot/LICENSE;legal" --add-data "$PSScriptRoot/NOTICE.md;legal" --add-data "$PSScriptRoot/THIRD_PARTY_NOTICES.md;legal" --add-data "$PSScriptRoot/LICENSES;legal/LICENSES" main.py
    if ($LASTEXITCODE -ne 0) { throw 'Falló el empaquetado portable. Se conservaron los intermedios para diagnosticarlo.' }
    $outputDir = Join-Path $PSScriptRoot 'outputs'
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    $newExe = Join-Path $stagingOutput "$Name.exe"
    $finalExe = Join-Path $outputDir "$Name.exe"
    # Reemplazar la entrada del archivo evita modificar otras copias enlazadas.
    & $pythonExe -B -c 'import os,sys; os.replace(sys.argv[1],sys.argv[2])' $newExe $finalExe
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo guardar el ejecutable terminado; se conserva en work/portable-output.' }
    if (-not $KeepBuildFiles) {
        $buildFolder = [IO.Path]::GetFullPath((Join-Path $workBase $Name))
        $prefix = $workBase.TrimEnd('\') + '\'
        if (-not $buildFolder.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'La ruta de limpieza no está dentro de work/pyinstaller.'
        }
        if (Test-Path -LiteralPath $buildFolder) {
            $resolved = (Resolve-Path -LiteralPath $buildFolder).ProviderPath
            if (-not $resolved.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Ruta de limpieza inesperada.' }
            $links = Get-ChildItem -LiteralPath $buildFolder -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint } | Select-Object -First 1
            if (((Get-Item -LiteralPath $buildFolder).Attributes -band [IO.FileAttributes]::ReparsePoint) -or $links) { throw 'La carpeta generada contiene enlaces; no se limpió automáticamente.' }
            if (Test-Path -LiteralPath (Join-Path $buildFolder 'Analysis-00.toc')) {
                Remove-Item -LiteralPath $buildFolder -Recurse -Force
            }
        }
    }
    Write-Host "Generado outputs\$Name.exe."
}
finally {
    $env:PATH = $originalPath
    $env:OPENBLAS_NUM_THREADS = $originalOpenblas
    $env:OMP_NUM_THREADS = $originalOmp
    $env:PYTHONDONTWRITEBYTECODE = $originalBytecode
    Pop-Location
}
