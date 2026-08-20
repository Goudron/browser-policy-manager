[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$MsiPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Stage([string]$Message) {
    Write-Host "[windows-smoke] $Message"
}

function Invoke-Msi([string[]]$Arguments) {
    $process = Start-Process -Wait -PassThru -FilePath msiexec.exe -ArgumentList $Arguments
    if ($process.ExitCode -ne 0) { throw "msiexec failed with exit code $($process.ExitCode)" }
}

function Wait-BpmReady {
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health/ready
            if ($response.Content -match '"ready":true') { return }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    throw 'BPM did not become ready within 30 seconds'
}

if (-not $IsWindows -or -not [Environment]::Is64BitOperatingSystem) {
    throw 'Windows x64 smoke must run on a native Windows x64 host.'
}
if (-not (Test-Path -LiteralPath $MsiPath)) { throw "MSI is absent: $MsiPath" }
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Windows MSI smoke requires an elevated administrator session.'
}

$InstallDirectory = Join-Path $env:ProgramFiles 'Browser Policy Manager'
$StateDirectory = Join-Path $env:ProgramData 'Browser Policy Manager'
$Migrator = Join-Path $InstallDirectory 'bpm-migrate.cmd'
try {
    Write-Stage 'clean install; service must remain stopped and migrations must remain explicit'
    Invoke-Msi @('/i', $MsiPath, '/qn', '/norestart', '/l*v', (Join-Path $env:TEMP 'bpm-msi-install.log'))
    if ((Get-Service -Name BPM).Status -ne 'Stopped') { throw 'MSI started BPM during installation' }
    if (-not (Test-Path -LiteralPath $Migrator)) { throw 'installed migration command is absent' }
    & $Migrator
    if ($LASTEXITCODE -ne 0) { throw 'explicit BPM migration failed' }
    Start-Service -Name BPM
    Wait-BpmReady
    if ((Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/).Content -notmatch '"version":"0.9.5.1"') {
        throw 'BPM root response does not expose version 0.9.5.1'
    }
    Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/help/ | Out-Null
    Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/profiles | Out-Null
    Stop-Service -Name BPM
    Start-Service -Name BPM
    Wait-BpmReady
    Stop-Service -Name BPM
    Write-Stage 'uninstall preserves operator state directory and database'
    Invoke-Msi @('/x', $MsiPath, '/qn', '/norestart', '/l*v', (Join-Path $env:TEMP 'bpm-msi-uninstall.log'))
    if (-not (Test-Path -LiteralPath (Join-Path $StateDirectory 'bpm.db'))) {
        throw 'ordinary MSI uninstall removed the operator-owned BPM database'
    }
    Write-Stage 'Windows MSI smoke: OK'
}
finally {
    if (Get-Service -Name BPM -ErrorAction SilentlyContinue) {
        Stop-Service -Name BPM -ErrorAction SilentlyContinue
        & msiexec.exe /x $MsiPath /qn /norestart | Out-Null
    }
}
