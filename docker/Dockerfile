# VT25_2x live trader — python -m vtlive scheduler
#
# One container per broker (alpaca / ibkr):
#   - Alpaca mode: runs only Python trader
#   - IBKR mode: runs both IB Gateway (Java) and Python trader via direct process management
#
# For IBKR mode, we use gnzsnz/ib-gateway as the base which includes:
#   - Java runtime (JDK or JRE)
#   - IB Gateway (IBC + TWS)
#   - Xvfb for display handling
#   - Necessary X11 utilities
#
# State and logs live in the mounted /app/runtime/<BROKER>/ folder
# live/config.yaml is mounted read-only so edits take effect on restart without a rebuild

ARG IB_GATEWAY_VERSION=stable
FROM ghcr.io/gnzsnz/ib-gateway:${IB_GATEWAY_VERSION}

USER root

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VT_RUNTIME_DIR=/app/runtime \
    XDG_CACHE_HOME=/app/runtime/.cache \
    HOME=/app/runtime

# Fix apt sources and install Python (adapted from intraday-pulse-live)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then \
      sed -i -E \
        -e '/^Suites:/ s/\bnoble-backports\b//g' \
        -e '/^Components:/ s/\b(restricted|multiverse)\b//g' \
        -e '/^(Suites|Components):/ s/[[:space:]]+/ /g' \
        -e '/^(Suites|Components):/ s/[[:space:]]+$//' \
        /etc/apt/sources.list.d/ubuntu.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
      sed -i -E \
        -e '/noble-backports/d' \
        -e 's/\b(restricted|multiverse)\b//g' \
        -e 's/[[:space:]]+/ /g' \
        -e 's/[[:space:]]+$//' \
        /etc/apt/sources.list; \
    fi \
    && apt-get update && apt-get install --no-install-recommends -y \
      python3 python3-pip python3-setuptools

# Ensure directories have correct permissions
RUN mkdir -p /home/ibgateway/{Jts,ibc} && \
    chmod -R 777 /home/ibgateway/{Jts,ibc} 2>/dev/null || true

# ── IBC + TOTP patch — auto 2FA login without phone approval ──
#   kesor/ibc-totp patches IBC to generate TOTP codes from IBKR_TOTP_SECRET
#   so 2FA login is fully automated
ARG IBC_VERSION=3.23.0
COPY docker/ibc-totp/ /tmp/ibc-totp/
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    sed -i -E \
      -e '/^Suites:/ s/\bnoble-backports\b//g' \
      -e '/^Components:/ s/\b(restricted|multiverse)\b//g' \
      /etc/apt/sources.list.d/ubuntu.sources 2>/dev/null || true && \
    chmod +x /tmp/ibc-totp/build.sh && \
    /tmp/ibc-totp/build.sh "${IBC_VERSION}" /home/ibgateway/ibc

WORKDIR /app
COPY requirements-live.txt .
# optional build secret "extra_ca": CA bundle for builds behind a TLS-inspecting proxy
# Note: Using --break-system-packages to work around PEP 668 restriction in Debian 12+
RUN --mount=type=secret,id=extra_ca,required=false \
    if [ -f /run/secrets/extra_ca ]; then export PIP_CERT=/run/secrets/extra_ca; fi; \
    pip install --break-system-packages -r requirements-live.txt

COPY qlab/ qlab/
COPY vtlive/ vtlive/
COPY live/config.yaml live/config.yaml
COPY data/processed/ data/processed/

# Copy entrypoint script (direct process management, no supervisor)
COPY docker/entrypoint-ibkr.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /app/runtime && chmod 777 /app/runtime

# scheduler writes runtime/<BROKER>/heartbeat at least every 5 minutes
HEALTHCHECK --interval=5m --timeout=20s --start-period=2m --retries=2 \
  CMD python3 -c "import glob,os,sys,time; f=glob.glob('/app/runtime/*/heartbeat'); sys.exit(0 if f and time.time()-max(map(os.path.getmtime,f))<900 else 1)"

ENTRYPOINT ["/entrypoint.sh"]
