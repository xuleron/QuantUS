#!/bin/bash
# ============================================================================
# manage.sh <alpaca|ibkr> <command> — VT25_2x 交易容器管理
#   (通常通过 docker/alpaca.sh 或 docker/ibkr.sh 调用)
#
#   build     构建镜像
#   start     后台启动调度器（每个交易日收盘前 20 分钟计算信号并下 MOC 单）
#   stop      停止并删除容器
#   restart   重启
#   logs      跟踪日志
#   status    容器状态 + 账户/持仓/当前档位
#   check     连接检查：配置、行情、券商账户（不下单）
#   signal    打印今天的信号（不需要券商）
#   dryrun    立即跑一次交易任务但不下单（--force --dry-run）
#   pause     暂停交易（创建 STOP 文件，调度器继续运行）
#   resume    恢复交易
#   shell     进入容器
#   run ...   在一次性容器里执行任意 vtlive 子命令，例如: run trade --force --tif day
# ============================================================================
set -e

TAG="$1"; shift || true
CMD="${1:-help}"; shift || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE=(docker compose -f "$SCRIPT_DIR/docker-compose.yml")
ENV_FILE="$PROJECT_DIR/.env"

case "$TAG" in
  alpaca) DEFAULT_BROKER="alpaca_paper" ;;
  ibkr)   DEFAULT_BROKER="ibkr_paper" ;;
  *) echo "usage: $0 <alpaca|ibkr> <command>"; exit 1 ;;
esac

# Broker for this container: VT_ALPACA_BROKER / VT_IBKR_BROKER from .env, else default.
if [ -f "$ENV_FILE" ]; then
  VAR="VT_$(echo "$TAG" | tr a-z A-Z)_BROKER"
  VAL=$(grep -E "^${VAR}=" "$ENV_FILE" | tail -1 | cut -d= -f2- | tr -d '"' | awk '{print $1}')
fi
export VT_TAG="$TAG"
export VT_BROKER="${VAL:-$DEFAULT_BROKER}"
export HOST_UID="$(id -u)" HOST_GID="$(id -g)"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }

check_env() {
  if [ ! -f "$ENV_FILE" ]; then
    cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
    warn ".env 不存在，已从 .env.example 复制，请先编辑: $ENV_FILE"
    exit 1
  fi
  mkdir -p "$PROJECT_DIR/runtime"
}

oneoff() { "${COMPOSE[@]}" run --rm --no-deps trader "$@"; }

cd "$PROJECT_DIR"
case "$CMD" in
  build)   check_env; "${COMPOSE[@]}" build ;;
  start)   check_env
           if [ "$TAG" = "ibkr" ]; then
             info "启动 vt25-ibkr (集成 IB Gateway on localhost:4001)..."
           fi
           "${COMPOSE[@]}" up -d trader
           info "已启动 vt25-$TAG (BROKER=$VT_BROKER)。日志: $0 logs" ;;
  stop)    "${COMPOSE[@]}" down ;;
  restart) check_env; "${COMPOSE[@]}" up -d --force-recreate trader ;;
  logs)    "${COMPOSE[@]}" logs -f --tail 200 trader ;;
  status)  docker ps --filter "name=vt25-$TAG" --format 'table {{.Names}}\t{{.Status}}'
           check_env; oneoff status ;;
  check)   check_env; oneoff check ;;
  signal)  check_env; oneoff signal ;;
  dryrun)  check_env; oneoff trade --force --dry-run ;;
  pause)   check_env; oneoff stop ;;
  resume)  check_env; oneoff resume ;;
  shell)   docker exec -it "vt25-$TAG" /bin/bash ;;
  run)     check_env; oneoff "$@" ;;
  *)       sed -n '2,20p' "$0" ;;
esac
