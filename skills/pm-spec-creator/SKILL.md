---
name: pm-spec-creator
description: |
  Reads a project spec (markdown), extracts structured sections (features, eval cases,
  edge cases), creates a GitHub Project board with columns, and generates issues from
  each extracted unit. Supports dry-run mode for preview without side effects.
version: 1.0.0
author: ndethi
license: MIT
tags: [pm, spec, github, project-management, automation]
---

# PM Spec Creator

## Overview

This skill reads a project specification (markdown), parses it into structured
units (features, eval cases, edge cases, out-of-scope items), and creates:
1. A **GitHub Project (v2)** board with standard columns (Backlog, In Progress, Review, Done).
2. **GitHub Issues** — one per extracted unit, labeled and assigned to the project.

## Inputs

- `--spec-file <path>` — Path to the markdown spec file (required).
- `--repo <owner/repo>` — Target GitHub repository (required).
- `--dry-run` — Preview extracted units + planned issues without creating anything.
- `--project-name <name>` — Override the default project name (defaults to repo name + " Board").
- `--column-names <comma-separated>` — Override default column names.

## Outputs

- JSON summary on stdout: `{ project_url, issues_created, columns, units_extracted }`.
-_actual GitHub Project + issues (when not `--dry-run`).

## Extraction Logic

The script parses the markdown spec and extracts:

| Section Pattern | Issue Label | Column |
|-----------------|-------------|--------|
| `## LOGIC` numbered items | `feature` | Backlog |
| `## EVAL` or `eval_` prefixed items | `eval` | Backlog |
| `## EDGE CASES` bullet items | `edge-case` | Backlog |
| `## OUT OF SCOPE` bullet items | `out-of-scope` | Backlog |
| `## OUTPUTS` items | `deliverable` | Backlog |
| `## ASSUMPTIONS` items | `assumption` | Backlog |

## CLI

```bash
# Dry run (preview)
python skills/pm-spec-creator/scripts/pm_spec_creator.py \
  --spec-file docs/SPEC-genealogy-viz.md \
  --repo ndethi/jnealogy \
  --dry-run

# Create project + issues
python skills/pm-spec-creator/scripts/pm_spec_creator.py \
  --spec-file docs/SPEC-genealogy-viz.md \
  --repo ndethi/jnealogy \
  --project-name "Jnealogy Board"
```

## Dependencies

- `gh` CLI (authenticated with `repo` and `project` scopes)
- Python 3.10+
- No third-party Python packages required

## Evals

`evals/test_pm_spec_creator.py` covers:
1. Spec parsing — extracts correct number of units from a fixture spec
2. Label mapping — units get correct labels
3. Dry-run mode — produces JSON summary without GitHub side effects
4. Project name fallback — defaults to repo name when not specified
5. Column defaults — uses standard columns when not overridden
6. Edge case — empty spec file returns empty extraction
7. Issue title format — `<section>: <first line of unit text>`