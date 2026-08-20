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

function Get-StableWixId([string]$Prefix, [string]$Value) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value.ToLowerInvariant())
    $digest = [System.Security.Cryptography.SHA256]::HashData($bytes)
    $suffix = [System.BitConverter]::ToString($digest).Replace('-', '').Substring(0, 24)
    return "${Prefix}_$suffix"
}

function Get-PayloadRelativePath([string]$FullName) {
    return $FullName.Substring($Payload.Length).TrimStart('\').Replace('\', '/')
}

function New-HarvestedPayloadFragment([string]$Destination) {
    $payloadFiles = @(
        Get-ChildItem -LiteralPath $Payload -File -Recurse |
            Where-Object { (Get-PayloadRelativePath $_.FullName) -ne 'bpm-service.exe' } |
            Sort-Object FullName
    )
    if ($payloadFiles.Count -eq 0) {
        throw 'Windows MSI payload contains no application files to harvest'
    }
    $payloadDirectories = @(
        Get-ChildItem -LiteralPath $Payload -Directory -Recurse |
            ForEach-Object { Get-PayloadRelativePath $_.FullName } |
            Sort-Object
    )
    $directoryIds = @{}
    foreach ($relativeDirectory in $payloadDirectories) {
        $directoryIds[$relativeDirectory] = Get-StableWixId 'BpmDirectory' $relativeDirectory
    }

    $lines = [System.Collections.Generic.List[string]]::new()
    $null = $lines.Add('<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">')
    $null = $lines.Add('  <Fragment>')
    $null = $lines.Add('    <DirectoryRef Id="INSTALLFOLDER">')

    function Add-PayloadDirectories([string]$ParentRelativePath, [int]$Depth) {
        $children = @($payloadDirectories | Where-Object {
            $separator = $_.LastIndexOf('/')
            $parent = if ($separator -lt 0) { '' } else { $_.Substring(0, $separator) }
            $parent -eq $ParentRelativePath
        })
        foreach ($relativeDirectory in $children) {
            $nameSeparator = $relativeDirectory.LastIndexOf('/')
            $name = if ($nameSeparator -lt 0) {
                $relativeDirectory
            } else {
                $relativeDirectory.Substring($nameSeparator + 1)
            }
            $indent = '  ' * $Depth
            $directoryId = $directoryIds[$relativeDirectory]
            $escapedName = [System.Security.SecurityElement]::Escape($name)
            $null = $lines.Add(
                ('{0}<Directory Id="{1}" Name="{2}">' -f $indent, $directoryId, $escapedName)
            )
            Add-PayloadDirectories $relativeDirectory ($Depth + 1)
            $null = $lines.Add("$indent</Directory>")
        }
    }

    Add-PayloadDirectories '' 3
    $null = $lines.Add('    </DirectoryRef>')
    $null = $lines.Add('    <ComponentGroup Id="BpmPayload">')
    foreach ($payloadFile in $payloadFiles) {
        $relativeFile = Get-PayloadRelativePath $payloadFile.FullName
        $separator = $relativeFile.LastIndexOf('/')
        $parentDirectory = if ($separator -lt 0) { '' } else { $relativeFile.Substring(0, $separator) }
        $directoryId = if ($parentDirectory) { $directoryIds[$parentDirectory] } else { 'INSTALLFOLDER' }
        $componentId = Get-StableWixId 'BpmComponent' $relativeFile
        $fileId = Get-StableWixId 'BpmFile' $relativeFile
        $source = [System.Security.SecurityElement]::Escape(
            ('!(bindpath.payload)\' + $relativeFile.Replace('/', '\'))
        )
        $null = $lines.Add(
            ('      <Component Id="{0}" Directory="{1}" Guid="*">' -f $componentId, $directoryId)
        )
        $null = $lines.Add(
            ('        <File Id="{0}" Source="{1}" KeyPath="yes" />' -f $fileId, $source)
        )
        $null = $lines.Add('      </Component>')
    }
    $null = $lines.Add('    </ComponentGroup>')
    $null = $lines.Add('  </Fragment>')
    $null = $lines.Add('</Wix>')
    Set-Content -LiteralPath $Destination -Value $lines -Encoding utf8
}

function New-WindowsAlembicConfiguration([string]$Source, [string]$Destination) {
    $configuration = @(
        Get-Content -LiteralPath $Source |
            Where-Object { -not $_.TrimStart().StartsWith('#') }
    )
    if ($configuration.Count -eq 0) {
        throw 'Windows Alembic configuration has no executable settings'
    }
    Set-Content -LiteralPath $Destination -Value $configuration -Encoding ascii
}

if (-not $IsWindows) {
    throw 'Windows MSI assembly must run on a native Windows x64 host.'
}
if (-not [Environment]::Is64BitOperatingSystem) {
    throw 'BPM 0.9.5.1 Windows MSI supports x64 hosts only.'
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
    & $RuntimePython -m pip install --disable-pip-version-check --no-index --find-links $Wheelhouse `
        --requirement (Join-Path $SourceRoot 'distributions/windows/requirements.windows.lock')
    if ($LASTEXITCODE -ne 0) { throw 'failed to install locked Windows base runtime' }
    $BpmWheel = Get-ChildItem -LiteralPath $Wheelhouse -Filter "browser_policy_manager-$Version-*.whl" |
        Select-Object -First 1
    if ($null -eq $BpmWheel) { throw 'BPM wheel is absent from the private wheelhouse' }
    & $RuntimePython -m pip install --disable-pip-version-check --no-index --find-links $Wheelhouse `
        --no-deps $BpmWheel.FullName
    if ($LASTEXITCODE -ne 0) { throw 'failed to install BPM into the private Windows runtime' }
    & $RuntimePython -I -c "import importlib.metadata, importlib.util, app.main; assert importlib.metadata.version('browser-policy-manager') == '$Version'; assert all(importlib.util.find_spec(name) is None for name in ('numpy', 'onnxruntime', 'tokenizers'))"
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
    New-WindowsAlembicConfiguration (Join-Path $SourceRoot 'alembic.ini') (Join-Path $Payload 'alembic.ini')
    Copy-Item (Join-Path $SourceRoot 'LICENSE') -Destination $Payload
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
    $PayloadFragment = Join-Path $WorkRoot 'harvested-payload.wxs'
    New-HarvestedPayloadFragment $PayloadFragment
    & wix build -arch x64 -ext $Target.wix.util_extension `
        -bindpath "payload=$Payload" -bindpath "state=$State" `
        -out $OutputArtifact (Join-Path $SourceRoot 'distributions/windows/Product.wxs') $PayloadFragment
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
