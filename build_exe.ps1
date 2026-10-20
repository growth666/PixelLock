$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "找不到虚拟环境 Python：$python"
}

Push-Location $projectRoot
$previousOnefile = $env:PIXELLOCK_ONEFILE
try {
    $env:PIXELLOCK_ONEFILE = "0"
    & $python -m PyInstaller --clean --noconfirm PixelLock.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller 构建失败，退出码：$LASTEXITCODE"
    }
    $env:PIXELLOCK_ONEFILE = "1"
    & $python -m PyInstaller --clean --noconfirm --distpath dist\portable --workpath build\portable PixelLock.spec
    if ($LASTEXITCODE -ne 0) {
        throw "单文件版构建失败，退出码：$LASTEXITCODE"
    }
} finally {
    $env:PIXELLOCK_ONEFILE = $previousOnefile
    Pop-Location
}
