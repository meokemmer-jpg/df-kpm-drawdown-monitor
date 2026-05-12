"""DF-KPM-Drawdown-Monitor LaunchAgent-Entry [CRUX-MK]."""

from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

from .drawdown_monitor_main import (
    compute_drawdown_alert,
    get_default_mode,
)
from .audit_logger import log_audit_event


def main(argv: list[str] | None = None) -> int:
    stop_flag = Path("/tmp/df-kpm-drawdown-monitor.stop")
    if stop_flag.exists():
        print(f"STOP.flag detected", file=sys.stderr)
        return 2

    mode = get_default_mode()
    if mode == "real-api" and not os.environ.get("PHRONESIS_TICKET"):
        print("Real-API requires PHRONESIS_TICKET", file=sys.stderr)
        log_audit_event(
            event="real_mode_rejected_no_phronesis",
            df_id="df-kpm-drawdown-monitor",
            details={"reason": "PHRONESIS_TICKET missing"},
        )
        return 1

    # Mock-Default: simulate normal-state
    alert = compute_drawdown_alert(
        drawdown_pct=Decimal("8"),
        hive_score=Decimal("0.75"),
    )

    log_audit_event(
        event="drawdown_alert_computed",
        df_id="df-kpm-drawdown-monitor",
        details={
            "alert_id": alert.alert_id,
            "severity": alert.severity.value,
            "drawdown_state": alert.drawdown_state.value,
            "drawdown_pct": str(alert.drawdown_pct),
            "hive_score": str(alert.hive_score),
            "hive_decision": alert.hive_decision,
            "family_emergency_protocol": alert.family_emergency_protocol,
        },
    )

    health_data = {
        "status": "ok",
        "timestamp": alert.timestamp,
        "drawdown_state": alert.drawdown_state.value,
        "severity": alert.severity.value,
    }
    health_path = Path("/tmp/df-kpm-drawdown-monitor-health.json")
    try:
        health_path.write_text(json.dumps(health_data, indent=2))
    except Exception as e:
        print(f"Could not write health: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
