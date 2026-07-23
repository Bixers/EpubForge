param(
    [string]$Python = "py -3"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& py -3 -m pip install -r requirements.txt

$args = @(
    "--clean",
    "--name", "EpubForge",
    "--windowed",
    "--onefile",
    "--add-data", "app/assets/default.css;app/assets",
    "--add-data", "app/assets/app.ico;app/assets",
    "--add-data", "app/assets/app_icon.png;app/assets",
    "app/main.py"
)

$icon = Join-Path $ProjectRoot "app/assets/app.ico"
if (Test-Path $icon) {
    $args = @("--icon", $icon) + $args
}

& py -3 -m PyInstaller @args
