#
# BPM 0.9.6 container distribution.  The base image is an OCI-index digest;
# Docker resolves the matching linux platform manifest without following a
# mutable tag at release build time.
ARG BPM_PYTHON_IMAGE=python:3.14.3-slim-bookworm@sha256:f21c0d5a44c56805654c15abccc1b2fd576c8d93aca0a3f74b4aba2dc92510e2

FROM ${BPM_PYTHON_IMAGE} AS wheel-builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY app ./app

# Build precisely the application wheel.  Neither development nor optional AI
# extras are installed in this stage or copied into the release image.
RUN python -m pip wheel --no-deps --wheel-dir /wheels .

FROM ${BPM_PYTHON_IMAGE} AS runtime

ARG BPM_SOURCE_REVISION=unknown

LABEL org.opencontainers.image.title="Browser Policy Manager" \
      org.opencontainers.image.description="BPM 0.9.6 single-node Docker distribution" \
      org.opencontainers.image.version="0.9.6" \
      org.opencontainers.image.revision="${BPM_SOURCE_REVISION}" \
      org.opencontainers.image.licenses="MPL-2.0" \
      org.opencontainers.image.source="https://github.com/Goudron/browser-policy-manager"

ENV PATH="/opt/bpm/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    BPM_HOST=0.0.0.0 \
    BPM_PORT=8000 \
    BPM_RELOAD=false \
    BPM_DATABASE_URL=sqlite+aiosqlite:////var/lib/bpm/bpm.db \
    BPM_DOCUMENTATION_SITE_DIR=/opt/bpm/documentation/site

RUN addgroup --system bpm && adduser --system --ingroup bpm --home /nonexistent bpm \
    && python -m venv /opt/bpm/venv

COPY --from=wheel-builder /wheels /tmp/wheels
COPY distributions/docker/requirements.lock /tmp/requirements.lock
RUN pip install --requirement /tmp/requirements.lock \
    && pip install --no-deps /tmp/wheels/browser_policy_manager-*.whl \
    && pip check \
    && rm -rf /tmp/wheels /tmp/requirements.lock

WORKDIR /opt/bpm

# Alembic revisions are deliberately outside the Python wheel.  They are a
# separately visible, release-owned payload used only by the explicit
# `migrate` command below.
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

# A Docker distributive is built only after documentation/package verification.
# Do not substitute app/documentation/site: it is a local development cache.
COPY documentation/dist/bpm-documentation-0.9.6.tar.gz /tmp/bpm-documentation.tar.gz
RUN mkdir -p /opt/bpm/documentation/site /var/lib/bpm \
    && tar --extract --gzip --file /tmp/bpm-documentation.tar.gz \
        --strip-components=1 --directory /opt/bpm/documentation/site \
    && rm /tmp/bpm-documentation.tar.gz \
    && chown -R bpm:bpm /opt/bpm /var/lib/bpm

COPY distributions/docker/entrypoint.sh /usr/local/bin/bpm
RUN chmod 0555 /usr/local/bin/bpm

USER bpm

VOLUME ["/var/lib/bpm"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health/ready', timeout=3).read()"

ENTRYPOINT ["/usr/local/bin/bpm"]
CMD ["serve"]
