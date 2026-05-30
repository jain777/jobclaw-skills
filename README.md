# JobClaw Skills

Open-source [Claude Code](https://claude.com/claude-code) skills that run your **entire job hunt** — onboarding, search, fit scoring, tailored resumes, cover letters, application answers, recruiter-inbox triage, interview prep, and offer negotiation. Each skill is a self-contained workflow you invoke in Claude Code.

**Bring your own keys — but most skills need none, because Claude itself is the engine.** ~14 of the 19 skills are pure reasoning (no external API); only job search and company research use optional data-API keys.

These are the reusable **brain** behind JobClaw (an optional autonomous job-hunt agent) — but they stand alone: run them yourself in Claude Code, no agent required.

## Install

**As a Claude plugin (one command):**

```
/plugin marketplace add jain777/jobclaw-skills
/plugin install jobclaw-skills
```

(Replace `jain777/jobclaw-skills` with your fork/repo. The plugin auto-loads every skill in `skills/`.)

**Or manually:** clone this repo and copy `skills/` into your project's `.claude/skills/` (or symlink it).

**For `render-resume`** (the only skill with a non-Python dependency), install [rendercv](https://github.com/rendercv/rendercv) once:

```
python3 -m venv skills/render-resume/.venv
skills/render-resume/.venv/bin/pip install "rendercv[full]"
```

**Check your setup anytime** with `python3 scripts/doctor.py` — it reports whether rendercv is installed (the only install-required dependency, for resume PDFs) and which optional API keys are set. The skills flag a missing dependency **up front** and offer to install it, rather than failing mid-task.

## Quick start

1. **Onboard** — `/build-profile` (share a resume/LinkedIn PDF; it mines your links and can pull career memories from ChatGPT/Claude/Gemini). Writes `profile/master-profile.md`, the shared memory every other skill reads.
2. **Hunt** — `/find-jobs`, then `/score-fit` on the interesting ones.
3. **Apply** — `/apply-to-job <url>` runs the whole chain (score → tailored resume **PDF** → cover letter → form answers) in **auto-pilot or review** mode, stopping before anything is sent. Or run the pieces by hand: `/tailor-resume` (produces the PDF by default), `/write-cover-letter`, `/answer-application-questions`.
4. **Manage** — `/triage-inbox` recruiter emails, `/infer-status`, `/draft-reply`; `/prep-interview` + `/mock-interview`; `/coach-negotiation` on offers.

Every skill knows the pipeline (see [`knowledge/pipeline.md`](knowledge/pipeline.md)): it ends by naming the next step, reuses what's already captured (the profile + `jobs/current.json` + sidecars) instead of re-asking, and never fabricates.

## Skill catalog (20)

**Foundation & orchestration**
| Skill | Does | Keys |
|---|---|---|
| [`build-profile`](skills/build-profile) | Turns resume / LinkedIn PDF / AI-memory + **enriched links** into the canonical **master profile**. | none |
| [`apply-to-job`](skills/apply-to-job) | Orchestrates the apply chain for one job (score → tailored resume PDF → cover letter → answers) in **auto-pilot or review** mode; stops before submit. | none |

**Discovery**
| Skill | Does | Keys |
|---|---|---|
| [`find-jobs`](skills/find-jobs) | Searches jobs across 13 pluggable adapters (ATS-direct, SmartRecruiters, Teamtailor, YC, Cutshort, Adzuna, SerpApi, Firecrawl, HN…); dedupes + verifies freshness. See [`docs/JOB_SEARCH.md`](docs/JOB_SEARCH.md). | optional |
| [`score-fit`](skills/score-fit) | ATS-style fit score + matched/missing keywords + gaps + apply/skip call; work-auth aware. | none |
| [`research-company`](skills/research-company) | Comp, day-to-day, growth, news, sentiment, red flags. | optional (web) |
| [`map-career-path`](skills/map-career-path) | Real transition examples + a skill/experience gap roadmap. | optional (CSE) |

**Materials**
| Skill | Does | Keys |
|---|---|---|
| [`tailor-resume`](skills/tailor-resume) | Job-specific, ATS-optimized resume — **renders the PDF by default** (+ visual QA); never fabricates. | rendercv |
| [`render-resume`](skills/render-resume) | Typesets a resume to a polished **PDF** via [rendercv](https://github.com/rendercv/rendercv) (9 themes, clickable links, ATS-safe default). | rendercv |
| [`review-render`](skills/review-render) | Visual-QA auto-fix loop for the rendered PDF (widows/overflow/fill). | rendercv |
| [`write-cover-letter`](skills/write-cover-letter) | Tone-controlled, region-aware, one-page letter. | none |
| [`answer-application-questions`](skills/answer-application-questions) | Correct, format-obeying answers to application form questions. | none |

**Comms & status**
| Skill | Does | Keys |
|---|---|---|
| [`write-outreach`](skills/write-outreach) | Cold recruiter/referral message with one clear CTA. | none |
| [`triage-inbox`](skills/triage-inbox) | Classifies a recruiter email + extracts dates/links/asks + suggested action. | none |
| [`draft-reply`](skills/draft-reply) | Tone-matched reply draft for a chosen intent. | none |
| [`infer-status`](skills/infer-status) | Canonical application status + next action from signals. | none |

**Interview, negotiation & coaching**
| Skill | Does | Keys |
|---|---|---|
| [`prep-interview`](skills/prep-interview) | Likely questions + STAR talking points + a prep plan. | none |
| [`mock-interview`](skills/mock-interview) | Text interview loop + a scored report. | none |
| [`coach-negotiation`](skills/coach-negotiation) | Leverage analysis + ranges + a draft counter email (**you send it**). | none |
| [`career-coach`](skills/career-coach) | Open Q&A loaded with your master profile. | none |
| [`request-human-input`](skills/request-human-input) | The reasoning half of human-in-the-loop; composes a mobile-first question + parses the reply (pairs with the optional agent). | none |

## Knowledge packs

Shared intelligence every skill reads:
- [`knowledge/pipeline.md`](knowledge/pipeline.md) — the stage map + each skill's next step (how the skills chain).
- [`knowledge/regions/`](knowledge/regions) — per-region (US, India) job sources, **visa/sponsorship logic**, resume & comp conventions. Add a country by copying `_schema.md`.
- [`knowledge/work-authorization.md`](knowledge/work-authorization.md) — canonical work-auth enum + the cross-region rule (judge against the *job's* region).
- [`knowledge/companies/`](knowledge/companies) — a 3500+ company catalog (`companies.csv`, all industries + YC + frontier AI) + a cached ATS resolver (`resolved.json`).
- [`knowledge/ai-roles.md`](knowledge/ai-roles.md) — AI title filter + role archetypes.
- [`knowledge/status/taxonomy.md`](knowledge/status/taxonomy.md) — email-class × application-status decision table.

## Keys (all optional)

Copy `.env.example` → `.env`. Most skills need nothing. Job search gets stronger as you add keys (Adzuna is free; SerpApi/Firecrawl freemium) — full breakdown in [`docs/JOB_SEARCH.md`](docs/JOB_SEARCH.md).

## Design notes

- **The master profile** (`profile/master-profile.md`) is the shared memory; `build-profile` creates it, the rest consume it. Skills also compose via small JSON sidecars (e.g. `scores/<id>.score.json` → `tailor-resume`).
- **Claude is the model** — no external LLM key for reasoning skills.
- **Scripts are Python 3 stdlib only** (zero build), print JSON to stdout, read keys from env, and degrade gracefully when a key is absent.
- **Never fabricates** — every materials/comms skill is grounded in the profile; see [`skills/_shared/RULES.md`](skills/_shared/RULES.md).

## Roadmap

More region packs (Canada / EU / Singapore), Naukri & Internshala adapters (India consumer/FMCG recall), and direct enterprise-ATS adapters. (Relevance ranking shipped — `find-jobs` computes a real `fit_rank` and `score-fit`/`build-profile` share one matching engine; see [`knowledge/relevance.md`](knowledge/relevance.md).) Job-search strategy + caveats: [`docs/JOB_SEARCH.md`](docs/JOB_SEARCH.md).

## License & credits

[MIT](LICENSE). The AI-role archetype taxonomy in `knowledge/ai-roles.md` is adapted from the open-source [career-ops](https://github.com/santifer/career-ops) project. Contributions welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).
