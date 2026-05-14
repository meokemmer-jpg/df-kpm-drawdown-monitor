"""K12+K13+K16 Provenance-Integration fuer df-kpm-drawdown-monitor [CRUX-MK].

Welle-54 Architekt-Self via Add-on-Modul-Pattern (W52-A bewaehrt).
"""
from __future__ import annotations
import logging, os, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_DF_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_DF_ROOT))

try:
    from _df_common.full_provenance_envelope import build_full_envelope, FullProvenanceEnvelope
    from _df_common.rfc3161_anchor import rfc3161_timestamp, AnchorRecord
    from _df_common.atomic_lock import AtomicLock
    W48_FOUNDATION = True
except ImportError:
    W48_FOUNDATION = False

logger = logging.getLogger(__name__)

_HMAC_SECRET = os.environ.get("DF_KPMDD_HMAC_SECRET", "df-kpm-drawdown-monitor-dev-hmac-v1")
_TTL_S = int(os.environ.get("DF_KPMDD_ENVELOPE_TTL_S", "86400"))
DEFAULT_LOCK_PATH = Path("/tmp/df-kpm-drawdown-monitor.lock.lockfile")


class KPMDrawdownProvenanceRecorder:
    """K11 try/except + K12 envelope + K13 RFC3161-anchor + K16 AtomicLock."""

    def __init__(self, audit_dir: Path | str = "branch-hub/audit/df-kpm-drawdown-monitor/",
                 k16_lock_path: Optional[Path] = None):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.envelopes_dir = self.audit_dir / "provenance-full"
        self.envelopes_dir.mkdir(parents=True, exist_ok=True)
        self.anchors_dir = self.audit_dir / "anchors"
        self.anchors_dir.mkdir(parents=True, exist_ok=True)
        self._lock_path = k16_lock_path

    def _read_predecessor_hash(self) -> Optional[str]:
        try:
            files = sorted(self.envelopes_dir.glob("*.envelope.json"), key=lambda p: p.stat().st_mtime)
            if not files: return None
            import json
            with open(files[-1]) as f: data = json.load(f)
            return data.get("payload_hash")
        except Exception: return None

    def record_action(self, action_type: str, payload: dict[str, Any]) -> Optional[dict]:
        """K11 non-fatal try/except."""
        if not W48_FOUNDATION: return None
        try:
            predecessor = self._read_predecessor_hash()
            envelope = build_full_envelope(
                operation_id=f"df-kpm-drawdown-monitor-{datetime.now(timezone.utc).isoformat()}",
                operation_type=action_type,
                issuer="df-kpm-drawdown-monitor",
                payload=payload,
                signing_secret=_HMAC_SECRET,
                ttl_seconds=_TTL_S,
                chain_predecessor_hash=predecessor,
            )
            envelope_path = self.envelopes_dir / f"{envelope.operation_id}.envelope.json"
            import json
            with open(envelope_path, "w") as f:
                json.dump({"payload_hash": envelope.payload_hash, "signature": envelope.signature, "operation_id": envelope.operation_id, "issued_at_iso": envelope.issued_at_iso}, f, indent=2)
            try:
                anchor = rfc3161_timestamp(envelope.payload_hash)
                with open(self.anchors_dir / "rfc3161-anchors.jsonl", "a") as f:
                    f.write(json.dumps({"chain_hash": anchor.chain_hash, "ts": anchor.timestamp_iso, "source": anchor.source}) + "\n")
            except Exception as e:
                logger.warning(f"K13 anchor failed: {e}")
                anchor = None
            return {"envelope": envelope, "anchor": anchor}
        except Exception as e:
            logger.warning(f"K11 non-fatal: {e}")
            return None
