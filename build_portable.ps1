param(
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')]
    [string]$Name = "SignalLab-PC-1.1.0",
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
    $env:PATH = ((Split-Path $pythonExe), (Join-Path $env:SystemRoot 'System32'), $env:SystemRoot) -join ';'
    $env:OPENBLAS_NUM_THREADS = '1'
    $env:OMP_NUM_THREADS = '1'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $workBase = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'work\pyinstaller'))
    $stagingOutput = Join-Path $PSScriptRoot 'work\portable-output'
    & $pythonExe -B -m PyInstaller --noconfirm --clean --onefile --windowed --icon "$PSScriptRoot/signallab_pc/assets/signallab.ico" --name $Name --distpath $stagingOutput --workpath $workBase --specpath work --add-data "$PSScriptRoot/signallab_pc/assets;signallab_pc/assets" main.py
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
