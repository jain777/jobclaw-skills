# Runtimes — using jobclaw-skills across agents

These skills follow the open [Agent Skills](https://agentskills.io) standard (`SKILL.md` =
`name` + `description` frontmatter + markdown body + optional `scripts/` and `reference/`). The
same `skills/` directory drives every runtime below — `skills/` is the single source of truth.
The runtime-neutral entry point is [`../AGENTS.md`](../AGENTS.md).

## One-time setup

```bash
./scripts/install.sh            # wire all runtimes (symlinks + Cursor rules)
./scripts/install.sh codex      # or just one
./scripts/install.sh all --global   # also link user-level dirs (~/.agents/skills, ~/.hermes/skills)
./scripts/install.sh all --copy     # copy instead of symlink (Windows / restricted FS)
./scripts/install.sh --dry-run      # preview
```

`install.sh` is a thin wrapper over `scripts/setup_runtime.py` (pure stdlib, idempotent).

## Compatibility matrix

| Runtime | Reads SKILL.md? | Discovery path | Invoke | Setup |
|---|---|---|---|---|
| **Claude Code** | yes (native) | `.claude/skills/` or plugin | `/skill-name` | plugin install, or `install.sh claude` |
| **Codex CLI** | yes (native) | `.agents/skills/` (walks up) | `/skills`, `$mention`, or auto | `install.sh codex` |
| **OpenClaw** | yes (native) | workspace `skills/` | `openclaw skills …` or auto | native — run with this repo as workspace |
| **Hermes** | yes (native) | `./skills/` or `~/.hermes/skills/` | auto (description-gated) | native; `install.sh hermes --global` for user-level |
| **Cursor** | partial | `.cursor/rules/*.mdc` | auto-attach or `@rule-name` | `install.sh cursor` (generates `.mdc`) |

All runtimes also read **`AGENTS.md`** as injected instructions (Cursor, Codex, Hermes natively;
it's a sensible fallback for OpenClaw).

## Per-runtime notes

### Claude Code
The original target. Install as a plugin (`/plugin marketplace add … && /plugin install jobclaw-skills`)
or symlink `skills/` into `.claude/skills/` (`install.sh claude`). `allowed-tools` frontmatter is honored
here. Reads `CLAUDE.md`.

### Codex CLI
Codex scans `.agents/skills/` from the cwd up to the repo root. `install.sh codex` symlinks
`.agents/skills → ../skills`. Codex also reads `AGENTS.md` natively. Skills can be invoked explicitly
(`/skills`, `$mention`) or chosen implicitly from the `description`. The optional `agents/openai.yaml`
per-skill file (UI/branding, invocation policy) is **not** shipped — skills work without it.

### OpenClaw
OpenClaw uses the same SKILL.md standard as Claude Code and reads the workspace `skills/` directory
directly — no wiring needed when this repo is the workspace. Per-skill install via `openclaw skills`
also works.

### Hermes
Hermes auto-discovers skills from `./skills/` (project) or `~/.hermes/skills/` (user) and activates
them by the `description` field. Run from this repo as the project root, or `install.sh hermes --global`
to link into `~/.hermes/skills/`. Hermes injects `AGENTS.md` as session context.

### Cursor
Cursor's native rule format is `.cursor/rules/*.mdc`, not SKILL.md. `install.sh cursor` (or
`python3 scripts/gen_cursor_rules.py`) generates one **Agent-Requested** rule per skill — a thin
pointer whose `description` gates auto-attach and whose body says "read `skills/<name>/SKILL.md` and
follow it." The generated `00-jobclaw.mdc` is `alwaysApply: true` and carries the repo-wide rules.
Because the `.mdc` files are pointers, the SKILL.md stays the single source of truth — **rerun the
generator after editing any skill** (`scripts/gen_cursor_rules.py --check` flags staleness in CI).
Newer Cursor versions also read SKILL.md and `AGENTS.md` directly.

## Things that are runtime-namespaced

- **Optional MCP tools.** A few skills name optional tools by their Claude-MCP identifiers — e.g.
  `mcp__playwright__browser_navigate` / `…browser_snapshot` in `build-profile` §1b for rendering a
  JS-only page. Every such use is **gated and optional**: if your runtime exposes the equivalent
  (browser automation, web fetch/search), map it; otherwise the skill skips that path and asks the
  user instead. No skill hard-requires a Claude-specific tool.
- **`allowed-tools` frontmatter.** A Claude Code hint listing the tools a skill may use. Other runtimes
  ignore unknown frontmatter keys — harmless to leave in place.
- **Slash-command references in skill bodies** (e.g. "Next: `/score-fit`") are **prose suggestions** for
  the next step, not framework calls. Skills compose through JSON sidecars (see `AGENTS.md`), so the
  chain works regardless of how your runtime names its commands.

## Dependencies

- **Python 3** is required for the thin helper scripts under `skills/*/scripts/` — all stdlib-only.
- **rendercv** is the only non-stdlib dependency, and only `render-resume` / `tailor-resume` PDFs need
  it. Install once: `python3 -m venv skills/render-resume/.venv && skills/render-resume/.venv/bin/pip
  install "rendercv[full]"`. Everything else degrades gracefully without it. Run
  `python3 scripts/doctor.py` to check.
