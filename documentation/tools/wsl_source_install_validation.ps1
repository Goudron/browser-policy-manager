[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Windows10", "Windows11")]
    [string]$WindowsTarget,
    [Parameter(Mandatory = $true)]
    [string]$Distro,
    [Parameter(Mandatory = $true)]
    [string]$BpmRef,
    [Parameter(Mandatory = $true)]
    [string]$CheckoutPath,
    [int]$Port = 8000,
    [string]$EvidenceRoot,
    [string]$BrowserExecutable,
    [switch]$PreflightOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-JsonFile {
    param($Value, [string]$Path, [int]$Depth = 12)
    $Value | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding utf8
}

function Add-Event {
    param(
        [string]$CheckId,
        [string]$Owner,
        [string]$Command,
        [int]$ExitCode,
        [string]$OutputFile
    )
    $record = [ordered]@{
        timestamp = (Get-Date).ToUniversalTime().ToString("o")
        check_id = $CheckId
        owner = $Owner
        command = $Command
        exit_code = $ExitCode
        output_file = $OutputFile
    }
    ($record | ConvertTo-Json -Compress) |
        Add-Content -LiteralPath $script:EventsPath -Encoding utf8
}

function Invoke-CapturedProcess {
    param(
        [string]$CheckId,
        [string]$Owner,
        [string]$FilePath,
        [string[]]$Arguments,
        [switch]$RequireSuccess,
        [string]$ExactOutputName
    )
    $script:CommandSequence += 1
    if ($ExactOutputName) {
        $outputName = $ExactOutputName
    } else {
        $safeCheck = $CheckId -replace "[^A-Za-z0-9._-]", "-"
        $outputName = ("command-{0:D3}-{1}.txt" -f $script:CommandSequence, $safeCheck)
    }
    $outputPath = Join-Path $script:EvidenceDirectory $outputName
    $displayCommand = (@($FilePath) + $Arguments) -join " "
    $outputLines = @()
    $exitCode = 0
    try {
        & $FilePath @Arguments 2>&1 | ForEach-Object {
            $outputLines += $_.ToString()
        }
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) {
            $exitCode = 0
        }
    } catch {
        $outputLines += $_.Exception.Message
        $exitCode = 1
    }
    $outputText = $outputLines -join [Environment]::NewLine
    $outputText | Set-Content -LiteralPath $outputPath -Encoding utf8
    Add-Event -CheckId $CheckId -Owner $Owner -Command $displayCommand -ExitCode $exitCode -OutputFile $outputName
    if ($RequireSuccess -and $exitCode -ne 0) {
        throw "$CheckId failed with exit code $exitCode. See $outputName."
    }
    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = $outputText
        OutputFile = $outputName
    }
}

function Invoke-Wsl {
    param(
        [string]$CheckId,
        [string]$Command,
        [switch]$RequireSuccess,
        [string]$ExactOutputName
    )
    return Invoke-CapturedProcess -CheckId $CheckId -Owner "wsl" -FilePath "wsl.exe" -Arguments @("-d", $Distro, "--", "bash", "-lc", $Command) -RequireSuccess:$RequireSuccess -ExactOutputName $ExactOutputName
}

function Convert-KeyValueOutput {
    param([string]$Text)
    $record = [ordered]@{}
    foreach ($line in ($Text -split "\r?\n")) {
        if ($line -match "^([^=]+)=(.*)$") {
            $record[$matches[1]] = $matches[2]
        }
    }
    return $record
}

