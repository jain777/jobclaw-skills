# AGENTS.md — JobClaw by whatNxtAI

Universal, runtime-neutral instructions for any coding/agent runtime that reads `AGENTS.md`
(Codex, Cursor, Hermes, OpenClaw, and friends). Claude Code reads `CLAUDE.md`; both point at the
same skills. For per-runtime setup, see [`docs/RUNTIMES.md`](docs/RUNTIMES.md).

## What this repo is

**JobClaw by whatNxtAI** is a collection of **20 portable [Agent Skills](https://agentskills.io)** that run an end-to-end job
hunt — onboarding a profile, searching jobs, scoring fit, tailoring resumes, writing cover letters,
answering application questions, triaging the recruiter inbox, prepping interviews, and coaching
negotiation — plus shared **knowledge packs**. The LLM is the engine: ~14 of the 20 skills are pure
reasoning and need no external API key. Only job search and company research use optional data-API
keys (copy `.env.example` → `.env`).

These skills are **runtime-agnostic**. Each is a `SKILL.md` directory under `skills/`, written to the
open agent-skills standard (`name` + `description` frontmatter, markdown body, optional `scripts/`
and `reference/`). Nothing here depends on a specific agent framework.

## How skills work here

- **Discovery / invocation.** Skills live in `skills/<verb-noun>/SKILL.md`. Invoke one when the task
  matches its `description` (auto), or explicitly by name. Each skill ends by naming the next step in
  the pipeline. Cross-runtime discovery paths and invocation syntax are in
  [`docs/RUNTIMES.md`](docs/RUNTIMES.md).
- **Composition is file-based, not call-based.** Skills do **not** invoke each other through a
  framework API. They compose via small JSON **sidecars** at fixed paths and one shared **master
  profile** — so the chain works identically on any runtime. The full stage map is in
  [`knowledge/pipeline.md`](knowledge/pipeline.md). Key sidecars:
  - `profile/master-profile.md` — the shared memory `build-profile` writes and every skill reads.
  - `jobs/current.json` — the job under work (`{company, role, url, job_id, jd_text, region, …}`).
  - `scores/<job-id>.score.json` — `score-fit` → `tailor-resume`.
  - `resumes/<slug>.tailor.json` — `tailor-resume` → `write-cover-letter`.
  - `companies/<slug>.json` — `research-company` → `prep-interview` / `coach-negotiation`.
  - `inbox/triage-<YYYY-MM-DD>.json` — `triage-inbox` → `infer-status` / `draft-reply`.
- **Scripts.** Thin Python 3 **stdlib-only** helpers under `skills/*/scripts/` — run them with
  `python3`. They print JSON to stdout, read keys from env, and degrade gracefully (never crash) when
  a key or dependency is missing. The one exception is `render-resume`, which uses
  [rendercv](https://github.com/rendercv/rendercv) in its own `.venv` (optional; install only if you
  need resume PDFs). Run `python3 scripts/doctor.py` to see what's installed.

## The hard rules (non-negotiable)

Every skill whose output reaches a human or downstream skill obeys
[`skills/_shared/RULES.md`](skills/_shared/RULES.md). In short:

1. **Never fabricate** — select, reorder, and reframe real experience; never invent roles, dates,
   metrics, tools, or skills. Flag genuine gaps instead.
2. **Never echo the `context:` block** — the profile's `career_goal` / `additional_info` direct output
   but never appear in anything a reader sees. (`career-coach` is the one documented exception, and may
   only paraphrase.)
3. **Region pack first** — before producing geography-varying text, read
   `knowledge/regions/<code>.md`; for work-authorization, `knowledge/work-authorization.md` (judged
   against the **job's** region).
4. **No emoji** — encouraging-coach voice, sentence case, verb-led.
5. **Known-info gate** — never re-ask what the profile, `jobs/current.json`, or a sidecar already holds;
   ask only genuinely missing fields, in one batched prompt.

## Runtime notes

- **Tool names are runtime-namespaced.** A few skills reference optional tools by their Claude-MCP
  names (e.g. `mcp__playwright__browser_navigate` for JS-page rendering in `build-profile` §1b). Every
  such use is **optional and gated** — if your runtime exposes the equivalent (browser automation, web
  fetch/search), map it; if not, the skill skips that path and degrades gracefully. The
  `allowed-tools` frontmatter is a Claude Code hint; other runtimes ignore it.
- **Preserve the directory tree.** Skills reference shared assets by relative path
  (`../../knowledge/…`, `../_shared/RULES.md`). Keep `skills/` and `knowledge/` together at the repo
  root so those paths resolve.
- **rendercv is optional.** Only `render-resume` / `tailor-resume` PDFs need it; everything else runs
  with stdlib alone.

For contributor conventions and testing, see `CLAUDE.md` and `CONTRIBUTING.md`.
