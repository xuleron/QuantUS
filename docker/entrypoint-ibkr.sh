#!/bin/bash
# Single container: IB Gateway (Java) + VT25_2x Trader (Python)
# Direct process management (no supervisor) - inspired by intraday-pulse-live
set -eo pipefail

export TZ=America/New_York

# Load .env - sourcing it sets all variables
if [ -f /app/.env ]; then
  set -a
  . /app/.env
  set +a
fi

# Alpaca mode: just run trader
if [[ "$BROKER" != ibkr* ]]; then
  exec python3 -m vtlive scheduler
fi

# IBKR mode: start both services
echo "═══════════════════════════════════════════════════════════════════"
echo "Starting VT25_2x Trader with integrated IB Gateway"
echo "───────────────────────────────────────────────────────────────────"
echo "  BROKER: $BROKER"
echo "  IBKR_HOST: ${IBKR_HOST:-127.0.0.1}"
echo "  IBKR_PORT: ${IBKR_PORT:-4001}"
echo "  IBKR_USERNAME: ${IBKR_USERNAME:-<not set>}"
echo "  IBKR_TRADING_MODE: ${IBKR_TRADING_MODE:-paper}"
echo "  2FA Device: ${IBKR_2FA_DEVICE:-Mobile Authenticator app}"
echo ""
echo "This container includes:"
echo "  • IB Gateway (Java) - connects to Interactive Brokers"
echo "  • VT25_2x Trader (Python) - runs trading scheduler"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

mkdir -p /app/runtime
chmod 777 /app/runtime 2>/dev/null || true
mkdir -p /home/ibgateway/{Jts,ibc} 2>/dev/null || true
chmod -R 777 /home/ibgateway/{Jts,ibc} 2>/dev/null || true

# Export IB Gateway environment variables (required by run.sh and common.sh)
export SCRIPT_PATH=/home/ibgateway/scripts
export DISPLAY=:1
export TWS_USERID="${IBKR_USERNAME}"
export TWS_PASSWORD="${IBKR_PASSWORD}"
export TRADING_MODE="${IBKR_TRADING_MODE:-paper}"
export TWOFA_DEVICE="${IBKR_2FA_DEVICE:-Mobile Authenticator app}"
export TWS_TOTP_SECRET="${IBKR_TOTP_SECRET}"
export IBC_INI=/home/ibgateway/ibc/config.ini
export IBC_INI_TMPL=/home/ibgateway/ibc/config.ini.tmpl
export TWS_SETTINGS_PATH=/home/ibgateway/Jts

# Start IB Gateway directly (run.sh manages Xvfb internally)
GW_PORT="${IBKR_PORT:-4001}"
GW_WAIT_SECONDS="${IBKR_GW_WAIT:-120}"

echo ">> Starting IB Gateway (logs → runtime/ib-gateway.log)…"
/home/ibgateway/scripts/run.sh >> /app/runtime/ib-gateway.log 2>&1 &
GW_PID=$!

TRADER_PID=""
cleanup() {
  echo ">> Shutting down…"
  [ -n "$TRADER_PID" ] && kill -TERM "$TRADER_PID" 2>/dev/null || true
  kill -TERM "$GW_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup SIGTERM SIGINT

# Wait for Gateway API to be ready
echo ">> Waiting for IB Gateway API on 127.0.0.1:${GW_PORT} (up to ${GW_WAIT_SECONDS}s)…"
_deadline=$((SECONDS + GW_WAIT_SECONDS))
until (exec 3<>"/dev/tcp/127.0.0.1/${GW_PORT}") 2>/dev/null; do
  exec 3>&- 2>/dev/null || true
  if ! kill -0 "$GW_PID" 2>/dev/null; then
    echo "!! IB Gateway exited before API came up"; exit 1
  fi
  if [ "$SECONDS" -ge "$_deadline" ]; then
    echo "!! Timed out waiting for IB Gateway API"; cleanup; exit 1
  fi
  sleep 2
done
exec 3>&- 2>/dev/null || true
echo ">> IB Gateway API ready"

# Start trader in background
cd /app
echo ">> Starting VT25_2x Trader (BROKER=$BROKER)…"
python3 -m vtlive scheduler >> /app/runtime/vtlive.log 2>&1 &
TRADER_PID=$!

# Monitor both processes
while true; do
  _exit=0
  wait -n "$GW_PID" "$TRADER_PID" || _exit=$?
  if ! kill -0 "$GW_PID" 2>/dev/null; then
    echo ">> IB Gateway exited (${_exit}) — stopping container"
    cleanup; exit "${_exit}"
  fi
  echo ">> Trader exited (${_exit}) — restarting in 3s (Gateway kept alive)"
  sleep 3
  python3 -m vtlive scheduler >> /app/runtime/vtlive.log 2>&1 &
  TRADER_PID=$!
done
