from __future__ import annotations

import tomllib
from pathlib import Path

import audit_estate_layout as audit
import vendor_estate

REVISION = "a" * 40

MANIFEST = """\
version = 1

[repository]
id = "larsbx/consumer"

[governance]
repository = "stale"
revision = "stale"

[governance.sha256]
"x" = "y"

[[plane]]
id = "kernel"
"""


def test_pin_replaces_governance_and_keeps_everything_else():
    data = tomllib.loads(vendor_estate.pin(MANIFEST, REVISION, {"f": "d"}))
    assert data["governance"] == {
        "repository": audit.GOVERNANCE_REPOSITORY,
        "revision": REVISION,
        "sha256": {"f": "d"},
    }
    assert data["repository"] == {"id": "larsbx/consumer"}
    assert data["plane"] == [{"id": "kernel"}]


def test_pin_is_idempotent():
    once = vendor_estate.pin(MANIFEST, REVISION, {"f": "d"})
    assert vendor_estate.pin(once, REVISION, {"f": "d"}) == once


def test_vendor_then_check_round_trips(tmp_path: Path):
    (tmp_path / "estate.toml").write_text(MANIFEST, encoding="utf-8")
    assert set(vendor_estate.drift(tmp_path)) == set(audit.VENDORED)

    vendor_estate.vendor(tmp_path, REVISION)
    assert vendor_estate.drift(tmp_path) == []
    pinned = tomllib.loads((tmp_path / "estate.toml").read_text(encoding="utf-8"))["governance"]
    assert set(pinned["sha256"]) == set(audit.VENDORED)

    (tmp_path / "tools/audit_estate_layout.py").write_text("# drift\n", encoding="utf-8")
    assert vendor_estate.drift(tmp_path) == ["tools/audit_estate_layout.py"]
    assert vendor_estate.main([str(tmp_path), "--check"]) == 1
