#!/usr/bin/env python3
"""
ideabrowser.py — Browse, triage, and manage ideas from Telegram/CLI/gateway.
Stores ideas as JSON in a local registry.

Usage:
  python ideabrowser.py --action <add|list|search|promote|reject|defer|export|stats> [options]
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional


DEFAULT_REGISTRY = os.path.expanduser("~/.hermes/profiles/exp/ideas.json")


def load_registry(path: str) -> Dict:
    """Load the idea registry from a JSON file. Returns empty structure if missing."""
    registry_path = Path(path)
    if not registry_path.exists():
        return {"ideas": []}
    data = registry_path.read_text()
    if not data.strip():
        return {"ideas": []}
    return json.loads(data)


def save_registry(registry: Dict, path: str) -> None:
    """Save the registry to a JSON file. Creates parent dirs."""
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Actions ----------

def action_add(args, registry):
    """Add a new idea to the registry."""
    idea = {
        "id": str(uuid.uuid4()),
        "text": args.text,
        "status": "pending",
        "tags": args.tags.split(",") if args.tags else [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    registry["ideas"].append(idea)
    save_registry(registry, args.registry)
    return {"action": "add", "idea": idea}


def action_list(args, registry):
    """List ideas, optionally filtered by status and/or tag."""
    ideas = registry["ideas"]
    if args.status:
        ideas = [i for i in ideas if i["status"] == args.status]
    if args.tag:
        ideas = [i for i in ideas if args.tag in i.get("tags", [])]
    return {"action": "list", "count": len(ideas), "ideas": ideas}


def action_search(args, registry):
    """Search ideas by text and tags."""
    query = args.query.lower()
    results = []
    for idea in registry["ideas"]:
        if query in idea["text"].lower():
            results.append(idea)
        elif any(query in tag.lower() for tag in idea.get("tags", [])):
            results.append(idea)
    return {"action": "search", "query": args.query, "count": len(results), "ideas": results}


def action_promote(args, registry):
    """Promote an idea: change status to 'promoted' and optionally export a spec file."""
    for idea in registry["ideas"]:
        if idea["id"] == args.id:
            idea["status"] = "promoted"
            idea["updated_at"] = now_iso()
            save_registry(registry, args.registry)
            result = {"action": "promote", "idea": idea}
            if args.export_file:
                spec_content = f"# {idea['text']}\n\n## Overview\n\nPromoted from idea registry.\n\n## Status\n\nPromoted on {idea['updated_at']}\n"
                Path(args.export_file).parent.mkdir(parents=True, exist_ok=True)
                Path(args.export_file).write_text(spec_content)
                result["file"] = args.export_file
            return result
    return {"action": "promote", "error": f"Idea {args.id} not found"}


def action_reject(args, registry):
    """Reject an idea: change status to 'rejected'."""
    for idea in registry["ideas"]:
        if idea["id"] == args.id:
            idea["status"] = "rejected"
            idea["updated_at"] = now_iso()
            save_registry(registry, args.registry)
            return {"action": "reject", "idea": idea}
    return {"action": "reject", "error": f"Idea {args.id} not found"}


def action_defer(args, registry):
    """Defer an idea: change status to 'deferred'."""
    for idea in registry["ideas"]:
        if idea["id"] == args.id:
            idea["status"] = "deferred"
            idea["updated_at"] = now_iso()
            save_registry(registry, args.registry)
            return {"action": "defer", "idea": idea}
    return {"action": "defer", "error": f"Idea {args.id} not found"}


def action_export(args, registry):
    """Export an idea as a markdown spec file."""
    for idea in registry["ideas"]:
        if idea["id"] == args.id:
            spec_content = f"""# {idea['text']}

## Overview
{idea['text']}

## Metadata
- ID: {idea['id']}
- Status: {idea['status']}
- Created: {idea['created_at']}
- Tags: {', '.join(idea.get('tags', []))}

## LOGIC
TODO: Define implementation steps.

## OUTPUTS
TODO: Define expected outputs.

## EDGE CASES
TODO: Define edge cases.
"""
            export_path = args.export_file or f"docs/SPEC-{idea['id'][:8]}.md"
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)
            Path(export_path).write_text(spec_content)
            return {"action": "export", "idea": idea, "file": export_path}
    return {"action": "export", "error": f"Idea {args.id} not found"}


def action_stats(args, registry):
    """Return statistics about ideas in the registry."""
    ideas = registry["ideas"]
    statuses = {}
    for idea in ideas:
        s = idea["status"]
        statuses[s] = statuses.get(s, 0) + 1
    return {"action": "stats", "total": len(ideas), "by_status": statuses}


ACTIONS = {
    "add": action_add,
    "list": action_list,
    "search": action_search,
    "promote": action_promote,
    "reject": action_reject,
    "defer": action_defer,
    "export": action_export,
    "stats": action_stats,
}


def main():
    parser = argparse.ArgumentParser(description="Browse, triage, and manage ideas.")
    parser.add_argument("--action", required=True, choices=list(ACTIONS.keys()))
    parser.add_argument("--text", default=None, help="Idea text (for add)")
    parser.add_argument("--id", default=None, help="Idea UUID")
    parser.add_argument("--status", default=None, help="Filter by status")
    parser.add_argument("--tag", default=None, help="Filter by tag")
    parser.add_argument("--tags", default=None, help="Comma-separated tags (for add)")
    parser.add_argument("--query", default=None, help="Search query")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY, help="Path to idea registry JSON")
    parser.add_argument("--export-file", default=None, help="Output file for export/promote")
    args = parser.parse_args()

    registry = load_registry(args.registry)
    handler = ACTIONS[args.action]
    result = handler(args, registry)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()