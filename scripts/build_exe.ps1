param(
    [string]$Python = "py -3",
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& py -3 -m pip install -r requirements.txt

$distDir = Join-Path $ProjectRoot "dist"
$oneFileExe = Join-Path $distDir "EpubForge.exe"
$oneDirOutput = Join-Path $distDir "EpubForge"
Remove-Item -LiteralPath $oneFileExe -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $oneDirOutput -Recurse -Force -ErrorAction SilentlyContinue

$args = @(
    "--clean",
    "--name", "EpubForge",
    "--windowed",
    "--add-data", "app/assets/default.css;app/assets",
    "--add-data", "app/assets/app.ico;app/assets",
    "--add-data", "app/assets/app_icon.png;app/assets",
    "--exclude-module", "qfluentwidgets.common.image_utils",
    "--exclude-module", "numpy",
    "--exclude-module", "PIL",
    "--exclude-module", "colorthief",
    "app/main.py"
)

if ($OneFile) {
    $args = @("--onefile") + $args
}

$icon = Join-Path $ProjectRoot "app/assets/app.ico"
if (Test-Path $icon) {
    $args = @("--icon", $icon) + $args
}

& py -3 -m PyInstaller @args
