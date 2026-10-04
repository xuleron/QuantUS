#!/bin/bash
# IBKR 容器（默认 BROKER=ibkr_paper；.env 里设 VT_IBKR_BROKER=ibkr_live 切实盘）
exec "$(dirname "$0")/manage.sh" ibkr "$@"
