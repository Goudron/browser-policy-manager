#!/usr/bin/env bash
# Build one BPM 0.9.6 native package inside its frozen target userspace.
# This script is executed only by tools/native_distribution.py with /source
# mounted read-only and /output mounted as a disposable artifact directory.
set -euo pipefail

readonly SOURCE_ROOT=/source
readonly WORK_ROOT=/work
readonly STAGE_ROOT="$WORK_ROOT/stage"
readonly WHEELHOUSE="$WORK_ROOT/wheelhouse"
readonly RUNTIME_PREFIX=/opt/bpm/runtime
readonly VENV_PREFIX=/opt/bpm/venv
readonly BPM_VERSION=0.9.6
readonly PYTHON_VERSION=3.14.6
readonly PYTHON_SHA256=143b1dddefaec3bd2e21e3b839b34a2b7fb9842272883c576420d605e9f30c63
readonly PACKAGE_NAME=browser-policy-manager

required_environment=(
    BPM_NATIVE_TARGET
    BPM_NATIVE_FORMAT
    BPM_NATIVE_ARTIFACT
    BPM_NATIVE_PACKAGE_RELEASE
    BPM_NATIVE_RUNTIME_DEPENDENCIES
    BPM_NATIVE_SOURCE_REVISION
)
for variable_name in "${required_environment[@]}"; do
    if [[ -z "${!variable_name:-}" ]]; then
        echo "[native-build] missing required environment: ${variable_name}" >&2
        exit 64
    fi
done

log() {
    printf '[native-build] target=%s %s\n' "$BPM_NATIVE_TARGET" "$*" >&2
}

install_build_prerequisites() {
    case "$BPM_NATIVE_TARGET" in
        ubuntu-26-04 | debian-13-5 | linux-mint-22-3)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update
            apt-get install --yes --no-install-recommends \
                build-essential ca-certificates curl dpkg-dev git \
                libbz2-dev libffi-dev libgdbm-dev liblzma-dev \
                libncurses-dev libreadline-dev libsqlite3-dev libssl-dev \
                tk-dev uuid-dev xz-utils zlib1g-dev
            ;;
        fedora-44)
            dnf install --assumeyes \
                bzip2 bzip2-devel ca-certificates curl findutils gcc gcc-c++ \
                gdbm-devel libffi-devel make ncurses-devel openssl-devel \
                readline-devel rpm-build sqlite-devel tar xz xz-devel zlib-devel
            ;;
        manjaro-stable)
            pacman -Syu --noconfirm --needed \
                base-devel bzip2 ca-certificates curl gdbm libffi ncurses \
                openssl readline sqlite systemd tar xz zlib
            test "$(pacman-mirrors -G)" = "stable"
            ;;
        *)
            echo "[native-build] unsupported target: $BPM_NATIVE_TARGET" >&2
            exit 64
            ;;
    esac
}

build_private_python() {
    local archive="Python-${PYTHON_VERSION}.tar.xz"
    local source_directory="$WORK_ROOT/Python-${PYTHON_VERSION}"

    log "download and verify CPython ${PYTHON_VERSION}"
    mkdir -p "$WORK_ROOT"
    cd "$WORK_ROOT"
    curl --fail --location --silent --show-error \
        --connect-timeout 30 --max-time 900 --retry 5 --retry-all-errors \
        --output "$archive" \
        "https://www.python.org/ftp/python/${PYTHON_VERSION}/${archive}"
    printf '%s  %s\n' "$PYTHON_SHA256" "$archive" | sha256sum --check --status
    tar --extract --file "$archive"

    log "compile private CPython runtime"
    cd "$source_directory"
    ./configure --prefix="$RUNTIME_PREFIX" --with-ensurepip=install
    make -j"$(nproc)"
    make altinstall
}

