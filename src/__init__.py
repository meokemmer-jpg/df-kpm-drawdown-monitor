"""DF-KPM-Drawdown-Monitor [CRUX-MK]. Lazy-Imports."""

__version__ = "0.1.0-PHASE-1"


def __getattr__(name):
    if name == "DrawdownSnapshot":
        from .drawdown_monitor_main import DrawdownSnapshot
        return DrawdownSnapshot
    if name == "DrawdownAlert":
        from .drawdown_monitor_main import DrawdownAlert
        return DrawdownAlert
    if name == "compute_drawdown_alert":
        from .drawdown_monitor_main import compute_drawdown_alert
        return compute_drawdown_alert
    raise AttributeError(f"module {__name__} has no attribute {name}")
