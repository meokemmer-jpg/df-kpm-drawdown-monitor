#!/bin/bash
# DF-KPM-Drawdown-Monitor Wrapper [CRUX-MK] - K16 Mutex
set -e

LOCK_DIR="/tmp/df-kpm-drawdown-monitor.lock"
LOCK_AGE_LIMIT_S=21600

if [ -d "$LOCK_DIR" ]; then
  LOCK_AGE_S=$(( $(date +%s) - $(stat -f %m "$LOCK_DIR" 2>/dev/null || echo 0) ))
  if [ "$LOCK_AGE_S" -gt "$LOCK_AGE_LIMIT_S" ]; then
    rm -rf "$LOCK_DIR"
  fi
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  exit 3
fi

echo "$$" > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT INT TERM

cd /Users/make/Projects/dark-factories/df-kpm-drawdown-monitor

if /usr/bin/python3 -m src.adapter_orchestrator; then
  exit 0
else
  RC=$?
  [ "$RC" = "2" ] && exit 0
  exit 0  # K_0-Schutz: status=partial -> exit 0
fi
