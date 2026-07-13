#!/usr/bin/env python3
"""
test_ideabrowser.py — Eval suite for the ideabrowser skill.

Covers:
1. Add idea — creates entry with UUID and pending status
2. List ideas — returns filtered list
3. Search — matches text and tags
4. Promote — changes status to promoted and exports spec file
5. Reject — changes status to rejected
6. Defer — changes status to deferred
7. Stats — returns counts by status
8. Empty registry — handles missing registry file gracefully
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "skills" / "ideabrowser" / "scripts" / "ideabrowser.py"


def run_script(args, registry_path=None):
    """Run ideabrowser.py with given args, return (exit_code, stdout_json, stderr)."""
    cmd = [sys.executable, str(SCRIPT), "--action", args[0]]
    if registry_path:
        cmd.extend(["--registry", registry_path])
    cmd.extend(args[1:])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        stdout_json = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        stdout_json = {"_raw": result.stdout}
    return result.returncode, stdout_json, result.stderr


def fresh_registry():
    """Create a fresh temporary registry file. Returns (path, cleanup_fn)."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.write(fd, b'{"ideas": []}')
    os.close(fd)
    return path, lambda: os.unlink(path)


def test_add_idea():
    """Test 1: Add idea creates entry with UUID and pending status."""
    reg, cleanup = fresh_registry()
    try:
        rc, data, _ = run_script(["add", "--text", "Test idea"], reg)
        assert rc == 0
        assert data["action"] == "add"
        assert "id" in data["idea"]
        assert data["idea"]["status"] == "pending"
        assert data["idea"]["text"] == "Test idea"
        assert len(data["idea"]["id"]) > 0  # UUID is non-empty
    finally:
        cleanup()


def test_list_ideas():
    """Test 2: List returns filtered list."""
    reg, cleanup = fresh_registry()
    try:
        run_script(["add", "--text", "Idea one"], reg)
        run_script(["add", "--text", "Idea two"], reg)
        rc, data, _ = run_script(["list", "--status", "pending"], reg)
        assert rc == 0
        assert data["count"] == 2
        assert len(data["ideas"]) == 2
    finally:
        cleanup()


def test_search():
    """Test 3: Search matches text."""
    reg, cleanup = fresh_registry()
    try:
        run_script(["add", "--text", "Build a genealogy app"], reg)
        run_script(["add", "--text", "Make a weather dashboard"], reg)
        rc, data, _ = run_script(["search", "--query", "genealogy"], reg)
        assert rc == 0
        assert data["count"] == 1
        assert "genealogy" in data["ideas"][0]["text"].lower()
    finally:
        cleanup()


def test_promote():
    """Test 4: Promote changes status to promoted."""
    reg, cleanup = fresh_registry()
    try:
        _, add_data, _ = run_script(["add", "--text", "Promote me"], reg)
        idea_id = add_data["idea"]["id"]
        export_file = tempfile.mktemp(suffix=".md")
        rc, data, _ = run_script(["promote", "--id", idea_id, "--export-file", export_file], reg)
        assert rc == 0
        assert data["action"] == "promote"
        assert data["idea"]["status"] == "promoted"
        assert os.path.exists(export_file)
    finally:
        cleanup()


def test_reject():
    """Test 5: Reject changes status to rejected."""
    reg, cleanup = fresh_registry()
    try:
        _, add_data, _ = run_script(["add", "--text", "Reject me"], reg)
        idea_id = add_data["idea"]["id"]
        rc, data, _ = run_script(["reject", "--id", idea_id], reg)
        assert rc == 0
        assert data["idea"]["status"] == "rejected"
    finally:
        cleanup()


def test_defer():
    """Test 6: Defer changes status to deferred."""
    reg, cleanup = fresh_registry()
    try:
        _, add_data, _ = run_script(["add", "--text", "Defer me"], reg)
        idea_id = add_data["idea"]["id"]
        rc, data, _ = run_script(["defer", "--id", idea_id], reg)
        assert rc == 0
        assert data["idea"]["status"] == "deferred"
    finally:
        cleanup()


def test_stats():
    """Test 7: Stats returns counts by status."""
    reg, cleanup = fresh_registry()
    try:
        run_script(["add", "--text", "A"], reg)
        run_script(["add", "--text", "B"], reg)
        _, data, _ = run_script(["add", "--text", "C"], reg)
        run_script(["reject", "--id", data["idea"]["id"]], reg)
        rc, stats_data, _ = run_script(["stats"], reg)
        assert rc == 0
        assert stats_data["total"] == 3
        assert stats_data["by_status"]["pending"] == 2
        assert stats_data["by_status"]["rejected"] == 1
    finally:
        cleanup()


def test_empty_registry():
    """Test 8: Handles missing registry file gracefully."""
    missing_path = tempfile.mktemp(suffix=".json")
    # Don't create the file
    rc, data, _ = run_script(["stats"], missing_path)
    assert rc == 0
    assert data["total"] == 0
    # Clean up if it was created
    if os.path.exists(missing_path):
        os.unlink(missing_path)


if __name__ == "__main__":
    tests = [
        test_add_idea,
        test_list_ideas,
        test_search,
        test_promote,
        test_reject,
        test_defer,
        test_stats,
        test_empty_registry,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed + failed} tests passed")
    if failed:
        sys.exit(1)