assemble_runtime_payload() {
    local runtime_python="${RUNTIME_PREFIX}/bin/python3.14"
    local documentation_archive="${SOURCE_ROOT}/documentation/dist/bpm-documentation-${BPM_VERSION}.tar.gz"
    local documentation_checksum="${documentation_archive}.sha256"
    local build_source="$WORK_ROOT/bpm-source"

    log "create locked BPM virtual environment"
    "$runtime_python" -m ensurepip --upgrade
    "$runtime_python" -m pip install --disable-pip-version-check --retries 5 --timeout 60 --upgrade \
        pip==25.3 setuptools==84.0.0 wheel==0.47.0
    mkdir -p "$WHEELHOUSE"
    "$runtime_python" -m pip wheel --disable-pip-version-check --retries 5 --timeout 60 --only-binary=:all: \
        --wheel-dir "$WHEELHOUSE" \
        --requirement "${SOURCE_ROOT}/distributions/docker/requirements.lock"
    rm -rf "$build_source"
    mkdir -p "$build_source"
    cp --archive "$SOURCE_ROOT/pyproject.toml" "$SOURCE_ROOT/README.md" \
        "$SOURCE_ROOT/LICENSE" "$build_source/"
    cp --archive "$SOURCE_ROOT/app" "$build_source/app"
    "$runtime_python" -m pip wheel --disable-pip-version-check --no-deps --no-build-isolation \
        --wheel-dir "$WHEELHOUSE" "$build_source"
    "$runtime_python" -m venv --copies "$VENV_PREFIX"
    "$VENV_PREFIX/bin/python" -m pip install --disable-pip-version-check --no-index \
        --find-links "$WHEELHOUSE" \
        --requirement "${SOURCE_ROOT}/distributions/docker/requirements.lock"
    "$VENV_PREFIX/bin/python" -m pip install --disable-pip-version-check --no-index \
        --find-links "$WHEELHOUSE" --no-deps \
        "$WHEELHOUSE"/browser_policy_manager-"${BPM_VERSION}"-*.whl
    "$VENV_PREFIX/bin/python" -m pip check
    "$VENV_PREFIX/bin/python" -I -c "
import importlib.metadata
import importlib.util
import app.main

assert importlib.metadata.version('browser-policy-manager') == '${BPM_VERSION}'
assert all(importlib.util.find_spec(name) is None for name in ('numpy', 'onnxruntime', 'tokenizers'))
"

    log "install verified documentation and migration payload"
    test -f "$documentation_archive"
    test -f "$documentation_checksum"
    (
        cd "$(dirname "$documentation_archive")"
        sha256sum --check "$(basename "$documentation_checksum")"
    )
    mkdir -p /opt/bpm/documentation/site
    tar --extract --gzip --file "$documentation_archive" --strip-components=1 \
        --directory /opt/bpm/documentation/site
    cp -a "${SOURCE_ROOT}/alembic" /opt/bpm/alembic
    install --mode=0644 "${SOURCE_ROOT}/alembic.ini" /opt/bpm/alembic.ini
    install --mode=0644 "${SOURCE_ROOT}/distributions/docker/requirements.lock" \
        /opt/bpm/requirements.lock
    install --mode=0644 "${SOURCE_ROOT}/LICENSE" /opt/bpm/LICENSE
    install --mode=0644 "${SOURCE_ROOT}/documentation/config/THIRD_PARTY_NOTICES.md" \
        /opt/bpm/THIRD_PARTY_NOTICES.md
    find /opt/bpm -type d -name __pycache__ -prune -exec rm -rf {} +
}

prepare_stage() {
    local documentation_sha

    log "stage native package payload"
    rm -rf "$STAGE_ROOT"
    mkdir -p "$STAGE_ROOT/opt" "$STAGE_ROOT/etc/bpm" "$STAGE_ROOT/usr/bin" \
        "$STAGE_ROOT/usr/lib/systemd/system" "$STAGE_ROOT/var/lib/bpm"
    cp -a /opt/bpm "$STAGE_ROOT/opt/bpm"
    install --mode=0644 "${SOURCE_ROOT}/distributions/native/templates/bpm.env" \
        "$STAGE_ROOT/etc/bpm/bpm.env"
    install --mode=0755 "${SOURCE_ROOT}/distributions/native/templates/bpm" \
        "$STAGE_ROOT/usr/bin/bpm"
    install --mode=0755 "${SOURCE_ROOT}/distributions/native/templates/bpm-migrate" \
        "$STAGE_ROOT/usr/bin/bpm-migrate"
    install --mode=0644 "${SOURCE_ROOT}/distributions/native/templates/bpm.service" \
        "$STAGE_ROOT/usr/lib/systemd/system/bpm.service"
    documentation_sha="$(sha256sum "${SOURCE_ROOT}/documentation/dist/bpm-documentation-${BPM_VERSION}.tar.gz" | awk '{print $1}')"
    cat >"$STAGE_ROOT/opt/bpm/release-manifest.json" <<EOF
{
  "schema_version": 1,
  "bpm_version": "${BPM_VERSION}",
  "source_revision": "${BPM_NATIVE_SOURCE_REVISION}",
  "target": "${BPM_NATIVE_TARGET}",
  "python_version": "${PYTHON_VERSION}",
  "documentation_archive_sha256": "${documentation_sha}",
  "database_migration": "explicit-bpm-migrate-only"
}
EOF
}

