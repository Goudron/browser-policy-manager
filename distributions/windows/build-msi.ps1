[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SourceRoot,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][string]$SourceRevision
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Target = Get-Content (Join-Path $SourceRoot 'distributions/windows/targets.json') -Raw |
    ConvertFrom-Json
$Version = $Target.target_bpm_version
$Artifact = $Target.installer.artifact
$WorkRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("bpm-msi-" + [guid]::NewGuid())
$Payload = Join-Path $WorkRoot 'payload'
$State = Join-Path $WorkRoot 'state'
$Wheelhouse = Join-Path $WorkRoot 'wheelhouse'
$Runtime = Join-Path $Payload 'runtime'
$Venv = Join-Path $Payload 'venv'
$OutputArtifact = Join-Path $OutputDirectory $Artifact

function Write-Stage([string]$Message) {
    Write-Host "[windows-distribution] $Message"
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-VerifiedDownload([string]$Url, [string]$ExpectedSha256, [string]$Destination) {
    Write-Stage "download $Url"
    Invoke-WebRequest -Uri $Url -OutFile $Destination
    $actual = Get-Sha256 $Destination
    if ($actual -ne $ExpectedSha256) {
        throw "checksum mismatch for ${Url}: expected $ExpectedSha256, got $actual"
    }
}

if (-not $IsWindows) {
    throw 'Windows MSI assembly must run on a native Windows x64 host.'
}
if (-not [Environment]::Is64BitOperatingSystem) {
    throw 'BPM 0.9.5 Windows MSI supports x64 hosts only.'
}
if (-not (Get-Command wix -ErrorAction SilentlyContinue)) {
    throw 'WiX Toolset is missing; install the pinned wix dotnet tool before building.'
}

New-Item -ItemType Directory -Force -Path $OutputDirectory, $WorkRoot, $Payload, $State, $Wheelhouse |
    Out-Null

try {
    $pythonInstaller = Join-Path $WorkRoot 'python-installer.exe'
    Get-VerifiedDownload $Target.runtime.installer_url $Target.runtime.installer_sha256 $pythonInstaller
    Write-Stage "install private CPython $($Target.runtime.python_version) into staging"
    $pythonArguments = @(
        '/quiet', 'InstallAllUsers=0', 'PrependPath=0', 'Include_test=0', 'Include_doc=0',
        'Include_launcher=0', "TargetDir=$Runtime"
    )
    $pythonProcess = Start-Process -Wait -PassThru -FilePath $pythonInstaller -ArgumentList $pythonArguments
    if ($pythonProcess.ExitCode -ne 0) {
        throw "private CPython installer failed with exit code $($pythonProcess.ExitCode)"
    }
    $RuntimePython = Join-Path $Runtime 'python.exe'
    if (-not (Test-Path -LiteralPath $RuntimePython)) {
        throw 'private CPython staging did not produce python.exe'
    }

    Write-Stage 'resolve locked Windows base runtime without optional BPM extras'
    & $RuntimePython -m ensurepip --upgrade
    & $RuntimePython -m pip install --disable-pip-version-check --upgrade `
        'pip==25.3' 'setuptools==84.0.0' 'wheel==0.47.0'
    if ($LASTEXITCODE -ne 0) { throw 'failed to install private Python build tooling' }
    & $RuntimePython -m pip wheel --disable-pip-version-check --only-binary=:all: `
        --wheel-dir $Wheelhouse --requirement (Join-Path $SourceRoot 'distributions/windows/requirements.windows.lock')
    if ($LASTEXITCODE -ne 0) { throw 'failed to resolve Windows base-runtime wheels' }

    $BuildSource = Join-Path $WorkRoot 'bpm-source'
    New-Item -ItemType Directory -Force -Path $BuildSource | Out-Null
    Copy-Item (Join-Path $SourceRoot 'pyproject.toml'), (Join-Path $SourceRoot 'README.md'),
        (Join-Path $SourceRoot 'LICENSE') -Destination $BuildSource
    Copy-Item (Join-Path $SourceRoot 'app') -Destination $BuildSource -Recurse
    & $RuntimePython -m pip wheel --disable-pip-version-check --no-deps --no-build-isolation `
        --wheel-dir $Wheelhouse $BuildSource
    if ($LASTEXITCODE -ne 0) { throw 'failed to build BPM wheel' }
    & $RuntimePython -m venv --copies $Venv
    if ($LASTEXITCODE -ne 0) { throw 'failed to create private BPM virtual environment' }
    $VenvPython = Join-Path $Venv 'Scripts/python.exe'
    & $VenvPython -m pip install --disable-pip-version-check --no-index --find-links $Wheelhouse `
        --requirement (Join-Path $SourceRoot 'distributions/windows/requirements.windows.lock')
    if ($LASTEXITCODE -ne 0) { throw 'failed to install locked Windows base runtime' }
    $BpmWheel = Get-ChildItem -LiteralPath $Wheelhouse -Filter "browser_policy_manager-$Version-*.whl" |
        Select-Object -First 1
    if ($null -eq $BpmWheel) { throw 'BPM wheel is absent from the private wheelhouse' }
    & $VenvPython -m pip install --disable-pip-version-check --no-index --find-links $Wheelhouse `
        --no-deps $BpmWheel.FullName
    if ($LASTEXITCODE -ne 0) { throw 'failed to install BPM into the private virtual environment' }
    & $VenvPython -I -c "import importlib.metadata, importlib.util, app.main; assert importlib.metadata.version('browser-policy-manager') == '$Version'; assert all(importlib.util.find_spec(name) is None for name in ('numpy', 'onnxruntime', 'tokenizers'))"
    if ($LASTEXITCODE -ne 0) { throw 'private BPM payload verification failed' }

    Write-Stage 'install verified documentation, migration, and native Windows service payload'
    $Documentation = Join-Path $SourceRoot "documentation/dist/bpm-documentation-$Version.tar.gz"
    $DocumentationChecksum = "$Documentation.sha256"
    if (-not (Test-Path -LiteralPath $Documentation) -or -not (Test-Path -LiteralPath $DocumentationChecksum)) {
        throw 'verified product documentation package is required before Windows packaging'
    }
    $ExpectedDocumentation = (Get-Content -LiteralPath $DocumentationChecksum -Raw).Trim().Split(' ')[0]
    $DocumentationSha256 = Get-Sha256 $Documentation
    if ($DocumentationSha256 -ne $ExpectedDocumentation) {
        throw 'documentation archive checksum does not match its recorded checksum'
    }
    $DocumentationSite = Join-Path $Payload 'documentation/site'
    New-Item -ItemType Directory -Force -Path $DocumentationSite | Out-Null
    & tar.exe -xzf $Documentation -C $DocumentationSite --strip-components=1
    if ($LASTEXITCODE -ne 0) { throw 'failed to extract verified documentation archive' }
    Copy-Item (Join-Path $SourceRoot 'alembic') -Destination (Join-Path $Payload 'alembic') -Recurse
    Copy-Item (Join-Path $SourceRoot 'alembic.ini'), (Join-Path $SourceRoot 'LICENSE') -Destination $Payload
    Copy-Item (Join-Path $SourceRoot 'distributions/docker/requirements.lock') -Destination $Payload
    Copy-Item (Join-Path $SourceRoot 'distributions/windows/requirements.windows.lock') -Destination $Payload
    Copy-Item (Join-Path $SourceRoot 'documentation/config/THIRD_PARTY_NOTICES.md') `
        -Destination (Join-Path $Payload 'BPM-THIRD_PARTY_NOTICES.md')
    Copy-Item (Join-Path $SourceRoot 'distributions/windows/THIRD_PARTY_NOTICES.md') `
        -Destination (Join-Path $Payload 'WINDOWS-THIRD_PARTY_NOTICES.md')
    Copy-Item (Join-Path $SourceRoot 'distributions/windows/templates/bpm-env.cmd'),
        (Join-Path $SourceRoot 'distributions/windows/templates/bpm.cmd'),
        (Join-Path $SourceRoot 'distributions/windows/templates/bpm-migrate.cmd'),
        (Join-Path $SourceRoot 'distributions/windows/templates/bpm-service.cmd'),
        (Join-Path $SourceRoot 'distributions/windows/templates/bpm-service.xml') -Destination $Payload
    Copy-Item (Join-Path $SourceRoot 'distributions/windows/templates/bpm.env') -Destination $State
    $WinSw = Join-Path $WorkRoot 'bpm-service.exe'
    Get-VerifiedDownload $Target.service_wrapper.url $Target.service_wrapper.sha256 $WinSw
    Copy-Item $WinSw -Destination (Join-Path $Payload 'bpm-service.exe')
    @{
        schema_version = 1
        bpm_version = $Version
        source_revision = $SourceRevision
        target = 'windows-10-11-x64'
        python_version = $Target.runtime.python_version
        documentation_archive_sha256 = $DocumentationSha256
        database_migration = 'explicit-bpm-migrate-only'
        service_account = $Target.installer.service_account
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Payload 'release-manifest.json') -Encoding utf8

    Write-Stage "build $Artifact with WiX $($Target.wix.tool_version)"
    if (Test-Path -LiteralPath $OutputArtifact) { Remove-Item -LiteralPath $OutputArtifact -Force }
    & wix build -arch x64 -ext $Target.wix.util_extension `
        -bindpath "payload=$Payload" -bindpath "state=$State" `
        -out $OutputArtifact (Join-Path $SourceRoot 'distributions/windows/Product.wxs')
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $OutputArtifact)) {
        throw 'WiX did not produce the expected MSI artifact'
    }

    $signatureStatus = 'NotSigned'
    if ($env:BPM_WINDOWS_SIGNING_CERTIFICATE_BASE64) {
        if (-not $env:BPM_WINDOWS_SIGNING_CERTIFICATE_PASSWORD) {
            throw 'BPM_WINDOWS_SIGNING_CERTIFICATE_PASSWORD is required when signing is enabled'
        }
        $Pfx = Join-Path $WorkRoot 'bpm-release-signing.pfx'
        [System.IO.File]::WriteAllBytes($Pfx, [Convert]::FromBase64String($env:BPM_WINDOWS_SIGNING_CERTIFICATE_BASE64))
        $SignTool = Get-Command signtool.exe -ErrorAction Stop
        Write-Stage 'sign MSI with Authenticode and RFC 3161 timestamp'
        & $SignTool.Source sign /fd SHA256 /f $Pfx /p $env:BPM_WINDOWS_SIGNING_CERTIFICATE_PASSWORD `
            /tr http://timestamp.digicert.com /td SHA256 $OutputArtifact
        if ($LASTEXITCODE -ne 0) { throw 'Authenticode signing failed' }
        $signatureStatus = (Get-AuthenticodeSignature -LiteralPath $OutputArtifact).Status.ToString()
        if ($signatureStatus -ne 'Valid') { throw "MSI Authenticode status is $signatureStatus" }
    }
    @{
        schema_version = 1
        artifact = $Artifact
        authenticode_status = $signatureStatus
        python_installer_sha256 = $Target.runtime.installer_sha256
        winsw_sha256 = $Target.service_wrapper.sha256
        wix_version = (& wix --version | Select-Object -First 1)
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory 'build-environment.json') -Encoding utf8
    "$(Get-Sha256 $OutputArtifact)  $Artifact" | Set-Content -LiteralPath "$OutputArtifact.sha256" -Encoding ascii
    Write-Stage "MSI built: $OutputArtifact"
}
finally {
    if (Test-Path -LiteralPath $WorkRoot) { Remove-Item -LiteralPath $WorkRoot -Recurse -Force }
}
