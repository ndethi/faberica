#!/usr/bin/env python3
"""
test_pm_spec_creator.py — Eval suite for the pm-spec-creator skill.

Covers:
1. Spec parsing — extracts correct number of units from a fixture spec
2. Label mapping — units get correct labels
3. Dry-run mode — produces JSON summary without GitHub side effects
4. Project name fallback — defaults to repo name when not specified
5. Column defaults — uses standard columns when not overridden
6. Edge case — empty spec file returns zero units
7. Issue title format — [<SECTION>] <first line of unit text>
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "skills" / "pm-spec-creator" / "scripts" / "pm_spec_creator.py"

FIXTURE_SPEC = """\
# Test Project Spec

## LOGIC
1. First feature item with some detail.
2. Second feature item with more detail.

## OUTPUTS
- output1.js
- output2.json

## EDGE CASES
- Edge case one
- Edge case two

## OUT OF SCOPE
- Out of scope item

## ASSUMPTIONS
- Assumption one
"""

EMPTY_SPEC = ""

def run_script(args):
    """Run pm_spec_creator.py with given args, return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr

def test_spec_parsing():
    """Test 1: Correct number of units extracted from fixture spec."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(FIXTURE_SPEC)
        spec_file = f.name
    try:
        rc, stdout, stderr = run_script([
            "--spec-file", spec_file,
            "--repo", "test/repo",
            "--dry-run",
        ])
        assert rc == 0, f"Exit code {rc}: {stderr}"
        data = json.loads(stdout)
        # 2 LOGIC + 2 OUTPUTS + 2 EDGE CASES + 1 OUT OF SCOPE + 1 ASSUMPTIONS = 8
        assert data["units_extracted"] == 8, f"Expected 8 units, got {data['units_extracted']}"
    finally:
        os.unlink(spec_file)

def test_label_mapping():
    """Test 2: Units get correct labels."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(FIXTURE_SPEC)
        spec_file = f.name
    try:
        rc, stdout, _ = run_script([
            "--spec-file", spec_file,
            "--repo", "test/repo",
            "--dry-run",
        ])
        data = json.loads(stdout)
        labels = {u["label"] for u in data["units"]}
        assert "feature" in labels, "Missing 'feature' label"
        assert "deliverable" in labels, "Missing 'deliverable' label"
        assert "edge-case" in labels, "Missing 'edge-case' label"
        assert "out-of-scope" in labels, "Missing 'out-of-scope' label"
    finally:
        os.unlink(spec_file)

def test_dry_run_no_side_effects():
    """Test 3: Dry-run produces JSON summary without GitHub side effects."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(FIXTURE_SPEC)
        spec_file = f.name
    try:
        rc, stdout, _ = run_script([
            "--spec-file", spec_file,
            "--repo", "test/repo",
            "--dry-run",
        ])
        assert rc == 0
        data = json.loads(stdout)
        assert data["dry_run"] is True
        assert "project_url" not in data, "project_url should not exist in dry-run"
        assert "issues_created" not in data, "issues_created should not exist in dry-run"
    finally:
        os.unlink(spec_file)

def test_project_name_fallback():
    """Test 4: Project name defaults to <repo-name> Board."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(FIXTURE_SPEC)
        spec_file = f.name
    try:
        rc, stdout, _ = run_script([
            "--spec-file", spec_file,
            "--repo", "ndethi/myrepo",
            "--dry-run",
        ])
        data = json.loads(stdout)
        assert data["project_name"] == "myrepo Board", f"Expected 'myrepo Board', got '{data['project_name']}'"
    finally:
        os.unlink(spec_file)

def test_column_defaults():
    """Test 5: Default columns are used when not overridden."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(FIXTURE_SPEC)
        spec_file = f.name
    try:
        rc, stdout, _ = run_script([
            "--spec-file", spec_file,
            "--repo", "test/repo",
            "--dry-run",
        ])
        data = json.loads(stdout)
        assert data["columns"] == ["Backlog", "In Progress", "Review", "Done"]
    finally:
        os.unlink(spec_file)

def test_empty_spec():
    """Test 6: Empty spec file returns 0 units extracted."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(EMPTY_SPEC)
        spec_file = f.name
    try:
        rc, stdout, _ = run_script([
            "--spec-file", spec_file,
            "--repo", "test/repo",
            "--dry-run",
        ])
        assert rc == 0
        data = json.loads(stdout)
        assert data["units_extracted"] == 0, f"Expected 0, got {data['units_extracted']}"
    finally:
        os.unlink(spec_file)

def test_issue_title_format():
    """Test 7: Issue titles follow [<SECTION>] <first line> format."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(FIXTURE_SPEC)
        spec_file = f.name
    try:
        rc, stdout, _ = run_script([
            "--spec-file", spec_file,
            "--repo", "test/repo",
            "--dry-run",
        ])
        data = json.loads(stdout)
        titles = data["units"][0]["title"]
        assert titles.startswith("[LOGIC]"), f"Expected title to start with '[LOGIC]', got '{titles}'"
    finally:
        os.unlink(spec_file)

if __name__ == "__main__":
    tests = [
        test_spec_parsing,
        test_label_mapping,
        test_dry_run_no_side_effects,
        test_project_name_fallback,
        test_column_defaults,
        test_empty_spec,
        test_issue_title_format,
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
