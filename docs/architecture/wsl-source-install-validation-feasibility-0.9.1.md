# BPM 0.9.1 WSL source-install validation feasibility

Status: **Runner prepared; actual Windows hosts required**

Backlog owner: BPM091-M11-10

## Decision

The BPM Linux source-install assertions can be reused inside Ubuntu 26.04 on WSL 2, but the
Windows/WSL integration boundary cannot be validated on the current Linux maintainer host or in a
Docker container. BPM091-M11-10 therefore prepares a fail-closed PowerShell runner and evidence
contract without making a Windows 10, Windows 11, WSL kernel, systemd, filesystem, localhost,
browser, shutdown, or restart claim.

Actual Windows 10 and Windows 11 hosts remain required for genuine validation. BPM091-M11-11 and
BPM091-M11-12 closed their conditional no-host paths without making Windows validation claims;
future actual-host reruns remain allowed.

## Reused source-install boundary

The installed WSL checkout must come from the exact Ubuntu 26.04 procedure in
documentation/src/dita/en/admin/admin-task-install-ubuntu-26-04-source.dita at the source hash
recorded by documentation/config/wsl-source-install-validation-contract-0.9.1.json. This reuses
the accepted package, Python 3.14, immutable checkout, virtual environment, editable installation,
migration, and six-locale documentation commands.

The runner does not install or update WSL and does not replace those Linux commands with native
Windows commands. Its only runtime adapter binds the foreground development process to 0.0.0.0
so the supplied Windows host can test WSL localhost forwarding and Edge access. That adapter is
validation-only and does not authorize external exposure or a production topology.

## Runner

Run documentation/tools/wsl_source_install_validation.ps1 from PowerShell on the actual target
host. The supplied checkout path is a Linux path inside the named WSL distribution and must resolve
under /home, never /mnt, /media, or another host-shared mount.

Preflight example:

    pwsh -NoProfile -File documentation/tools/wsl_source_install_validation.ps1 `
      -WindowsTarget Windows11 `
      -Distro Ubuntu-26.04 `
      -BpmRef <40-character-lowercase-commit> `
      -CheckoutPath /home/<linux-user>/browser-policy-manager `
      -PreflightOnly

Omit -PreflightOnly only after reviewing its evidence. Full validation runs migrations and
documentation checks, starts BPM, performs WSL and Windows probes, loads /profiles through
headless Windows Edge, stops BPM and proves connection refusal, terminates and restarts only the
named WSL distribution, proves the old BPM process is absent, and repeats the complete runtime
cycle.

## Evidence matrix

| Boundary | Runner evidence | Pass requirement |
| --- | --- | --- |
| Windows host | Caption, version, build, architecture, PowerShell version | Caption matches the requested Windows 10 or Windows 11 target |
| WSL version | wsl.exe --version, --status, --list --verbose | Version output exists and the named distribution reports WSL 2 |
| Distribution | /etc/os-release, uname -a, /proc/version | Ubuntu 26.04 is observed inside WSL |
| systemd | PID 1, systemctl is-system-running, /etc/wsl.conf | Mode is recorded; no BPM service behavior is inferred |
| Filesystem | pwd -P, wslpath -w, filesystem type | Checkout is under the WSL Linux /home filesystem |
| Source state | immutable Git ref, clean state, Python, Alembic, docs | Approved ref, Python 3.14+, migration and all docs checks pass |
| Localhost | WSL curl and Windows Invoke-WebRequest | Health, readiness, and /profiles answer in both runtime cycles |
| Browser | resolved msedge.exe, exit code, captured DOM | Windows Edge returns HTML from /profiles in both cycles |
| Shutdown | PID/PGID stop plus negative probes | WSL and Windows reject /health after each stop |
| Restart | wsl.exe --terminate, identity recheck, old PID check | Old BPM runtime is absent and the second cycle passes |
| Evidence | events, raw outputs, logs, summary, SHA-256 inventory | Complete bounded run directory contains no credentials |

## Feasibility and blockers

The runner is feasible on a host that provides PowerShell, current wsl.exe --version support,
WSL 2, an Ubuntu 26.04 distribution, Windows Edge or an explicitly supplied Edge executable, and
permission to terminate only that distribution. It intentionally blocks when any identity is
ambiguous, the checkout is on a Windows-mounted filesystem, the Git ref is not an exact lowercase
40-character commit, Windows localhost or Edge cannot reach BPM, shutdown leaves a responding
process, or restart preserves the old BPM runtime.

The runner never changes Windows Firewall, portproxy, Hyper-V, virtualization, registry, services,
scheduled tasks, IIS, proxy, TLS, DNS, or WSL installation state. It does not invoke Docker, handle
credentials, use production data, or claim native Windows support or production readiness.

## Current disposition

- Windows 10: unverified-no-actual-host-supplied. BPM091-M11-11 records the conditional boundary in
  `documentation/evidence/live-source-install/0.9.1/m11-11-windows10-wsl-20260715/run-manifest.json`
  and makes no Windows 10 validation claim.
- Windows 11: unverified-no-actual-host-supplied. BPM091-M11-12 records the conditional boundary in
  `documentation/evidence/live-source-install/0.9.1/m11-12-windows11-wsl-20260715/run-manifest.json`
  and makes no Windows 11 validation claim.
- Current Linux host: unsuitable for either outcome and deliberately not used to execute the runner.

Static contract checks can prove runner shape, fail-closed guards, evidence ownership, and forbidden
operations. They cannot turn this preparation task into Windows/WSL execution evidence.
