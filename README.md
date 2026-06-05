# JobClaw Skills

<p align="center">
  <em>Your entire job hunt, run from inside your AI coding agent.</em><br>
  Onboarding, search, fit scoring, tailored resumes, cover letters, recruiter triage, interview prep, and negotiation —<br>
  <strong>20 portable skills, one master profile, every word grounded in your real experience.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-000?style=flat&logo=anthropic&logoColor=white" alt="Claude Code">
  <img src="https://img.shields.io/badge/Codex-111827?style=flat&logo=openai&logoColor=white" alt="Codex">
  <img src="https://img.shields.io/badge/Cursor-0A0A0A?style=flat&logo=cursor&logoColor=white" alt="Cursor">
  <img src="https://img.shields.io/badge/Hermes-6E56CF?style=flat&logo=gnometerminal&logoColor=white" alt="Hermes">
  <img src="https://img.shields.io/badge/OpenClaw-1F6FEB?style=flat&logo=openclaw&logoColor=white" alt="OpenClaw">
  <img src="https://img.shields.io/badge/Agent_Skills-SKILL.md-2EAD33?style=flat" alt="Agent Skills standard">
  <img src="https://img.shields.io/badge/Python_3-stdlib-3776AB?style=flat&logo=python&logoColor=white" alt="Python 3 stdlib">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT">
</p>

---

## What is this

