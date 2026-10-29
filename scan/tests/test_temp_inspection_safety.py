"""Pre-scan housekeeping must never delete folders discovered by name alone."""
import os
import sys
import time
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zbtriage import localpaths, report, workflow
from test_followup_fixes import bundle


@pytest.fixture(params=("source", "bundle"))
def api(request, bundle):
    if request.param == "bundle":
        return bundle
    return types.SimpleNamespace(
        find_stale_temp=localpaths.find_stale_temp,
        workflow_before_scan=workflow.workflow_before_scan,
        _housekeeping_block=report._housekeeping_block)


def test_old_unrelated_and_active_folders_survive(tmp_path, api):
    old = time.time() - 2 * localpaths.STALE_TEMP_AGE
    unrelated = tmp_path / "bscan_unrelated"
    active = tmp_path / "zbt_ios_active"
    for folder in (unrelated, active):
        folder.mkdir()
        (folder / "copy.db").write_bytes(b"must survive")
        os.utime(str(folder), (old, old))
    # A directory's mtime does not change as an existing file is being used.
    with (active / "copy.db").open("rb") as opened:
        result = api.find_stale_temp(base=str(tmp_path))
        assert opened.read() == b"must survive"
    assert result["removed"] == 0
    assert result["failed"] == []
    assert set(result["retained"]) == {str(unrelated), str(active)}
    for folder in (unrelated, active):
        assert (folder / "copy.db").read_bytes() == b"must survive"


def test_links_are_not_inspected(tmp_path, api):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "private.txt").write_bytes(b"keep")
    link = tmp_path / "bscan_link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")
    assert api.find_stale_temp(base=str(tmp_path))["retained"] == []
    assert api.find_stale_temp(base=str(link))["retained"] == []
    assert (outside / "private.txt").read_bytes() == b"keep"


def test_housekeeping_notice_is_safe_and_does_not_claim_ownership(api, monkeypatch, capsys):
    status = {"removed": 0, "failed": [], "retained": ["/tmp/bscan_\x1b[2Jold\nforged"]}
    globals_ = api.workflow_before_scan.__globals__
    monkeypatch.setitem(globals_, "find_stale_temp", lambda: status)
    iocs = types.SimpleNamespace()
    api.workflow_before_scan(types.SimpleNamespace(), iocs)
    message = capsys.readouterr().err
    assert "\x1b" not in message
    assert len(message.splitlines()) == 1
    assert "not deleted" in message
    assert "no scan is running" in message
    assert api._housekeeping_block(iocs.housekeeping)["stale_temp_retained"] == [
        "/tmp/bscan_\ufffd[2Jold\nforged"]
