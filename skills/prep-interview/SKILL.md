---
name: prep-interview
description: >
  Build an interview prep brief — 8–12 likely questions split across the loop's rounds,
  profile-grounded STAR talking points per question, a prep checklist, and diplomatic
  questions to ask back. Reads companies/<slug>.json from research-company if present;
  otherwise runs a thin in-line sweep. Forked context.
when_to_use: >
  Use before any interview round (recruiter screen, technical, hiring manager, panel,
  final / onsite). Compose with /research-company first for the richest output.
user-invocable: true
allowed-tools: Read, Write, WebSearch, WebFetch
context: fork
---

# prep-interview

Walk into the room ready. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md). Question quality bar: [`reference/prep-rubric.md`](reference/prep-rubric.md). Verb sourcing per `tailor-resume/reference/action-verbs.md`.

## Inputs
1. **company** + **role** (required).
2. **Profile** — `profile/master-profile.md` (Notes / voice for tone; experience for STAR stories).
3. **Optional company brief** — `companies/<slug>.json` from a prior `/research-company` run. If present, use it heavily; if absent, run a thin sweep here (≠ a full research pass).
4. **Optional round** — `--round screen | technical | hiring-manager | panel | final`. If omitted, generate questions across the whole likely loop.

## Method

0. **Region pack.** Read `knowledge/regions/<code>.md` — US: behavioral often STAR-formal; IN: more credential-led at large MNCs. Note tone adjustments.

1. **Hydrate the company.** If `companies/<slug>.json` exists, harvest:
   - `jobSummary.dayToDayResponsibilities` → likely "what would your first 30/60/90 look like" / "walk me through how you'd ..." Qs.
   - `news.recentNews` → 1–2 "saw the X announcement — how would you think about Y" Qs.
   - `red_flags` → honest concerns the *user* should diplomatically raise back.
   
   If absent, run a thin sweep: 3–5 `WebSearch` hits about the role + product + any recent news; no Reddit / Blind pass (that's `research-company`'s job, not this one).

2. **Identify the loop.** Map `target.tracks` to the canonical rounds from [`../mock-interview/reference/report-schema.md`](../mock-interview/reference/report-schema.md):
   - software → coding · system-design · behavioral
   - product → product-sense · execution · strategy · behavioral
   - design → portfolio-review · whiteboard/app-critique · behavioral
   - data → coding/SQL · ML/stats · case · behavioral
   - quant → math-stats · research · coding · behavioral
   - finance → technical · case · fit
   - marketing → case · craft · behavioral
   - founders-office → case · ops · behavioral
   - sales → discovery/role-play · pitch/demo · behavioral
   - operations → case · execution · behavioral
   - customer-success → scenario/role-play · case · behavioral
   - content → portfolio/clips-review · writing-exercise · behavioral
   - hr → case · craft · behavioral
   
   Cap rounds to those realistic for `target.seniority` (no system-design for entry-level SWE; behavioral always present).

3. **Generate 8–12 questions** total, split across rounds. Mix per [`reference/prep-rubric.md`](reference/prep-rubric.md):
   - **Generic** to the role/round (the predictable spine).
   - **Company-specific** (drawn from the brief).
   - **Profile-targeted** (a hiring manager *will* ask about the biggest claim on the resume — prep for it).

4. **For each question, emit 1–3 STAR talking-point bullets** *grounded in the profile* — no invented stories. STAR = Situation · Task · Action · Result. Keep bullets fragmentary (the user will fill them in conversationally).

5. **Prep checklist** — 4–8 items. Things to read / refresh / practice / prepare to ask back. Include honest concerns from `red_flags` for the user to probe diplomatically.

6. **Questions to ask back** — 3–6, drawn from `dayToDayResponsibilities`, `news`, and `red_flags`. Each one frames a real concern as a constructive question.

## Output

### `interviews/<company-slug>-<role-slug>.prep.md`

```
# Prep — <Company> · <Role>
> as of <date> · source: companies/<slug>.json | thin sweep

## What to know about the company
- 5 bullets, each with a source link

## Loop & questions

### Round 1 — <name>
**Q1.** ...
  - STAR: ...

**Q2.** ...
  - STAR: ...

### Round 2 — <name>
...

## Prep checklist
- [ ] ...

## Questions to ask back
- (honest concern, diplomatic framing): "..."
- ...
```

### Stdout
3-line summary — `# questions across # rounds · 1 most important Q · suggested next` (`/mock-interview` with this prep + role).

## Anti-patterns
- Generic SWE Qs in a PM loop (or vice-versa).
- Inventing project stories the profile doesn't show.
- "Tell me about yourself" filler stacked on multiple rounds (one is fine if a screen leads).
- Quoting `context.career_goal` / `context.additional_info`.
- Cookie-cutter "Tell me about a time you failed" without a profile-grounded angle.
- Asking-back questions that are gripes in disguise — keep them constructive.
- Emoji.

## Rubric
See [reference/prep-rubric.md](reference/prep-rubric.md). Plus:
- [ ] 8–12 Qs total; balanced across the loop's rounds.
- [ ] ≥ 3 Qs are company-specific (cite source from brief or sweep).
- [ ] Every STAR bullet cites a profile fact (`experience[i]`, project, skill).
- [ ] Checklist has ≥ 1 item per round.
- [ ] Questions-to-ask-back includes ≥ 1 diplomatic raise of a `red_flag` from the brief (when one exists).