Open-source [Agent Skills](https://agentskills.io) that run your **entire job hunt** from inside an AI coding agent. Each skill is a self-contained `SKILL.md` workflow; together they form a pipeline that:

- **Onboards you once** — a resume / LinkedIn PDF (links and all) becomes the canonical **master profile** every other skill reads
- **Finds and scores jobs** — 13 pluggable adapters (ATS-direct, SmartRecruiters, YC, HN…), deduped and freshness-verified, ranked against your profile
- **Builds the materials** — ATS-optimized tailored resume **PDFs**, cover letters, and application-form answers
- **Runs the recruiter loop** — classifies inbox emails, infers application status, drafts tone-matched replies
- **Preps the human moments** — interview question banks + mock interviews, and offer-negotiation coaching

> **This is a filter, not a spray-and-pray tool.** The skills never fabricate, never echo your private goals into anything a recruiter sees, and **never submit anything for you** — every artifact stops before send so you have the final call. See [`skills/_shared/RULES.md`](skills/_shared/RULES.md).

**Bring your own keys — but most skills need none, because the model itself is the engine.** ~14 of the 20 skills are pure reasoning (no external API); only job search and company research use optional data-API keys.

These are the reusable **brain** behind JobClaw (an optional autonomous job-hunt agent) — but they stand alone: run them yourself in any supported runtime, no agent required.

## Features

| Feature | Description |
|---|---|
| **One master profile** | Onboard once from a resume/LinkedIn PDF (mines embedded links, can import ChatGPT/Claude/Gemini career memories); every skill reads it, nothing is re-asked. |
| **Multi-source search** | 13 adapters across Greenhouse/Lever/Ashby/Workday/SmartRecruiters/Teamtailor/YC/Cutshort/HN + Adzuna/SerpApi/Firecrawl, deduped across runs and verified live for freshness. |
| **Fit scoring** | ATS-style match % + matched/missing keywords + gaps + an apply-or-skip call, work-authorization aware (judged against the *job's* region). |
| **ATS resume PDFs** | Tailored, keyword-aligned resumes rendered via [rendercv](https://github.com/rendercv/rendercv) (9 themes, clickable links, ATS-safe default) with a visual-QA auto-fix loop. |
| **Recruiter inbox loop** | Classify → infer status → draft reply, driven by a shared email-class × application-status taxonomy. |
| **Interview + negotiation** | Question banks with STAR talking points, a text mock-interview loop with a scored report, and leverage-based counter-offer drafts. |
| **Region intelligence** | Per-region (US, India) sources, sponsorship logic, resume/comp conventions — add a country by copying one schema file. |
| **Human-in-the-loop** | The model evaluates and drafts; you decide and send. No auto-submit, ever. |
| **Never fabricates** | Selects, reorders, and reframes real experience; flags genuine gaps instead of inventing them. |

## Quick start

```bash
# 1. Clone
git clone https://github.com/jain777/jobclaw-skills && cd jobclaw-skills

# 2. Wire it into your agent (symlinks skills/ + generates Cursor rules; idempotent)
./scripts/install.sh                  # all runtimes — or: codex | cursor | hermes | openclaw | claude

# 3. (Optional) install rendercv for resume PDFs, then check your setup
python3 -m venv skills/render-resume/.venv
skills/render-resume/.venv/bin/pip install "rendercv[full]"
python3 scripts/doctor.py             # reports rendercv + which optional API keys are set

# 4. Open your agent in this directory and onboard
#    e.g. /build-profile  (share a resume/LinkedIn PDF)
```

## Use with your runtime

These follow the open agent-skills standard (`SKILL.md`), so the **same `skills/` directory** drives every runtime. `install.sh` (a stdlib-only wrapper over `scripts/setup_runtime.py`) links `skills/` into each runtime's discovery path; pass `--global` for user-level dirs, or `--copy` on Windows / restricted filesystems.

| Runtime | Wire it | Then invoke |
|---|---|---|
| **Claude Code** | plugin (below), or `./scripts/install.sh claude` | `/skill-name` |
| **Codex** | `./scripts/install.sh codex` (links `.agents/skills`) | `/skills`, `$mention`, or auto |
| **Cursor** | `./scripts/install.sh cursor` (generates `.cursor/rules/*.mdc`) | auto-attach, or `@rule-name` |
| **Hermes** | native (`./skills/`); `--global` links `~/.hermes/skills/` | auto (description-gated) |
| **OpenClaw** | native — run with this repo as the workspace | `openclaw skills …` or auto |

Every runtime also reads [`AGENTS.md`](AGENTS.md), the runtime-neutral guide. Full matrix, invocation details, and tool-namespacing notes: [`docs/RUNTIMES.md`](docs/RUNTIMES.md).

**Claude Code plugin (one command):**

```
/plugin marketplace add jain777/jobclaw-skills
/plugin install jobclaw-skills
```

(Replace `jain777/jobclaw-skills` with your fork/repo. The plugin auto-loads every skill in `skills/`.)

## Usage

Invoke a skill by name (slash command in Claude Code / Cursor / Codex; description-matched auto-invoke in Hermes / OpenClaw):

```
/build-profile                 → onboard: resume/LinkedIn PDF → master profile
/find-jobs                     → search + rank jobs against your profile
/score-fit                     → ATS-style fit score + apply/skip call for one job
/apply-to-job <url>            → full chain: score → resume PDF → cover letter → answers (stops before submit)
/tailor-resume                 → job-specific ATS resume, rendered to PDF + visually QA'd
/write-cover-letter            → one-page, region-aware cover letter
/answer-application-questions  → format-obeying answers to a form's questions
/triage-inbox                  → classify a recruiter email + extract dates/links/asks
/infer-status                  → canonical application status + next action
/draft-reply                   → tone-matched reply for a chosen intent
/research-company              → comp, day-to-day, growth, sentiment, red flags
/prep-interview                → likely questions + STAR talking points
/mock-interview                → text interview loop + scored report
/coach-negotiation             → leverage analysis + ranges + a draft counter (you send it)
/career-coach                  → open Q&A loaded with your profile
/write-outreach                → cold recruiter/referral message with one CTA
/map-career-path               → transition examples + a gap roadmap
```

Or just paste a job URL or description — `apply-to-job` / `score-fit` auto-detect it and capture the job once (`jobs/current.json`), so you never retype the JD.

## How it works

```
   /build-profile                profile/master-profile.md  ── the shared memory ──┐
        │                                                                          │
        ▼                                                                          │
   /find-jobs ──► /score-fit ──► apply or skip                                     │
                      │            │ (>= threshold)                                │
                      │            ▼                                               │
                      │     /apply-to-job  ──►  /tailor-resume (PDF)               │
                      │                          /write-cover-letter        reads ─┤
                      │                          /answer-application-questions     │
                      │                                  │                         │
                      │                          stops before submit — you send    │
                      ▼                                                            │
   recruiter loop:  /triage-inbox ──► /infer-status ──► /draft-reply        reads ─┤
                                                                                   │
   interview:       /research-company ──► /prep-interview ──► /mock-interview      │
                                                                                   │
   offer:           /coach-negotiation  (draft counter — you send)          reads ─┘

   Skills compose through JSON sidecars (jobs/current.json, scores/, resumes/,
   companies/, inbox/), not framework calls — so the chain runs on any runtime.
```

Full stage map: [`knowledge/pipeline.md`](knowledge/pipeline.md).

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

## Project structure

```
jobclaw-skills/
├── AGENTS.md                  # Runtime-neutral entry point (Codex / Cursor / Hermes)
├── CLAUDE.md                  # Claude Code contributor notes
├── skills/                    # 20 SKILL.md skills (+ _shared/RULES.md, the canon)
│   └── <verb-noun>/
│       ├── SKILL.md           # one skill workflow
│       ├── reference/         # optional schemas / rubrics
│       └── scripts/           # optional Python (stdlib) helpers
├── knowledge/                 # shared packs: regions, companies, ai-roles, status, pipeline
├── scripts/
│   ├── install.sh             # wire skills into a runtime (wrapper)
│   ├── setup_runtime.py       # per-runtime discovery wiring
│   ├── gen_cursor_rules.py    # SKILL.md → .cursor/rules/*.mdc
│   └── doctor.py              # check rendercv + API keys
├── .cursor/rules/             # generated Cursor rules (one per skill)
├── docs/                      # RUNTIMES.md (compat matrix) + JOB_SEARCH.md
├── tests/                     # smoke.py runner + fixtures
└── profile/                   # master-profile.example.md (your real one is gitignored)
```

## Keys (all optional)

Copy `.env.example` → `.env`. Most skills need nothing. Job search gets stronger as you add keys (Adzuna is free; SerpApi/Firecrawl freemium) — full breakdown in [`docs/JOB_SEARCH.md`](docs/JOB_SEARCH.md).

## Design notes

- **The master profile** (`profile/master-profile.md`) is the shared memory; `build-profile` creates it, the rest consume it. Skills also compose via small JSON sidecars (e.g. `scores/<id>.score.json` → `tailor-resume`).
- **The model is the engine** — no external LLM key for reasoning skills; runs on whichever model your runtime provides.
- **Runtime-agnostic by design** — `SKILL.md` + relative-path knowledge packs + JSON sidecars, no framework lock-in. See [`docs/RUNTIMES.md`](docs/RUNTIMES.md).
- **Scripts are Python 3 stdlib only** (zero build), print JSON to stdout, read keys from env, and degrade gracefully when a key is absent.
- **Never fabricates** — every materials/comms skill is grounded in the profile; see [`skills/_shared/RULES.md`](skills/_shared/RULES.md).

## Roadmap

More region packs (Canada / EU / Singapore), Naukri & Internshala adapters (India consumer/FMCG recall), and direct enterprise-ATS adapters. (Relevance ranking shipped — `find-jobs` computes a real `fit_rank` and `score-fit`/`build-profile` share one matching engine; see [`knowledge/relevance.md`](knowledge/relevance.md).) Job-search strategy + caveats: [`docs/JOB_SEARCH.md`](docs/JOB_SEARCH.md).

## License & credits

[MIT](LICENSE). The AI-role archetype taxonomy in `knowledge/ai-roles.md` is adapted from the open-source [career-ops](https://github.com/santifer/career-ops) project. Contributions welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).
