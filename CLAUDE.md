# CLAUDE.md — jobclaw-skills

Contributor onboarding for this repo. (Users don't need this — they just install the plugin and run the skills; see `README.md`.)

## What this is
A collection of **19 Claude Code skills** for an end-to-end job hunt, plus shared **knowledge packs**. Claude is the engine — most skills are pure reasoning; a handful have thin Python (stdlib) data-fetch scripts. Skills compose through a shared **master profile** (`profile/master-profile.md`) and small JSON **sidecars**, not a database.

## Layout
```
skills/<verb-noun>/SKILL.md        # one skill each (+ optional reference/, scripts/)
skills/_shared/RULES.md            # the hard rules every skill obeys
knowledge/regions/<code>.md        # per-region sources, sponsorship, conventions
knowledge/work-authorization.md    # canonical work-auth enum + cross-region rule
knowledge/companies/{companies.csv,resolved.json,SOURCES.md}  # catalog + cached ATS resolver
knowledge/ai-roles.md              # AI title filter + archetypes
knowledge/status/taxonomy.md       # email-class × application-status decision table
docs/JOB_SEARCH.md                 # find-jobs strategy + source tiers + caveats
tests/                             # smoke.py runner + fixtures (emails, offers, jobpostings)
profile/master-profile.example.md  # sample profile (the real one is gitignored)
```

## Conventions
- **Skills:** kebab-case, verb-led; frontmatter = `name`, `description` (+ `when_to_use`), `user-invocable`, `allowed-tools`; heavy skills use `context: fork`.
- **Scripts:** Python 3 **stdlib only**, print JSON to stdout, read keys from env, degrade gracefully (print `[]` + stderr note, never crash). Exception: `render-resume` uses `rendercv` in its own `.venv`.
- **Brand/voice:** address the user as "you"; verb-led, sentence case; **no emoji**.
- **Never fabricate**; **never raw-scrape LinkedIn**; **no PII committed** (real profiles/resumes/scores/jobs are gitignored). Full rules: `CONTRIBUTING.md` + `skills/_shared/RULES.md`.

## Testing
```
python3 tests/smoke.py    # compile gate + offline functional checks + fixture integrity
```
Reasoning skills (triage-inbox, score-fit, coach-negotiation, …) are exercised by running them in Claude Code against `tests/fixtures/` and comparing to each fixture's `_expected` block. See `tests/REPORT.md` for the latest run.

## Optional agent
These skills also power **JobClaw**, an optional autonomous agent that consumes them plus execution tooling (browser automation, email, human-in-the-loop messaging). The agent lives in a separate project; nothing here depends on it — every skill runs standalone in Claude Code.
