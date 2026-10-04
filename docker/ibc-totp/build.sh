#!/bin/bash
# Build IBC with kesor/ibc-totp patch and install into gnzsnz IB Gateway layout.
# Usage: build.sh <IBC_VERSION> <IBC_INSTALL_DIR>
set -euo pipefail

IBC_VERSION="${1:?IBC version required, e.g. 3.23.0}"
IBC_DIR="${2:?IBC install dir required, e.g. /home/ibgateway/ibc}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_URL="https://raw.githubusercontent.com/kesor/ibc-totp/master/ibc-patches/ibc-patch-totp.patch"
GOOGLEAUTH_VERSION="1.5.0"
GOOGLEAUTH_URL="https://repo1.maven.org/maven2/com/warrenstrange/googleauth/${GOOGLEAUTH_VERSION}/googleauth-${GOOGLEAUTH_VERSION}.jar"
IBGW_JTS_ROOT="${IBGW_JTS_ROOT:-/home/ibgateway/Jts}"

_find_gateway_jars() {
  local jars_dir=""
  shopt -s nullglob
  for d in "${IBGW_JTS_ROOT}/ibgateway/"*/jars; do
    if [ -d "$d" ] && compgen -G "$d/*.jar" >/dev/null; then
      jars_dir="$d"
      break
    fi
  done
  shopt -u nullglob
  if [ -z "$jars_dir" ]; then
    echo "ibc-totp: Gateway jars not found under ${IBGW_JTS_ROOT}/ibgateway/*/jars" >&2
    exit 1
  fi
  printf '%s' "$jars_dir"
}

echo "ibc-totp: building IBC ${IBC_VERSION} for ${IBC_DIR}"

# ── Optional apt mirror override ──
#   ports.ubuntu.com (arm64 apt source in the base image) is flaky/unreachable
#   from some networks. Set APT_MIRROR (e.g. http://mirrors.tuna.tsinghua.edu.cn)
#   to rewrite the apt sources before updating. Empty/unset = use image defaults.
#   http:// avoids needing ca-certificates in the (not-yet-updated) base image.
_configure_apt_mirror() {
  local mirror="${APT_MIRROR:-}"
  [ -z "$mirror" ] && return 0
  local arch suffix target pattern
  arch="$(dpkg --print-architecture)"
  case "$arch" in
    arm64|armhf) suffix="ubuntu-ports" ;;
    *) suffix="ubuntu" ;;
  esac
  target="${mirror%/}/${suffix}"
  pattern='https?://(ports\.ubuntu\.com/ubuntu-ports|(cn\.|old-releases\.|security\.)?archive\.ubuntu\.com/ubuntu)'
  if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then
    sed -i -E "s#${pattern}#${target}#g" /etc/apt/sources.list.d/ubuntu.sources
    echo "ibc-totp: apt mirror -> ${target} (deb822)"
  elif [ -f /etc/apt/sources.list ]; then
    sed -i -E "s#${pattern}#${target}#g" /etc/apt/sources.list
    echo "ibc-totp: apt mirror -> ${target}"
  fi
}
# ── Trim apt sources to what this script actually installs ──
#   ant/git/openjdk-17-jdk-headless/curl/ca-certificates/python3 all live in
#   main/universe. `apt-get update` otherwise also fetches the restricted and
#   multiverse Packages indices (several MB) for every suite, plus the
#   noble-backports suite entirely — all dead weight for this build. Dropping
#   them cuts the index download that was taking 240s+ on a slow mirror.
_trim_apt_sources() {
  local deb822=/etc/apt/sources.list.d/ubuntu.sources
  if [ -f "$deb822" ]; then
    sed -i -E \
      -e '/^Suites:/ s/\bnoble-backports\b//g' \
      -e '/^Components:/ s/\b(restricted|multiverse)\b//g' \
      -e '/^(Suites|Components):/ s/[[:space:]]+/ /g' \
      -e '/^(Suites|Components):/ s/[[:space:]]+$//' \
      "$deb822"
    echo "ibc-totp: trimmed apt sources (dropped backports/restricted/multiverse)"
  elif [ -f /etc/apt/sources.list ]; then
    sed -i -E \
      -e '/noble-backports/d' \
      -e 's/\b(restricted|multiverse)\b//g' \
      -e 's/[[:space:]]+/ /g' \
      -e 's/[[:space:]]+$//' \
      /etc/apt/sources.list
    echo "ibc-totp: trimmed apt sources (dropped backports/restricted/multiverse)"
  fi
}
export DEBIAN_FRONTEND=noninteractive
_configure_apt_mirror
_trim_apt_sources
apt-get update -y
# openjdk-17-jdk-headless first, ant second: ant's Depends offers
# "default-jre-headless | java2-runtime-headless" as alternatives, and apt
# only skips default-jre-headless (openjdk-21 on noble) if a package
# providing the other alternative is *already installed* when ant's
# dependency is resolved — not just present in the same install command.
apt-get install -y --no-install-recommends openjdk-17-jdk-headless
apt-get install -y --no-install-recommends ant git curl ca-certificates python3

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

