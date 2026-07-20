param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PayloadDir = Join-Path $ProjectRoot "dist\pyinstaller\mtga-deck-downloader"
$OutputDir = Join-Path $ProjectRoot "dist\release"
$IconPath = Join-Path $ProjectRoot "build\icons\app.ico"

if (-not (Test-Path (Join-Path $PayloadDir "mtga-deck-downloader.exe"))) {
    throw "PyInstaller payload not found at $PayloadDir"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$env:APP_VERSION = $Version
$env:PAYLOAD_DIR = $PayloadDir
$env:OUTPUT_DIR = $OutputDir
$env:ICON_PATH = $IconPath

$IsccCommand = Get-Command "iscc.exe" -ErrorAction SilentlyContinue
$IsccPath = if ($IsccCommand) { $IsccCommand.Source } else { $null }
if (-not $IsccPath) {
    $DefaultIscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (Test-Path $DefaultIscc) {
        $IsccPath = $DefaultIscc
    }
}
if (-not $IsccPath) {
    throw "Inno Setup 6 was not found. Install it or add iscc.exe to PATH."
}

& $IsccPath (Join-Path $PSScriptRoot "installer.iss")
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE"
}

Write-Host "Installer ready in $OutputDir"
