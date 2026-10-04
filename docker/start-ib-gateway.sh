#!/bin/bash
# Start IB Gateway in this container
# Mirrors gnzsnz/ib-gateway startup but integrated into trader container

set -e

export DISPLAY=:1
export TZ=America/New_York

# Start virtual X server for IB Gateway GUI (headless)
Xvfb $DISPLAY -screen 0 1024x768x16 > /dev/null 2>&1 &
XVFB_PID=$!
sleep 1

# Ensure IB Gateway can write to its config directories
mkdir -p /home/ibgateway/ibc
mkdir -p /home/ibgateway/Jts

# Start IB Gateway
cd /home/ibgateway
exec java \
  -Xmx512m \
  -Dcom.sun.jndi.ldap.connect.pool=false \
  -Dcom.ibm.jsse2.overrideDefaultTLS=true \
  -Dsun.awt.nopixfmt=true \
  -Dsun.java2d.noddraw=true \
  -Dsun.java2d.opengl=false \
  -Dsun.awt.useinternalframe=true \
  -Dprop.tws_disable_ssl_verification=true \
  -cp "/home/ibgateway/*" \
  com.ib.gateway.GatewayStart \
  --username="${IBKR_USERNAME}" \
  --password="${IBKR_PASSWORD}" \
  --trading-mode="${IBKR_TRADING_MODE:-paper}" \
  --ibgateway-location="/home/ibgateway"