cd "$WORKDIR"
if ! git clone --depth 1 --branch "${IBC_VERSION}" https://github.com/IbcAlpha/IBC.git 2>/dev/null; then
  git clone --depth 1 https://github.com/IbcAlpha/IBC.git
  cd IBC
  git checkout "${IBC_VERSION}"
else
  cd IBC
fi

curl -fsSL "${PATCH_URL}" -o /tmp/ibc-patch-totp.patch
git apply --whitespace=nowarn /tmp/ibc-patch-totp.patch
python3 "${SCRIPT_DIR}/apply-zh-labels.py"

mkdir -p lib
curl -fsSL "${GOOGLEAUTH_URL}" -o "lib/googleauth-${GOOGLEAUTH_VERSION}.jar"

export IBC_BIN="$(_find_gateway_jars)"
_jar_count="$(find "${IBC_BIN}" -maxdepth 1 -name '*.jar' | wc -l | tr -d ' ')"
echo "ibc-totp: IBC_BIN=${IBC_BIN}, jars=${_jar_count}"

export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}"
if [ ! -x "${JAVA_HOME}/bin/javac" ] && command -v java >/dev/null 2>&1; then
  _java_bin="$(readlink -f "$(command -v java)")"
  JAVA_HOME="$(dirname "$(dirname "$_java_bin")")"
  export JAVA_HOME
fi

ant -q jar
test -f resources/IBC.jar

mkdir -p "${IBC_DIR}/lib"
cp -f resources/IBC.jar "${IBC_DIR}/IBC.jar"
cp -f "lib/googleauth-${GOOGLEAUTH_VERSION}.jar" "${IBC_DIR}/lib/"

IBCSTART="${IBC_DIR}/scripts/ibcstart.sh"
if [ -f "$IBCSTART" ] && ! grep -q 'googleauth-1.5.0.jar' "$IBCSTART"; then
  sed -i 's|${ibc_path}/IBC.jar"|${ibc_path}/IBC.jar:${ibc_path}/lib/googleauth-1.5.0.jar"|g' "$IBCSTART"
fi

TMPL="${IBC_DIR}/config.ini.tmpl"
if [ -f "$TMPL" ] && ! grep -q '^TwsTotpSecret=' "$TMPL"; then
  sed -i '/^SecondFactorDevice=/a TwsTotpSecret=${TWS_TOTP_SECRET}' "$TMPL"
fi

chown -R ibgateway:ibgateway "${IBC_DIR}/IBC.jar" "${IBC_DIR}/lib" 2>/dev/null || true
echo "ibc-totp: installed patched IBC.jar ($(wc -c < "${IBC_DIR}/IBC.jar") bytes)"

# ── Build-only cleanup ──
#   ant/git/openjdk-17-jdk-headless were only needed to compile IBC.jar above;
#   none of them are needed at runtime. Purge them here, inside the same RUN
#   as the install, so the final image layer never carries this weight.
#   --auto-remove also catches openjdk-21-jre-headless/default-jre-headless
#   if some future Depends change pulls them in again despite the install
#   ordering above. curl/ca-certificates are left installed — the gnzsnz
#   base image may rely on them at runtime.
apt-get purge -y --auto-remove ant git openjdk-17-jdk-headless
