"""Tests fuer DF-KPM-Drawdown-Monitor [CRUX-MK]."""

from __future__ import annotations
from decimal import Decimal
import pytest

from src.drawdown_monitor_main import (
    AlertSeverity,
    DrawdownSnapshot,
    DrawdownAlert,
    compute_drawdown_alert,
    calculate_drawdown_pct,
    get_default_mode,
)
from src.kpm_variante_d_helpers import DrawdownState


def test_drawdown_snapshot_real_api_phronesis():
    """Real-API requires phronesis_ticket."""
    with pytest.raises(ValueError, match="phronesis_ticket"):
        DrawdownSnapshot(
            snapshot_id="test",
            timestamp="2026-05-11T10:00:00+00:00",
            current_nav_eur=Decimal("900000"),
            peak_nav_eur=Decimal("1000000"),
            drawdown_pct=Decimal("10"),
            source="real-api",
        )


def test_drawdown_snapshot_peak_must_be_geq_current():
    """peak_nav muss >= current_nav sein."""
    with pytest.raises(ValueError, match="peak_nav"):
        DrawdownSnapshot(
            snapshot_id="test",
            timestamp="2026-05-11T10:00:00+00:00",
            current_nav_eur=Decimal("1000000"),
            peak_nav_eur=Decimal("900000"),  # invalid
            drawdown_pct=Decimal("0"),
            source="mock",
        )


def test_calculate_drawdown_pct():
    """Drawdown = (peak - current) / peak * 100."""
    dd = calculate_drawdown_pct(
        current_nav=Decimal("850000"),
        peak_nav=Decimal("1000000"),
    )
    assert dd == Decimal("15.00")


def test_calculate_drawdown_pct_invalid_peak():
    """peak_nav <= 0 -> Error."""
    with pytest.raises(ValueError, match="peak_nav"):
        calculate_drawdown_pct(Decimal("100"), Decimal("0"))


def test_compute_alert_normal_state():
    """Drawdown 8% + HIVE 0.75 -> INFO/leverage_ok."""
    alert = compute_drawdown_alert(Decimal("8"), Decimal("0.75"))
    assert alert.severity == AlertSeverity.INFO
    assert alert.drawdown_state == DrawdownState.NORMAL
    assert alert.hive_decision == "leverage_ok"
    assert alert.family_emergency_protocol is False


def test_compute_alert_soft_brake():
    """Drawdown 16% -> WARN/SOFT_BRAKE."""
    alert = compute_drawdown_alert(Decimal("16"), Decimal("0.6"))
    assert alert.severity == AlertSeverity.WARN
    assert alert.drawdown_state == DrawdownState.SOFT_BRAKE
    assert alert.hive_decision == "no_leverage_increase"


def test_compute_alert_hard_cap():
    """Drawdown 22% -> CRITICAL/HARD_CAP."""
    alert = compute_drawdown_alert(Decimal("22"), Decimal("0.4"))
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.drawdown_state == DrawdownState.HARD_CAP
    assert alert.hive_decision == "auto_deleverage"
    assert "Phronesis" in alert.required_action


def test_compute_alert_emergency():
    """Drawdown 26% -> EMERGENCY + family-emergency."""
    alert = compute_drawdown_alert(Decimal("26"), Decimal("0.3"))
    assert alert.severity == AlertSeverity.EMERGENCY
    assert alert.drawdown_state == DrawdownState.ABSOLUTE_NO_GO
    assert alert.family_emergency_protocol is True
    assert "FAMILIEN-NOTFALL" in alert.required_action


def test_get_default_mode_sandbox(monkeypatch):
    monkeypatch.delenv("DF_KPM_DRAWDOWN_REAL_ENABLED", raising=False)
    assert get_default_mode() == "mock"


def test_get_default_mode_real_strict(monkeypatch):
    monkeypatch.setenv("DF_KPM_DRAWDOWN_REAL_ENABLED", "1")
    assert get_default_mode() == "mock"
    monkeypatch.setenv("DF_KPM_DRAWDOWN_REAL_ENABLED", "true")
    assert get_default_mode() == "real-api"
