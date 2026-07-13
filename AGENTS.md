# AGENTS.md — Faberica Framework Constitution

## 1. Design Authority

- **FRAMEWORK.md** is the design source of truth (architecture, invariants, skill contracts).
- **AGENTS.md** is the process constitution (rules, gates, definitions of done).
- When they disagree on *design*, FRAMEWORK.md wins. Open a PR fixing AGENTS.md first.

## 2. Operating Rules

### 2.1 Git is the source of truth
No state lives outside the repo. All artifacts (specs, trajectories, telemetry, evals, skills) are committed files.

### 2.2 Branch model
- `main` — production. **Never push here.** Promotion = human-merged `dev → main` PR.
- `dev` — integration. **Never commit directly.** All changes flow via PRs from `hermes/<topic>` branches.
- `hermes/<topic>` — working branches. One logical change per branch, one PR per branch, base **always `dev`**.

### 2.3 PR discipline
- Every PR targets `dev`. Human reviews and merges.
- Use `gh pr create --base dev`.

### 2.4 Commit style (Conventional Commits)
```
feat:   new capability
fix:    bug fix
chore:  maintenance, tooling, docs
refactor: code change without behavior change
test:   test additions or fixes
```

### 2.5 Plan before edit
Write a 3–5 line plan into `runs/hermes/iteration-log.md` *before* editing. State the spec reference, expected diff.

### 2.6 HITL gates (human-in-the-loop)
A gate means: **PR opened → human reviews → human merges**. No auto-merge past a gate.

### 2.7 No fabrication
Unknown facts = `TODO:` in the artifact. Never invent.

### 2.8 Executable acceptance > LLM judge
Deterministic checks are the gate. The judge only evaluates what deterministic checks cannot.

## 3. Skill Contract

Every skill at `skills/<name>/` contains:
- `SKILL.md` — YAML frontmatter + markdown body
- `scripts/` — deterministic code; model only orchestrates
- `evals/` — automated test proving acceptance criteria
- `references/` — load-on-demand docs (optional)

**No skill ships without a passing eval.**

## 4. Definitions of Done

### Skill-level
- `SKILL.md` + `scripts/` + `evals/` present
- Eval passes (`python -m pytest skills/<name>/evals/`)
- Registry entry in `_registry.md` with `status: active`

### Build-step level
- All skills in step complete
- HITL gate cleared (human merged PR)

## 5. Autonomous Workflow

Faberica supports an autonomous iteration loop:
1. **Cron** triggers `faber_iteration.sh` every 15 min.
2. Agent picks the highest-priority backlog item, implements on `hermes/<topic>`, opens PR to `dev`.
3. Agent **stops** and notifies Telegram with the PR URL.
4. **Human** reviews and merges into `dev`.
5. When `dev → main` PR is merged, `deploy_on_main.sh` detects the `deploy-*` tag and publishes to Cloudflare Pages.
6. Agent continues with the next backlog item after merge.

## 6. Reference Files
```
@AGENTS.md
@FRAMEWORK.md
@runs/hermes/STATE.json
@runs/hermes/backlog.md
```