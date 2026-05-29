# Contributing to JobClaw Skills

Thanks for helping make the job hunt suck less. A few ground rules keep this repo trustworthy and portable.

## Hard rules (non-negotiable)

These are enforced in [`skills/_shared/RULES.md`](skills/_shared/RULES.md) and reviewed on every PR:

1. **Never fabricate.** Resumes, answers, cover letters, and outreach are grounded only in the user's profile. No invented metrics, employers, dates, or skills. Unknown → leave blank / mark `[VERIFY]`.
2. **Never raw-scrape LinkedIn.** It breaks LinkedIn's ToS and gets tools sued. Coverage comes via SerpApi, the user's own authenticated session (agent-side), or job-alert emails. No exceptions.
3. **No PII in commits or PRs.** Real profiles, resumes, scores, and job results are gitignored (`profile/master-profile*.md`, `resumes/`, `jobs/`, `scores/`). Use the `*.example.md` files for samples.
4. **Scripts stay Python 3 stdlib-only** (`urllib`/`json`/`argparse`/…). No `pip install` for adapters — they must run anywhere. The one exception is `render-resume`, which uses `rendercv` inside its own `.venv`.
5. **Degrade gracefully.** Any script that needs a key must print `[]`/empty + a stderr note when the key is absent — never crash.
6. **No emoji** in skill output or docs.

## Adding a job-search adapter

A source = `skills/find-jobs/scripts/<name>.py` that prints a JSON array in the [job schema](skills/find-jobs/reference/job-schema.md) and reads its key (if any) from the environment. Then list it in `find-jobs/SKILL.md` §3 and `reference/sources.md`. That's the whole contract.

## Adding a region

Copy `knowledge/regions/_schema.md`, fill in the ~6 sections (sources, work-auth rows, resume/comp conventions, decision rules), and add catalog rows to `knowledge/companies/companies.csv`. No skill code changes needed.

## Adding a skill

`skills/<verb-noun>/SKILL.md` (kebab-case, verb-led) + optional `reference/` and `scripts/`. Follow the frontmatter convention of the existing skills (`name`, `description` + `when_to_use`, `user-invocable`, `allowed-tools`). Heavy skills use `context: fork`.

## Before you open a PR

```
python3 tests/smoke.py    # compile + offline + fixture checks must pass
```

Keep changes focused, match the surrounding style, and update the relevant `reference/`/README when behavior changes.
