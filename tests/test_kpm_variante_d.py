"""Tests fuer KPM-Variante-D (Drawdown-Monitor) [CRUX-MK]."""

from decimal import Decimal
import pytest

from src.kpm_variante_d_helpers import (
    TradingContext,
    DrawdownState,
    kelly_fraction_for_context,
    drawdown_cap_check,
    hive_leverage_gate,
    position_reduction_factor,
)


def test_kelly_fraction_full_matrix():
    assert kelly_fraction_for_context(TradingContext.NORMALREGIME_HIGH_CONFIDENCE) == Decimal("0.40")
    assert kelly_fraction_for_context(TradingContext.WITHDRAWAL_PHASE) == Decimal("0.20")


def test_drawdown_cap_thresholds_strict():
    assert drawdown_cap_check(Decimal("14.99")) == DrawdownState.NORMAL
    assert drawdown_cap_check(Decimal("15")) == DrawdownState.SOFT_BRAKE
    assert drawdown_cap_check(Decimal("19.99")) == DrawdownState.SOFT_BRAKE
    assert drawdown_cap_check(Decimal("20")) == DrawdownState.HARD_CAP
    assert drawdown_cap_check(Decimal("24.99")) == DrawdownState.HARD_CAP
    assert drawdown_cap_check(Decimal("25")) == DrawdownState.ABSOLUTE_NO_GO


def test_hive_leverage_gate_invalid():
    with pytest.raises(ValueError):
        hive_leverage_gate(Decimal("1.5"))
    with pytest.raises(ValueError):
        hive_leverage_gate(Decimal("-0.1"))


def test_position_reduction_per_state():
    assert position_reduction_factor(DrawdownState.NORMAL) == Decimal("1.0")
    assert position_reduction_factor(DrawdownState.SOFT_BRAKE) == Decimal("0.5")
    assert position_reduction_factor(DrawdownState.HARD_CAP) == Decimal("0.0")
    assert position_reduction_factor(DrawdownState.ABSOLUTE_NO_GO) == Decimal("0.0")
