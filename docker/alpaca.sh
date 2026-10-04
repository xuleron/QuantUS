#!/bin/bash
# Alpaca 容器（默认 BROKER=alpaca_paper；.env 里设 VT_ALPACA_BROKER=alpaca_live 切实盘）
exec "$(dirname "$0")/manage.sh" alpaca "$@"
