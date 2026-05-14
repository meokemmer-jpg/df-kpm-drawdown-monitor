"""Tests for df-kpm-drawdown-monitor provenance_integration [CRUX-MK]."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import provenance_integration as pi

def test_module_imports():
    assert hasattr(pi, "KPMDrawdownProvenanceRecorder")

def test_recorder_instantiable(tmp_path):
    r = pi.KPMDrawdownProvenanceRecorder(audit_dir=tmp_path)
    assert r.audit_dir.exists()
    assert r.envelopes_dir.exists()
    assert r.anchors_dir.exists()

def test_predecessor_hash_empty(tmp_path):
    r = pi.KPMDrawdownProvenanceRecorder(audit_dir=tmp_path)
    assert r._read_predecessor_hash() is None
