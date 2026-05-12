"""DF-KPM-Drawdown-Monitor Core-Logic [CRUX-MK].

Variante-D-Compliance-Monitor.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from .kpm_variante_d_helpers import (
    DrawdownState,
    drawdown_cap_check,
    hive_leverage_gate,
)


class AlertSeverity(Enum):
    """Alert-Severity per Variante-D."""
    INFO = "info"             # NORMAL state
    WARN = "warn"             # SOFT_BRAKE
    CRITICAL = "critical"     # HARD_CAP (Phronesis)
    EMERGENCY = "emergency"   # ABSOLUTE_NO_GO (Familien-Notfall)


@dataclass(frozen=True)
class DrawdownSnapshot:
    """Drawdown-Snapshot mit NAV-Historie."""
    snapshot_id: str
    timestamp: str
    current_nav_eur: Decimal
    peak_nav_eur: Decimal  # All-time-high
    drawdown_pct: Decimal  # (peak - current) / peak * 100
    source: str
    phronesis_ticket: Optional[str] = None

    def __post_init__(self):
        if self.source == "real-api" and not self.phronesis_ticket:
            raise ValueError("Real-API requires phronesis_ticket")
        if self.peak_nav_eur < self.current_nav_eur:
            raise ValueError(f"peak_nav ({self.peak_nav_eur}) must be >= current_nav ({self.current_nav_eur})")
        if self.drawdown_pct < Decimal("0"):
            raise ValueError(f"drawdown_pct must be >=0, got {self.drawdown_pct}")


@dataclass(frozen=True)
class DrawdownAlert:
    """Alert-Output bei Cap-Trigger."""
    alert_id: str
    timestamp: str
    severity: AlertSeverity
    drawdown_state: DrawdownState
    drawdown_pct: Decimal
    hive_score: Decimal
    hive_decision: str  # "leverage_ok" | "no_leverage_increase" | "auto_deleverage"
    required_action: str
    family_emergency_protocol: bool  # True bei ABSOLUTE_NO_GO


def _severity_for_state(state: DrawdownState) -> AlertSeverity:
    """Maps DrawdownState zu AlertSeverity."""
    if state == DrawdownState.NORMAL:
        return AlertSeverity.INFO
    if state == DrawdownState.SOFT_BRAKE:
        return AlertSeverity.WARN
    if state == DrawdownState.HARD_CAP:
        return AlertSeverity.CRITICAL
    if state == DrawdownState.ABSOLUTE_NO_GO:
        return AlertSeverity.EMERGENCY
    raise ValueError(f"Unknown state: {state}")


def _required_action_for_state(state: DrawdownState) -> str:
    """Returns required action string per state."""
    if state == DrawdownState.NORMAL:
        return "Keine Aktion noetig"
    if state == DrawdownState.SOFT_BRAKE:
        return "Position-Reduktion 50% + Wochen-Review-Pflicht"
    if state == DrawdownState.HARD_CAP:
        return "Trading-Pause SOFORT + Martin-Phronesis-Gate (Decision-Card pflicht)"
    if state == DrawdownState.ABSOLUTE_NO_GO:
        return "FAMILIEN-NOTFALL-PROTOKOLL: Harter Stop + Familien-Konferenz + Notfall-Liquiditaet pruefen"
    raise ValueError(f"Unknown state: {state}")


def compute_drawdown_alert(
    drawdown_pct: Decimal,
    hive_score: Decimal,
) -> DrawdownAlert:
    """Berechnet Drawdown-Alert mit Variante-D-Logic + HIVE-Gate.

    Args:
        drawdown_pct: Aktueller Drawdown (z.B. 17.5 fuer 17.5%)
        hive_score: HIVE-Score (0-1)

    Returns:
        DrawdownAlert mit Severity + Required-Action
    """
    state = drawdown_cap_check(drawdown_pct)
    severity = _severity_for_state(state)
    hive_decision = hive_leverage_gate(hive_score)
    action = _required_action_for_state(state)
    family_emergency = (state == DrawdownState.ABSOLUTE_NO_GO)

    return DrawdownAlert(
        alert_id=f"alert-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        severity=severity,
        drawdown_state=state,
        drawdown_pct=drawdown_pct,
        hive_score=hive_score,
        hive_decision=hive_decision,
        required_action=action,
        family_emergency_protocol=family_emergency,
    )


def calculate_drawdown_pct(current_nav: Decimal, peak_nav: Decimal) -> Decimal:
    """Drawdown = (peak - current) / peak * 100."""
    if peak_nav <= Decimal("0"):
        raise ValueError(f"peak_nav must be > 0, got {peak_nav}")
    if current_nav < Decimal("0"):
        raise ValueError(f"current_nav must be >=0, got {current_nav}")
    return ((peak_nav - current_nav) / peak_nav) * Decimal("100")


def get_default_mode() -> str:
    """Returns 'mock' (default) or 'real-api'."""
    if os.environ.get("DF_KPM_DRAWDOWN_REAL_ENABLED") == "true":
        return "real-api"
    return "mock"