write_build_environment() {
    case "$BPM_NATIVE_FORMAT" in
        deb)
            dpkg-query --show --showformat='${binary:Package}=${Version}\n' | LC_ALL=C sort \
                >"/output/build-environment.txt"
            ;;
        rpm)
            rpm --query --all --queryformat '%{NAME}=%{VERSION}-%{RELEASE}.%{ARCH}\n' \
                | LC_ALL=C sort >"/output/build-environment.txt"
            ;;
        arch)
            pacman --query | LC_ALL=C sort >"/output/build-environment.txt"
            ;;
    esac
    printf 'target=%s\nformat=%s\nsource_revision=%s\n' \
        "$BPM_NATIVE_TARGET" "$BPM_NATIVE_FORMAT" "$BPM_NATIVE_SOURCE_REVISION" \
        >>"/output/build-environment.txt"
}

comma_lines() {
    tr ',' '\n' <<<"$1" | sed 's/^ *//; s/ *$//' | sed '/^$/d'
}

build_deb() {
    local control="$STAGE_ROOT/DEBIAN"
    local depends
    depends="$(tr '\n' ',' <<<"$(comma_lines "$BPM_NATIVE_RUNTIME_DEPENDENCIES")" | sed 's/,$//; s/,/, /g')"
    mkdir -p "$control"
    cat >"$control/control" <<EOF
Package: ${PACKAGE_NAME}
Version: ${BPM_VERSION}-${BPM_NATIVE_PACKAGE_RELEASE}
Section: admin
Priority: optional
Architecture: amd64
Maintainer: Valery Ledovskoy
Depends: ${depends}
Description: Browser Policy Manager
 Browser Policy Manager manages Firefox Enterprise policies through a local web application.
 This package contains a private CPython 3.14.6 runtime and does not modify the system Python.
EOF
    printf '/etc/bpm/bpm.env\n' >"$control/conffiles"
    cat >"$control/postinst" <<'EOF'
#!/bin/sh
set -eu
if ! getent group bpm >/dev/null 2>&1; then
    addgroup --system bpm
fi
if ! getent passwd bpm >/dev/null 2>&1; then
    adduser --system --ingroup bpm --home /nonexistent --no-create-home bpm
fi
install -d -m 0750 -o bpm -g bpm /var/lib/bpm
systemctl daemon-reload >/dev/null 2>&1 || true
# BPM migrations and service activation are explicit operator actions.
EOF
    cat >"$control/postrm" <<'EOF'
#!/bin/sh
set -eu
systemctl daemon-reload >/dev/null 2>&1 || true
# State and the bpm account remain for operator-controlled recovery.
EOF
    chmod 0755 "$control/postinst" "$control/postrm"
    dpkg-deb --root-owner-group --build "$STAGE_ROOT" "/output/${BPM_NATIVE_ARTIFACT}"
}

