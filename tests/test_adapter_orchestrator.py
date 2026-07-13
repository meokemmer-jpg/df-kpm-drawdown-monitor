from pathlib import Path
import csv
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from provenance_integration import monitor_drawdown


def _write_equity_csv(path: Path, values: list[int]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["day", "equity"])
        writer.writeheader()
        for idx, value in enumerate(values, start=1):
            writer.writerow({"day": idx, "equity": value})


def test_adapter_orchestrator_discriminates_adversarial_drawdown_input(tmp_path):
    benign_csv = tmp_path / "benign_equity.csv"
    adversarial_csv = tmp_path / "adversarial_equity.csv"
    audit_dir = tmp_path / "audit"
    lock_path = tmp_path / "monitor.lock"

    _write_equity_csv(benign_csv, [1000, 1010, 1025, 1040])
    _write_equity_csv(adversarial_csv, [1000, 980, 900, 870])

    benign = monitor_drawdown(benign_csv, audit_dir=audit_dir, threshold_pct="10", lock_path=lock_path)
    adversarial = monitor_drawdown(adversarial_csv, audit_dir=audit_dir, threshold_pct="10", lock_path=lock_path)

    benign_payload = benign["payload"]
    adversarial_payload = adversarial["payload"]

    assert benign_payload["mission"] == "df-kpm-drawdown-monitor"
    assert adversarial_payload["mission"] == "df-kpm-drawdown-monitor"

    assert benign_payload["status"] == "OK"
    assert benign_payload["breached"] is False
    assert benign_payload["max_drawdown_pct"] == "0.0000"

    assert adversarial_payload["status"] == "BREACH"
    assert adversarial_payload["breached"] is True
    assert adversarial_payload["max_drawdown_pct"] == "13.0000"

    assert benign_payload["status"] != adversarial_payload["status"]
    assert benign_payload["max_drawdown_pct"] != adversarial_payload["max_drawdown_pct"]
    assert benign["provenance"]["envelope"]["payload_hash"] != adversarial["provenance"]["envelope"]["payload_hash"]
    assert benign["provenance"]["envelope"]["signature"] != adversarial["provenance"]["envelope"]["signature"]

    envelope_files = sorted((audit_dir / "provenance-full").glob("*.envelope.json"))
    assert len(envelope_files) == 2
    persisted = [json.loads(path.read_text(encoding="utf-8")) for path in envelope_files]
    assert {item["payload"]["status"] for item in persisted} == {"OK", "BREACH"}

    anchors = (audit_dir / "anchors" / "rfc3161-anchors.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(anchors) == 2
    assert all(json.loads(line)["payload_hash"] for line in anchors)
