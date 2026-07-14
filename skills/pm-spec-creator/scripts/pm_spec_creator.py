#!/usr/bin/env python3
"""
pm_spec_creator.py — Read a project spec, extract structured units, create GitHub
Project board + issues. Supports --dry-run for preview without side effects.

Usage:
  python pm_spec_creator.py --spec-file <path> --repo <owner/repo> [--dry-run]
                            [--project-name <name>] [--column-names <csv>]
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional


# ---------- Spec Parsing ----------

SECTION_PATTERNS = {
    "LOGIC": {
        "label": "feature",
        "column": "Backlog",
        # Numbered items: 1. 2. 3. or ## LOGIC section with numbered sub-items
        "pattern": r"(?m)^\d+\.\s+(.+?)(?=\n\d+\.\s+|\n##|\Z)",
    },
    "EVAL": {
        "label": "eval",
        "column": "Backlog",
        # Lines containing eval_ or EVAL FIRST or eval_XX_ prefix
        "pattern": r"(?m)^(?:eval_[\w]+|EVAL\s+FIRST)[^\n]*(?:\n(?!\d+\.|\#)[^\n]+)*",
    },
    "EDGE CASES": {
        "label": "edge-case",
        "column": "Backlog",
        # Bullet items under ## EDGE CASES
        "pattern": r"(?m)^-\s+(.+?)(?=\n-\s+|\n##|\Z)",
    },
    "OUT OF SCOPE": {
        "label": "out-of-scope",
        "column": "Backlog",
        "pattern": r"(?m)^-\s+(.+?)(?=\n-\s+|\n##|\Z)",
    },
    "OUTPUTS": {
        "label": "deliverable",
        "column": "Backlog",
        "pattern": r"(?m)^-\s+(.+?)(?=\n-\s+|\n##|\Z)",
    },
    "ASSUMPTIONS": {
        "label": "assumption",
        "column": "Backlog",
        "pattern": r"(?m)^-\s+(.+?)(?=\n-\s+|\n##|\Z)",
    },
}


def parse_spec(spec_text: str) -> List[Dict[str, str]]:
    """Parse a markdown spec into structured units.

    Returns a list of dicts: {section, label, column, title, body}
    """
    units = []

    # Split spec into sections by ## headers
    sections = re.split(r"(?m)^(#{1,2}\s+.+)$", spec_text)
    # sections alternates: [preamble, "## HEADER1", body1, "## HEADER2", body2, ...]

    i = 1
    current_header = ""
    while i < len(sections):
        header_line = sections[i].strip()
        body = sections[i + 1] if i + 1 < len(sections) else ""

        # Match header to a known section pattern
        matched_section = None
        for section_name, pattern_def in SECTION_PATTERNS.items():
            if section_name.lower() in header_line.lower():
                matched_section = section_name
                break

        if matched_section:
            label = SECTION_PATTERNS[matched_section]["label"]
            column = SECTION_PATTERNS[matched_section]["column"]

            # Extract items from body
            if matched_section == "LOGIC":
                # Numbered items
                items = re.findall(r"(?m)^\d+\.\s+(.+?)(?=\n\d+\.\s+|\n##|\Z)", body, re.DOTALL)
                for idx, item_text in enumerate(items, 1):
                    first_line = item_text.strip().split("\n")[0][:120]
                    units.append({
                        "section": matched_section,
                        "label": label,
                        "column": column,
                        "title": f"[{matched_section}] {idx}. {first_line}",
                        "body": item_text.strip(),
                    })
            else:
                # Bullet items
                items = re.findall(r"(?m)^-\s+(.+?)(?=\n-\s+|\n##|\Z)", body, re.DOTALL)
                for item_text in items:
                    first_line = item_text.strip().split("\n")[0][:120]
                    units.append({
                        "section": matched_section,
                        "label": label,
                        "column": column,
                        "title": f"[{matched_section}] {first_line}",
                        "body": item_text.strip(),
                    })

        i += 2

    return units


# ---------- GitHub Operations ----------

def run_gh(args: List[str], capture: bool = True) -> str:
    """Run a gh CLI command and return stdout. Raises on failure."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=capture,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip() if capture else ""


def create_project(repo: str, project_name: str) -> str:
    """Create a GitHub Project (v2) and return its URL."""
    # gh project create --owner <owner> --title <name>
    owner = repo.split("/")[0]
    output = run_gh([
        "project", "create",
        "--owner", owner,
        "--title", project_name,
        "--format", "json",
    ])
    data = json.loads(output)
    return data.get("url", "")


def create_issue(repo: str, title: str, body: str, labels: List[str]) -> int:
    """Create a GitHub issue and return its number."""
    label_args = []
    for lbl in labels:
        label_args.extend(["--label", lbl])

    output = run_gh([
        "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body", body,
    ] + label_args)
    # gh issue create returns the URL; extract issue number
    match = re.search(r"/issues/(\d+)", output)
    return int(match.group(1)) if match else 0


def add_issue_to_project(project_url: str, issue_number: int, repo: str) -> None:
    """Add an issue to a GitHub Project board."""
    # gh project item-add <project-number> --url <issue-url> --owner <owner>
    # Extract project number from URL
    match = re.search(r"/projects/(\d+)", project_url)
    if not match:
        return
    project_num = match.group(1)
    owner = project_url.split("/")[3]  # extract owner from URL path

    issue_url = f"https://github.com/{repo}/issues/{issue_number}"
    run_gh([
        "project", "item-add", project_num,
        "--owner", owner,
        "--url", issue_url,
    ])


# ---------- Main ----------

DEFAULT_COLUMNS = ["Backlog", "In Progress", "Review", "Done"]


def main():
    parser = argparse.ArgumentParser(description="Create GitHub Project + issues from a spec file.")
    parser.add_argument("--spec-file", required=True, help="Path to the markdown spec file")
    parser.add_argument("--repo", required=True, help="GitHub repo (owner/repo)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating anything")
    parser.add_argument("--project-name", default=None, help="Override project name")
    parser.add_argument("--column-names", default=None, help="Comma-separated column names")
    args = parser.parse_args()

    # Read spec
    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        print(json.dumps({"error": f"Spec file not found: {args.spec_file}"}))
        sys.exit(1)

    spec_text = spec_path.read_text()

    # Parse
    units = parse_spec(spec_text)

    # Determine project name
    project_name = args.project_name or f"{args.repo.split('/')[1]} Board"
    columns = args.column_names.split(",") if args.column_names else DEFAULT_COLUMNS

    if args.dry_run:
        result = {
            "dry_run": True,
            "project_name": project_name,
            "columns": columns,
            "units_extracted": len(units),
            "units": [{"title": u["title"], "label": u["label"], "column": u["column"]} for u in units],
        }
        print(json.dumps(result, indent=2))
        return

    # Create project
    project_url = create_project(args.repo, project_name)

    # Create issues
    issues_created = []
    for unit in units:
        issue_num = create_issue(
            args.repo,
            unit["title"],
            unit["body"],
            [unit["label"]],
        )
        if issue_num:
            add_issue_to_project(project_url, issue_num, args.repo)
            issues_created.append({"number": issue_num, "title": unit["title"]})

    result = {
        "dry_run": False,
        "project_name": project_name,
        "project_url": project_url,
        "issues_created": len(issues_created),
        "issues": issues_created,
        "columns": columns,
        "units_extracted": len(units),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()