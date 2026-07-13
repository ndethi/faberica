# FRAMEWORK.md — Faberica Design Authority

## 1. Skill Contract

Every skill at `skills/<name>/` must have:
- `SKILL.md` — YAML frontmatter (`name`, `description`, `version`, `author`, `license`, `tags`) + markdown body
- `scripts/` — deterministic executable code (Python/Node); model only orchestrates
- `evals/` — automated test proving acceptance criteria (pytest)
- `references/` — load-on-demand docs (optional)
- `assets/` — templates (optional)

**No skill ships without a passing eval.**

## 2. Lifecycle Skills

| Stage | Skill | Purpose |
|-------|-------|---------|
| 1 | intent-collect | Collect project intent from spec/Telegram/CLI |
| 2 | scaffold | Generate project structure from intent |
| 3 | build | Compile the project |
| 4 | evaluate | Run quality gate (tests, lint, trajectory-guard) |
| 5 | deploy | Push to Cloudflare Pages |
| 6 | publish | Semantic version, tag, release notes |
| 7 | observe | Collect telemetry post-deploy |
| 8 | feedback | Close the loop (client feedback → triage → propose → HITL → build) |

## 3. Cross-Cutting Skills

| Skill | Purpose |
|-------|---------|
| pm-spec-creator | Read a spec, create GitHub Project + issues board |
| ideabrowser | Browse/triage ideas from Telegram/CLI/gateway |
| trajectory-guard | Diff expected vs actual trajectory |
| model-route | Pick local vs frontier per step |
| scope-ledger | Baseline scope + extended-scope items |

## 4. Telemetry

- Schema: `runs/telemetry.schema.json`
- Orchestrator: `orchestrator/orchestrator.py` sequences lifecycle skills per run plan
- Trajectory conformance: `exact` / `ordered` / `partial`

## 5. Autonomous Workflow

See `docs/SPEC-autonomous-workflow.md` for the full specification.

## 6. Post-Deploy Feedback Loop

```
observe → triage → propose → HITL → build → verify
```

## 7. Self-Extension

New skills are authored via the `skill-author` meta-skill (or manual PR).
Hard rules: no skill without eval; no skill without dedup search.

## 8. Build Plan

| Step | ID | Focus |
|------|-----|-------|
| 0 | build.00-init | Repo, registry, AGENTS.md |
| 1 | build.01-pm-spec-creator | pm-spec-creator skill |
| 2 | build.02-ideabrowser | ideabrowser skill |
| 3 | build.03-lifecycle | intent-collect → scaffold → build → evaluate → deploy → publish → observe → feedback |
| 4 | build.04-autonomous | faber_iteration.sh + deploy_on_main.sh + cron setup |