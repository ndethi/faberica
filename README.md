# Faberica — Autonomous MVP Framework

Faberica is an autonomous idea-to-MVP framework that borrows the Faber phase-gated lifecycle
but runs entirely independently of the `faber` repo. It provides:

- **pm-spec-creator** — a skill that reads a project spec, creates a GitHub Project board,
  and generates issues from structured spec sections.
- **ideabrowser** — a skill that lets you browse and triage ideas from Telegram, the CLI,
  or any gateway.
- A reusable framework for spinning up new MVP repos with the full Faber lifecycle
  (anchor → backlog → plan → implement → eval → PR → HITL merge → deploy).

## Repo Structure

```
faberica/
├── AGENTS.md              # Process constitution (borrowed from Faber, simplified)
├── FRAMEWORK.md           # Design authority (lifecycle, skill contracts)
├── skills/
│   ├── pm-spec-creator/   # PR #1
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── pm_spec_creator.py
│   │   └── evals/
│   │       └── test_pm_spec_creator.py
│   └── ideabrowser/       # PR #2
│       ├── SKILL.md
│       ├── scripts/
│       │   └── ideabrowser.py
│       └── evals/
│           └── test_ideabrowser.py
├── docs/
│   └── SPEC-autonomous-workflow.md
├── scripts/
│   ├── faber_iteration.sh
│   └── deploy_on_main.sh
├── LICENSE
└── README.md
```

## Branch Model

| Branch | Purpose |
|--------|---------|
| `main` | Production — never push directly |
| `dev`  | Integration — never commit directly, all changes via PR from `hermes/<topic>` |
| `hermes/<topic>` | Working branches — one logical change per branch |

## HITL Gates

- PR `dev ← hermes/<topic>`: Human reviews and merges.
- PR `main ← dev`: Human reviews and merges; triggers CI/CD to Cloudflare Pages.

## License

MIT