build_rpm() {
    local rpm_root="$WORK_ROOT/rpmbuild"
    local spec="$rpm_root/SPECS/${PACKAGE_NAME}.spec"
    local requires
    requires="$(comma_lines "$BPM_NATIVE_RUNTIME_DEPENDENCIES" | sed 's/^/Requires: /')"
    rm -rf "$rpm_root"
    mkdir -p "$rpm_root"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
    cat >"$spec" <<EOF
Name: ${PACKAGE_NAME}
Version: ${BPM_VERSION}
Release: ${BPM_NATIVE_PACKAGE_RELEASE}
Summary: Browser Policy Manager
License: MPL-2.0
BuildArch: x86_64
# BPM carries a private CPython under /opt.  Fedora's generic buildroot hook
# must not rewrite its standard-library shebangs to the system interpreter.
%global __brp_mangle_shebangs %{nil}
# The runtime dependencies below are an explicit target contract.  Automatic
# RPM detection incorrectly turns the %pre account creation into requirements
# on a not-yet-existing user and group.
AutoReq: no
${requires}

%description
Browser Policy Manager manages Firefox Enterprise policies through a local web application.

%prep

%build

%install
rm -rf %{buildroot}
cp -a ${STAGE_ROOT}/. %{buildroot}/

%pre
getent group bpm >/dev/null || groupadd --system bpm
getent passwd bpm >/dev/null || useradd --system --gid bpm --home-dir /nonexistent --shell /sbin/nologin bpm

%files
/opt/bpm
%dir /etc/bpm
%config(noreplace) /etc/bpm/bpm.env
/usr/bin/bpm
/usr/bin/bpm-migrate
/usr/lib/systemd/system/bpm.service
%dir %attr(0750,bpm,bpm) /var/lib/bpm

%changelog
* 2026-08-13 Valery Ledovskoy - ${BPM_VERSION}-${BPM_NATIVE_PACKAGE_RELEASE}
- BPM ${BPM_VERSION} native distribution
EOF
    rpmbuild --define "_topdir ${rpm_root}" --bb "$spec"
    cp "$rpm_root/RPMS/x86_64/${BPM_NATIVE_ARTIFACT}" "/output/${BPM_NATIVE_ARTIFACT}"
}

build_arch() {
    local package_root="$WORK_ROOT/pkgbuild"
    local dependencies
    dependencies="$(comma_lines "$BPM_NATIVE_RUNTIME_DEPENDENCIES" | sed "s/^/'/; s/$/'/" | paste -sd' ' -)"
    rm -rf "$package_root"
    mkdir -p "$package_root"
    cp -a "$STAGE_ROOT" "$package_root/stage"
    cat >"$package_root/PKGBUILD" <<EOF
pkgname=${PACKAGE_NAME}
pkgver=${BPM_VERSION}
pkgrel=${BPM_NATIVE_PACKAGE_RELEASE}
pkgdesc='Browser Policy Manager'
arch=('x86_64')
url='https://github.com/Goudron/browser-policy-manager'
license=('MPL-2.0')
depends=(${dependencies})
backup=('etc/bpm/bpm.env')
install='bpm.install'

package() {
  cp -a "\${startdir}/stage/." "\${pkgdir}/"
}
EOF
    cat >"$package_root/bpm.install" <<'EOF'
post_install() {
  getent group bpm >/dev/null || groupadd --system bpm
  getent passwd bpm >/dev/null || useradd --system --gid bpm --home-dir /nonexistent --shell /usr/bin/nologin bpm
  install -d -m 0750 -o bpm -g bpm /var/lib/bpm
  # BPM migrations and service activation are explicit operator actions.
}

post_upgrade() {
  install -d -m 0750 -o bpm -g bpm /var/lib/bpm
  # Do not migrate or start BPM during an upgrade.
}
EOF
    id --user builder >/dev/null 2>&1 || useradd --create-home --shell /bin/bash builder
    chown -R builder:builder "$package_root"
    runuser -u builder -- bash -c "cd '$package_root' && makepkg --nodeps --noconfirm"
    cp "$package_root/${BPM_NATIVE_ARTIFACT}" "/output/${BPM_NATIVE_ARTIFACT}"
}

main() {
    log "install target build prerequisites"
    install_build_prerequisites
    build_private_python
    assemble_runtime_payload
    prepare_stage
    case "$BPM_NATIVE_FORMAT" in
        deb) build_deb ;;
        rpm) build_rpm ;;
        arch) build_arch ;;
        *)
            echo "[native-build] unsupported package format: $BPM_NATIVE_FORMAT" >&2
            exit 64
            ;;
    esac
    write_build_environment
    (
        cd /output
        sha256sum "$BPM_NATIVE_ARTIFACT" >"${BPM_NATIVE_ARTIFACT}.sha256"
    )
    log "built ${BPM_NATIVE_ARTIFACT}"
}

main "$@"