function Resolve-EdgeExecutable {
    if ($BrowserExecutable) {
        if (-not (Test-Path -LiteralPath $BrowserExecutable -PathType Leaf)) {
            throw "The supplied BrowserExecutable does not exist."
        }
        return (Resolve-Path -LiteralPath $BrowserExecutable).Path
    }
    $candidates = @(
        (Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"),
        (Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"),
        (Join-Path $env:LocalAppData "Microsoft\Edge\Application\msedge.exe")
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw "Microsoft Edge was not found. Supply -BrowserExecutable with an actual Windows browser."
}

function Invoke-WindowsProbe {
    param(
        [string]$CheckId,
        [string]$Url,
        [switch]$ExpectFailure
    )
    $script:CommandSequence += 1
    $outputName = ("command-{0:D3}-{1}.txt" -f $script:CommandSequence, $CheckId)
    $outputPath = Join-Path $script:EvidenceDirectory $outputName
    $exitCode = 0
    $statusCode = $null
    $body = ""
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 4
        $statusCode = [int]$response.StatusCode
        $body = [string]$response.Content
    } catch {
        $exitCode = 1
        $body = $_.Exception.Message
    }
    [ordered]@{
        url = $Url
        status_code = $statusCode
        output = $body
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $outputPath -Encoding utf8
    Add-Event -CheckId $CheckId -Owner "windows-host" -Command "Invoke-WebRequest $Url" -ExitCode $exitCode -OutputFile $outputName
    if ($ExpectFailure) {
        if ($exitCode -eq 0) {
            throw "$CheckId unexpectedly reached BPM after shutdown."
        }
    } elseif ($exitCode -ne 0 -or $statusCode -ne 200) {
        throw "$CheckId did not return HTTP 200."
    }
    $script:ProbeRecords += [ordered]@{
        check_id = $CheckId
        owner = "windows-host"
        url = $Url
        expected = $(if ($ExpectFailure) { "connection-refused" } else { "HTTP-200" })
        exit_code = $exitCode
        status_code = $statusCode
        output_file = $outputName
    }
}

function Wait-WindowsReady {
    param([int]$Cycle)
    $url = "http://localhost:$Port/health/ready"
    for ($attempt = 1; $attempt -le 120; $attempt += 1) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ([int]$response.StatusCode -eq 200 -and [string]$response.Content -match '"ready"\s*:\s*true') {
                Add-Event -CheckId "cycle-$Cycle-windows-ready-wait" -Owner "windows-host" -Command "Invoke-WebRequest $url (attempt $attempt)" -ExitCode 0 -OutputFile "probes.json"
                return
            }
        } catch {
            # Readiness retries are represented by the final event.
        }
        Start-Sleep -Seconds 1
    }
    Add-Event -CheckId "cycle-$Cycle-windows-ready-wait" -Owner "windows-host" -Command "Invoke-WebRequest $url (120 attempts)" -ExitCode 1 -OutputFile "probes.json"
    throw "BPM did not become reachable from Windows localhost in cycle $Cycle."
}

function Expand-ShellTemplate {
    param([string]$Template, [int]$Cycle = 0)
    return $Template.Replace("__CHECKOUT__", $CheckoutPath).Replace("__PORT__", [string]$Port).Replace("__RUN_ID__", $RunId).Replace("__CYCLE__", [string]$Cycle).Replace("__BPM_REF__", $BpmRef)
}

function Start-BpmRuntime {
    param([int]$Cycle)
    $template = @'
set -euo pipefail
cd -- '__CHECKOUT__'
source .venv/bin/activate
runtime_root='/tmp/__RUN_ID__-cycle-__CYCLE__'
mkdir -p "$runtime_root"
export BPM_DATABASE_URL='sqlite+aiosqlite:///./data/bpm.db'
export BPM_HOST='0.0.0.0'
export BPM_PORT='__PORT__'
export BPM_RELOAD='true'
nohup setsid bash -lc 'exec make dev' >"$runtime_root/runtime.log" 2>&1 </dev/null &
printf '%s\n' "$!" >"$runtime_root/runtime.pid"
cat "$runtime_root/runtime.pid"
'@
    $command = Expand-ShellTemplate -Template $template -Cycle $Cycle
    $result = Invoke-Wsl -CheckId "cycle-$Cycle-runtime-start" -Command $command -RequireSuccess
    if ($result.Output.Trim() -notmatch "^\d+$") {
        throw "Cycle $Cycle did not return a numeric runtime PID."
    }
    $script:RuntimeRoots[$Cycle] = "/tmp/$RunId-cycle-$Cycle"
}

function Save-RuntimeLog {
    param([int]$Cycle)
    if (-not $script:RuntimeRoots.ContainsKey($Cycle)) {
        return
    }
    $runtimeRoot = $script:RuntimeRoots[$Cycle]
    Invoke-Wsl -CheckId "cycle-$Cycle-runtime-log" -Command "cat '$runtimeRoot/runtime.log'" -ExactOutputName "runtime-cycle-$Cycle.log" | Out-Null
}

function Stop-BpmRuntime {
    param(
        [int]$Cycle,
        [switch]$BestEffort
    )
    if (-not $script:RuntimeRoots.ContainsKey($Cycle)) {
        return
    }
    $template = @'
set -euo pipefail
runtime_root='/tmp/__RUN_ID__-cycle-__CYCLE__'
test -s "$runtime_root/runtime.pid"
pid=$(cat "$runtime_root/runtime.pid")
if kill -0 "$pid" 2>/dev/null; then
    pgid=$(ps -o pgid= -p "$pid" | tr -d ' ')
    test -n "$pgid"
    kill -TERM -- "-$pgid"
    for attempt in $(seq 1 30); do
        if ! kill -0 "$pid" 2>/dev/null; then exit 0; fi
        sleep 1
    done
    exit 1
fi
'@
    $command = Expand-ShellTemplate -Template $template -Cycle $Cycle
    $result = Invoke-Wsl -CheckId "cycle-$Cycle-runtime-stop" -Command $command
    if (-not $BestEffort -and $result.ExitCode -ne 0) {
        throw "Cycle $Cycle runtime did not stop cleanly."
    }
}

function Assert-WslProbe {
    param(
        [int]$Cycle,
        [string]$Path,
        [string]$ExpectedPattern
    )
    $url = "http://127.0.0.1:$Port$Path"
    $safeName = $Path.Trim("/").Replace("/", "-")
    if (-not $safeName) {
        $safeName = "root"
    }
    $result = Invoke-Wsl -CheckId "cycle-$Cycle-wsl-$safeName" -Command "curl -fsS --max-time 5 '$url'" -RequireSuccess
    if ($result.Output -notmatch $ExpectedPattern) {
        throw "Cycle $Cycle WSL probe $Path returned an unexpected body."
    }
    $script:ProbeRecords += [ordered]@{
        check_id = "cycle-$Cycle-wsl-$safeName"
        owner = "wsl"
        url = $url
        expected = $ExpectedPattern
        exit_code = $result.ExitCode
        output_file = $result.OutputFile
    }
}

function Assert-BrowserAccess {
    param([int]$Cycle)
    $url = "http://localhost:$Port/profiles"
    $arguments = @("--headless=new", "--disable-gpu", "--no-first-run", "--dump-dom", $url)
    $result = Invoke-CapturedProcess -CheckId "cycle-$Cycle-browser-access" -Owner "windows-host" -FilePath $script:EdgeExecutable -Arguments $arguments -RequireSuccess -ExactOutputName "browser-cycle-$Cycle.html"
    if ($result.Output -notmatch "(?i)<html") {
        throw "Windows Edge did not return an HTML document in cycle $Cycle."
    }
}

function Invoke-RuntimeCycle {
    param([int]$Cycle)
    Start-BpmRuntime -Cycle $Cycle
    try {
        Wait-WindowsReady -Cycle $Cycle
        Assert-WslProbe -Cycle $Cycle -Path "/health" -ExpectedPattern '"status"\s*:\s*"ok"'
        Assert-WslProbe -Cycle $Cycle -Path "/health/ready" -ExpectedPattern '"ready"\s*:\s*true'
        Assert-WslProbe -Cycle $Cycle -Path "/profiles" -ExpectedPattern "(?s).+"
        Invoke-WindowsProbe -CheckId "cycle-$Cycle-windows-health" -Url "http://localhost:$Port/health"
        Invoke-WindowsProbe -CheckId "cycle-$Cycle-windows-ready" -Url "http://localhost:$Port/health/ready"
        Invoke-WindowsProbe -CheckId "cycle-$Cycle-windows-profiles" -Url "http://localhost:$Port/profiles"
        Assert-BrowserAccess -Cycle $Cycle
    } finally {
        Save-RuntimeLog -Cycle $Cycle
        Stop-BpmRuntime -Cycle $Cycle
    }
    $wslStopped = Invoke-Wsl -CheckId "cycle-$Cycle-wsl-post-stop" -Command "curl -fsS --max-time 2 'http://127.0.0.1:$Port/health'"
    if ($wslStopped.ExitCode -eq 0) {
        throw "Cycle $Cycle WSL health probe still succeeded after stop."
    }
    Invoke-WindowsProbe -CheckId "cycle-$Cycle-windows-post-stop" -Url "http://localhost:$Port/health" -ExpectFailure
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw "This runner requires an actual Windows 10 or Windows 11 host. Linux and Docker are not valid substitutes."
}
if ($Distro -notmatch "^[A-Za-z0-9._-]+$") {
    throw "Distro contains unsupported characters."
}
if ($BpmRef -notmatch "^[0-9a-f]{40}$") {
    throw "BpmRef must be an exact 40-character lowercase Git commit."
}
if ($CheckoutPath -notmatch "^/home/[A-Za-z0-9._/-]+$" -or $CheckoutPath -match "^/(mnt|media)/" -or $CheckoutPath -match "^/run/desktop/mnt/host/") {
    throw "CheckoutPath must be an absolute path under the WSL Linux /home filesystem."
}
if ($Port -lt 1024 -or $Port -gt 65535) {
    throw "Port must be between 1024 and 65535."
}
if (-not $env:LOCALAPPDATA -and -not $EvidenceRoot) {
    throw "LOCALAPPDATA is unavailable; supply EvidenceRoot explicitly."
}

$ownerTask = $(if ($WindowsTarget -eq "Windows10") { "BPM091-M11-11" } else { "BPM091-M11-12" })
$taskNumber = $(if ($WindowsTarget -eq "Windows10") { "11" } else { "12" })
$windowsNumber = $(if ($WindowsTarget -eq "Windows10") { "10" } else { "11" })
$RunId = "bpm091-m11-$taskNumber-windows$windowsNumber-wsl-" + (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
if (-not $EvidenceRoot) {
    $EvidenceRoot = Join-Path $env:LOCALAPPDATA "BPM\wsl-source-install-validation\0.9.1"
}
$script:EvidenceDirectory = Join-Path $EvidenceRoot $RunId
New-Item -ItemType Directory -Path $script:EvidenceDirectory -Force | Out-Null
$script:EventsPath = Join-Path $script:EvidenceDirectory "events.jsonl"
New-Item -ItemType File -Path $script:EventsPath -Force | Out-Null
$script:CommandSequence = 0
$script:ProbeRecords = @()
$script:RuntimeRoots = @{}
$script:EdgeExecutable = $null
$status = "blocked"
$failure = $null
$startedAt = (Get-Date).ToUniversalTime().ToString("o")
$hostRecord = $null
$wslRecord = $null

try {
    $os = Get-CimInstance Win32_OperatingSystem
    $hostRecord = [ordered]@{
        requested_target = $WindowsTarget
        Caption = [string]$os.Caption
        Version = [string]$os.Version
        BuildNumber = [string]$os.BuildNumber
        OSArchitecture = [string]$os.OSArchitecture
        PowerShellVersion = [string]$PSVersionTable.PSVersion
    }
    Write-JsonFile -Value $hostRecord -Path (Join-Path $script:EvidenceDirectory "host.json")
    $expectedCaption = $(if ($WindowsTarget -eq "Windows10") { "Windows 10" } else { "Windows 11" })
    if ($hostRecord.Caption -notmatch [regex]::Escape($expectedCaption)) {
        throw "Observed Windows caption does not match requested target $WindowsTarget."
    }

    $wslVersion = Invoke-CapturedProcess -CheckId "wsl-version" -Owner "windows-host" -FilePath "wsl.exe" -Arguments @("--version") -RequireSuccess
    if (-not $wslVersion.Output.Trim()) {
        throw "wsl.exe --version returned no version evidence."
    }
    $wslStatus = Invoke-CapturedProcess -CheckId "wsl-status" -Owner "windows-host" -FilePath "wsl.exe" -Arguments @("--status") -RequireSuccess
    $wslList = Invoke-CapturedProcess -CheckId "wsl-list" -Owner "windows-host" -FilePath "wsl.exe" -Arguments @("--list", "--verbose") -RequireSuccess
    $distroLines = @($wslList.Output -split "\r?\n" | Where-Object { $_ -match [regex]::Escape($Distro) })
    if ($distroLines.Count -ne 1 -or $distroLines[0] -notmatch "\s+2\s*$") {
        throw "The requested distribution must exist exactly once and report WSL generation 2."
    }

    $identityTemplate = @'
set -e
. /etc/os-release
printf 'ID=%s\nVERSION_ID=%s\n' "$ID" "$VERSION_ID"
printf 'UNAME=%s\n' "$(uname -a)"
printf 'PROC_VERSION=%s\n' "$(cat /proc/version)"
'@
    $identity = Invoke-Wsl -CheckId "distribution-identity" -Command $identityTemplate -RequireSuccess
    $identityRecord = Convert-KeyValueOutput -Text $identity.Output
    if ($identityRecord["ID"] -ne "ubuntu" -or $identityRecord["VERSION_ID"] -ne "26.04") {
        throw "The WSL distribution is not Ubuntu 26.04."
    }

    $systemdTemplate = @'
set +e
printf 'PID1=%s\n' "$(ps -p 1 -o comm= | tr -d ' ')"
printf 'SYSTEMD_STATE=%s\n' "$(systemctl is-system-running 2>/dev/null || printf 'not-enabled')"
printf '%s\n' 'WSL_CONF_BEGIN'
cat /etc/wsl.conf 2>/dev/null || true
printf '%s\n' 'WSL_CONF_END'
exit 0
'@
    $systemd = Invoke-Wsl -CheckId "systemd-mode" -Command $systemdTemplate -RequireSuccess

    $filesystemTemplate = @'
set -e
cd -- '__CHECKOUT__'
physical=$(pwd -P)
case "$physical" in /home/*) ;; *) exit 41 ;; esac
case "$physical" in /mnt/*|/media/*|/run/desktop/mnt/host/*) exit 42 ;; esac
printf 'PHYSICAL_PATH=%s\n' "$physical"
printf 'WINDOWS_PATH=%s\n' "$(wslpath -w "$physical")"
printf 'FILESYSTEM_TYPE=%s\n' "$(stat -f -c %T "$physical")"
'@
    $filesystemCommand = Expand-ShellTemplate -Template $filesystemTemplate
    $filesystem = Invoke-Wsl -CheckId "filesystem-location" -Command $filesystemCommand -RequireSuccess

    $preflightTemplate = @'
set -euo pipefail
cd -- '__CHECKOUT__'
test "$(git rev-parse HEAD)" = '__BPM_REF__'
test -z "$(git status --short)"
test -x .venv/bin/python
source .venv/bin/activate
python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)'
printf 'GIT_REF=%s\n' "$(git rev-parse HEAD)"
printf 'PYTHON=%s\n' "$(python --version 2>&1)"
'@
    $preflightCommand = Expand-ShellTemplate -Template $preflightTemplate
    $sourcePreflight = Invoke-Wsl -CheckId "installed-source-preflight" -Command $preflightCommand -RequireSuccess -ExactOutputName "source-preflight.txt"

    $script:EdgeExecutable = Resolve-EdgeExecutable
    $wslRecord = [ordered]@{
        distro = $Distro
        generation = 2
        version_output_file = $wslVersion.OutputFile
        status_output_file = $wslStatus.OutputFile
        list_output_file = $wslList.OutputFile
        identity = $identityRecord
        identity_output_file = $identity.OutputFile
        systemd_output_file = $systemd.OutputFile
        filesystem = Convert-KeyValueOutput -Text $filesystem.Output
        filesystem_output_file = $filesystem.OutputFile
        source_preflight_output_file = $sourcePreflight.OutputFile
        browser_executable = $script:EdgeExecutable
    }
    Write-JsonFile -Value $wslRecord -Path (Join-Path $script:EvidenceDirectory "wsl.json")

    if (-not $PreflightOnly) {
        $assertionTemplate = @'
set -euo pipefail
cd -- '__CHECKOUT__'
source .venv/bin/activate
export BPM_DATABASE_URL='sqlite+aiosqlite:///./data/bpm.db'
alembic upgrade head
alembic current
make docs-validate
make docs-build
make docs-install-dev
test -f app/documentation/site/manifest.json
'@
        $assertionCommand = Expand-ShellTemplate -Template $assertionTemplate
        Invoke-Wsl -CheckId "installed-source-assertions" -Command $assertionCommand -RequireSuccess -ExactOutputName "source-assertions.txt" | Out-Null

        Invoke-RuntimeCycle -Cycle 1

        Invoke-CapturedProcess -CheckId "wsl-terminate" -Owner "windows-host" -FilePath "wsl.exe" -Arguments @("--terminate", $Distro) -RequireSuccess | Out-Null
        Start-Sleep -Seconds 2
        $restartIdentity = Invoke-Wsl -CheckId "wsl-restart-identity" -Command '. /etc/os-release; test "$ID" = ubuntu; test "$VERSION_ID" = 26.04' -RequireSuccess
        $oldRuntimeTemplate = @'
set -e
pid=$(cat '/tmp/__RUN_ID__-cycle-1/runtime.pid')
if kill -0 "$pid" 2>/dev/null; then
    ! ps -o args= -p "$pid" | grep -Eq 'make dev|uvicorn app.main:app'
fi
'@
        $oldRuntimeCommand = Expand-ShellTemplate -Template $oldRuntimeTemplate
        $oldRuntimeAbsent = Invoke-Wsl -CheckId "wsl-restart-old-runtime-absent" -Command $oldRuntimeCommand -RequireSuccess
        if ($restartIdentity.ExitCode -ne 0 -or $oldRuntimeAbsent.ExitCode -ne 0) {
            throw "WSL restart checks did not pass."
        }

        Invoke-RuntimeCycle -Cycle 2
    }

    $status = "pass"
} catch {
    $failure = $_.Exception.Message
} finally {
    foreach ($cycle in @(1, 2)) {
        if ($script:RuntimeRoots.ContainsKey($cycle)) {
            try {
                Stop-BpmRuntime -Cycle $cycle -BestEffort
                Save-RuntimeLog -Cycle $cycle
            } catch {
                if (-not $failure) {
                    $failure = "Cleanup failed: $($_.Exception.Message)"
                }
                $status = "blocked"
            }
        }
    }
    Write-JsonFile -Value $script:ProbeRecords -Path (Join-Path $script:EvidenceDirectory "probes.json")
    $summary = [ordered]@{
        schema_version = 1
        backlog_item = $ownerTask
        target_bpm_version = "0.9.1"
        run_id = $RunId
        started_at = $startedAt
        completed_at = (Get-Date).ToUniversalTime().ToString("o")
        windows_target = $WindowsTarget
        distro = $Distro
        bpm_ref = $BpmRef
        checkout_path = $CheckoutPath
        mode = $(if ($PreflightOnly) { "preflight-only" } else { "full-validation" })
        status = $status
        disposition = $(if ($PreflightOnly -and $status -eq "pass") {
            "preflight-pass-not-windows-validation"
        } elseif ($status -eq "pass") {
            "accepted-actual-windows-wsl-validation-candidate"
        } else {
            "blocked"
        })
        failure = $failure
        actual_windows_host = $true
        docker_or_container_evidence = $false
        evidence_directory = $script:EvidenceDirectory
    }
    Write-JsonFile -Value $summary -Path (Join-Path $script:EvidenceDirectory "summary.json")
    $hashes = @()
    Get-ChildItem -LiteralPath $script:EvidenceDirectory -File |
        Where-Object { $_.Name -ne "sha256.json" } |
        Sort-Object Name |
        ForEach-Object {
            $hashes += [ordered]@{
                path = $_.Name
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        }
    Write-JsonFile -Value $hashes -Path (Join-Path $script:EvidenceDirectory "sha256.json")
}

if ($status -ne "pass") {
    throw "WSL validation blocked: $failure. Evidence: $script:EvidenceDirectory"
}
Write-Output "WSL validation $status. Evidence: $script:EvidenceDirectory"
