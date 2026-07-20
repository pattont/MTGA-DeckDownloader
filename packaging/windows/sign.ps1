param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$ErrorActionPreference = "Stop"
if (-not $env:WINDOWS_CERTIFICATE_BASE64) {
    Write-Host "WINDOWS_CERTIFICATE_BASE64 is not set; leaving $Path unsigned."
    exit 0
}
if (-not $env:WINDOWS_CERTIFICATE_PASSWORD) {
    throw "WINDOWS_CERTIFICATE_PASSWORD is required when a certificate is provided."
}

$ResolvedPath = (Resolve-Path $Path).Path
$SignTool = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe" |
    Sort-Object FullName |
    Select-Object -Last 1
if (-not $SignTool) {
    throw "signtool.exe was not found in the Windows SDK."
}

$CertificatePath = Join-Path $env:RUNNER_TEMP "mtga-deck-downloader-signing.pfx"
try {
    [IO.File]::WriteAllBytes(
        $CertificatePath,
        [Convert]::FromBase64String($env:WINDOWS_CERTIFICATE_BASE64)
    )
    $TimestampUrl = if ($env:WINDOWS_TIMESTAMP_URL) {
        $env:WINDOWS_TIMESTAMP_URL
    } else {
        "http://timestamp.digicert.com"
    }
    & $SignTool.FullName sign /fd SHA256 /td SHA256 /tr $TimestampUrl /f $CertificatePath /p $env:WINDOWS_CERTIFICATE_PASSWORD $ResolvedPath
    if ($LASTEXITCODE -ne 0) {
        throw "signtool failed with exit code $LASTEXITCODE"
    }
    & $SignTool.FullName verify /pa /v $ResolvedPath
    if ($LASTEXITCODE -ne 0) {
        throw "signature verification failed with exit code $LASTEXITCODE"
    }
} finally {
    Remove-Item -Force -ErrorAction SilentlyContinue $CertificatePath
}
