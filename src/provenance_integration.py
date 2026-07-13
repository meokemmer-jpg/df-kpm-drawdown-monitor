"""Provenance-backed drawdown monitor for df-kpm-drawdown-monitor."""
from __future__ import annotations

import csv
import fcntl
import hashlib
import hmac
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Optional

logger = logging.getLogger(__name__)

_HMAC_SECRET = os.environ.get("DF_KPMDD_HMAC_SECRET", "df-kpm-drawdown-monitor-dev-hmac-v1")
_TTL_S = int(os.environ.get("DF_KPMDD_ENVELOPE_TTL_S", "86400"))
DEFAULT_LOCK_PATH = Path(tempfile.gettempdir()) / "df-kpm-drawdown-monitor.lock.lockfile"


@dataclass(frozen=True)
class DrawdownResult:
    mission: str
    source_path: str
    threshold_pct: str
    observations: int
    peak_equity: str
    trough_equity: str
    max_drawdown_pct: str
    breached: bool
    status: str
    event_id: str

    def as_payload(self) -> dict[str, Any]:
        return {
            "mission": self.mission,
            "source_path": self.source_path,
            "threshold_pct": self.threshold_pct,
            "observations": self.observations,
            "peak_equity": self.peak_equity,
            "trough_equity": self.trough_equity,
            "max_drawdown_pct": self.max_drawdown_pct,
            "breached": self.breached,
            "status": self.status,
            "event_id": self.event_id,
        }


class AtomicFileLock:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fd: Optional[int] = None

    def __enter__(self) -> "AtomicFileLock":
        self._fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._fd is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _hmac_signature(payload_hash: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload_hash.encode("ascii"), hashlib.sha256).hexdigest()


def _quantize(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def read_equity_csv(path: Path | str) -> list[Decimal]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)

    values: list[Decimal] = []
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "equity" not in reader.fieldnames:
            raise ValueError("CSV must contain an 'equity' column")
        for row_number, row in enumerate(reader, start=2):
            raw = (row.get("equity") or "").strip()
            try:
                equity = Decimal(raw)
            except InvalidOperation as exc:
                raise ValueError(f"invalid equity at CSV line {row_number}: {raw!r}") from exc
            if equity <= 0:
                raise ValueError(f"equity must be positive at CSV line {row_number}")
            values.append(equity)

    if not values:
        raise ValueError("CSV contains no equity observations")
    return values


def compute_drawdown(equity_values: Iterable[Decimal], threshold_pct: Decimal) -> dict[str, Any]:
    values = list(equity_values)
    if not values:
        raise ValueError("at least one equity observation is required")
    if threshold_pct < 0:
        raise ValueError("threshold_pct must be non-negative")

    peak = values[0]
    trough_at_max = values[0]
    max_drawdown = Decimal("0")

    for equity in values:
        if equity > peak:
            peak = equity
        drawdown = ((peak - equity) / peak) * Decimal("100")
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            trough_at_max = equity

    breached = max_drawdown >= threshold_pct
    return {
        "observations": len(values),
        "peak_equity": _quantize(max(values)),
        "trough_equity": _quantize(trough_at_max),
        "max_drawdown_pct": _quantize(max_drawdown),
        "breached": breached,
        "status": "BREACH" if breached else "OK",
    }


class KPMDrawdownProvenanceRecorder:
    """Writes verifiable provenance envelopes and local timestamp anchors to disk."""

    def __init__(self, audit_dir: Path | str = "branch-hub/audit/df-kpm-drawdown-monitor/", k16_lock_path: Optional[Path] = None):
        self.audit_dir = Path(audit_dir)
        self.envelopes_dir = self.audit_dir / "provenance-full"
        self.anchors_dir = self.audit_dir / "anchors"
        self.envelopes_dir.mkdir(parents=True, exist_ok=True)
        self.anchors_dir.mkdir(parents=True, exist_ok=True)
        self._lock_path = Path(k16_lock_path) if k16_lock_path is not None else DEFAULT_LOCK_PATH

    def _read_predecessor_hash(self) -> Optional[str]:
        files = sorted(self.envelopes_dir.glob("*.envelope.json"), key=lambda p: p.stat().st_mtime_ns)
        if not files:
            return None
        try:
            with files[-1].open(encoding="utf-8") as handle:
                data = json.load(handle)
            return data.get("payload_hash")
        except (OSError, json.JSONDecodeError):
            logger.warning("could not read predecessor envelope", exc_info=True)
            return None

    def record_action(self, action_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        issued_at = datetime.now(timezone.utc).isoformat()
        payload_hash = _sha256_payload(payload)
        predecessor_hash = self._read_predecessor_hash()
        operation_id = f"df-kpm-drawdown-monitor-{issued_at.replace(':', '').replace('+', 'Z')}"
        envelope = {
            "operation_id": operation_id,
            "operation_type": action_type,
            "issuer": "df-kpm-drawdown-monitor",
            "issued_at_iso": issued_at,
            "ttl_seconds": _TTL_S,
            "payload": payload,
            "payload_hash": payload_hash,
            "chain_predecessor_hash": predecessor_hash,
            "signature": _hmac_signature(payload_hash, _HMAC_SECRET),
            "signature_alg": "hmac-sha256",
        }

        with AtomicFileLock(self._lock_path):
            envelope_path = self.envelopes_dir / f"{operation_id}.envelope.json"
            with envelope_path.open("w", encoding="utf-8") as handle:
                json.dump(envelope, handle, indent=2, sort_keys=True)
                handle.write("\n")

            anchor = {
                "anchor_type": "local-rfc3161-surrogate",
                "timestamp_iso": datetime.now(timezone.utc).isoformat(),
                "chain_hash": hashlib.sha256((payload_hash + issued_at).encode("ascii")).hexdigest(),
                "payload_hash": payload_hash,
                "source": "local-clock",
            }
            with (self.anchors_dir / "rfc3161-anchors.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(anchor, sort_keys=True) + "\n")

        return {"envelope": envelope, "anchor": anchor, "envelope_path": str(envelope_path)}


def monitor_drawdown(source_csv: Path | str, audit_dir: Path | str, threshold_pct: Decimal | str = Decimal("10"), lock_path: Optional[Path] = None) -> dict[str, Any]:
    threshold = Decimal(str(threshold_pct))
    source = Path(source_csv)
    equity_values = read_equity_csv(source)
    metrics = compute_drawdown(equity_values, threshold)
    payload = DrawdownResult(
        mission="df-kpm-drawdown-monitor",
        source_path=str(source.resolve()),
        threshold_pct=_quantize(threshold),
        observations=metrics["observations"],
        peak_equity=metrics["peak_equity"],
        trough_equity=metrics["trough_equity"],
        max_drawdown_pct=metrics["max_drawdown_pct"],
        breached=metrics["breached"],
        status=metrics["status"],
        event_id=hashlib.sha256(_canonical_json({"source": str(source.resolve()), "metrics": metrics})).hexdigest(),
    ).as_payload()
    provenance = KPMDrawdownProvenanceRecorder(audit_dir=audit_dir, k16_lock_path=lock_path).record_action("drawdown-monitor", payload)
    return {"payload": payload, "provenance": provenance}
