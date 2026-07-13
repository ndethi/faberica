---
name: ideabrowser
description: |
  Browse, triage, and manage ideas from Telegram, CLI, or any gateway. Stores ideas
  as JSON in a local registry, supports search, filtering, promotion to specs, and
  integration with the pm-spec-creator skill for GitHub project setup.
version: 1.0.0
author: ndethi
license: MIT
tags: [ideation, telegram, cli, idea-management, triage]
---

# Ideabrowser

## Overview

A lightweight idea management tool that lets you:
1. **Capture** ideas from Telegram messages, CLI input, or any text source.
2. **Browse** ideas with filtering by status, tag, or date.
3. **Triage** ideas: promote, reject, defer, or convert to a spec file.
4. **Export** ideas as markdown specs ready for `pm-spec-creator`.

## Inputs

- `--action <add|list|search|promote|reject|defer|export|stats>` — Action to perform (required).
- `--text <idea text>` — Idea text (for `add`).
- `--id <idea_id>` — Idea UUID (for `promote`, `reject`, `defer`, `export`).
- `--status <pending|promoted|rejected|deferred>` — Filter by status (for `list`).
- `--tag <tag>` — Filter by tag (for `list`, `search`).
- `--query <text>` — Search query (for `search`).
- `--registry <path>` — Path to the idea registry JSON (default: `~/.hermes/profiles/exp/ideas.json`).
- `--export-file <path>` — Output file for `export` action (writes a markdown spec).

## Outputs

All actions return JSON on stdout. `export` writes a markdown file and returns `{ file, idea_id }`.

## CLI

```bash
# Add an idea
python skills/ideabrowser/scripts/ideabrowser.py \
  --action add \
  --text "Interactive genealogy visualization with d3.js"

# List all pending ideas
python skills/ideabrowser/scripts/ideabrowser.py \
  --action list --status pending

# Search ideas
python skills/ideabrowser/scripts/ideabrowser.py \
  --action search --query "genealogy"

# Promote an idea to a spec file
python skills/ideabrowser/scripts/ideabrowser.py \
  --action promote --id <uuid> --export-file docs/SPEC-my-idea.md

# Get stats
python skills/ideabrowser/scripts/ideabrowser.py --action stats
```

## Registry Format

```json
{
  "ideas": [
    {
      "id": "uuid",
      "text": "idea text",
      "status": "pending|promoted|rejected|deferred",
      "tags": ["tag1", "tag2"],
      "created_at": "ISO-8601",
      "updated_at": "ISO-8601"
    }
  ]
}
```

## Dependencies

- Python 3.10+
- No third-party packages required

## Evals

`evals/test_ideabrowser.py` covers:
1. Add idea — creates entry with UUID and pending status
2. List ideas — returns filtered list
3. Search — matches text and tags
4. Promote — changes status to promoted and exports spec file
5. Reject — changes status to rejected
6. Defer — changes status to deferred
7. Stats — returns counts by status
8. Empty registry — handles missing registry file gracefully