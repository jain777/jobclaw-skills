---
name: research-company
description: >
  Build a structured company × role brief — compensation, day-to-day, career growth,
  recent news, community sentiment (Reddit / Blind / Glassdoor), red flags, and a
  "fit for this user" view. Heavy reasoning — runs forked. Writes companies/<slug>.{md,json}
  sidecars consumed by prep-interview and coach-negotiation.
when_to_use: >
  Use before an interview round, before negotiating an offer, or whenever the user wants
  to decide whether to pursue a role at a specific company. Heavy — runs forked.
user-invocable: true
allowed-tools: Read, Write, WebSearch, WebFetch
context: fork
---

# research-company

A 360° brief on a company × role, grounded in real sources — every claim cites a URL. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md).

## Inputs
- `company` (required) — name or canonical key.
- `role` (optional but strongly recommended) — title at the target level.
- Profile: `profile/master-profile.md` for the `fit_for_user` view (read `context:` for *direction only*; never echo).

## Method (forked context — be liberal with WebSearch / WebFetch)

0. **Region pack.** Read `knowledge/regions/<code>.md` — comp norms (USD base+equity vs INR LPA CTC fixed+variable) and which community sources to weight (Glassdoor.com vs Glassdoor.in, `r/india` for IN-only).

1. **Discovery sweep** — site-restricted WebSearch queries (run a handful, don't be precious):
   - `"<company>" compensation "<role>" levels.fyi OR teamblind OR glassdoor`
   - `"<company>" "<role>" "day-to-day" OR responsibilities OR "what we do"`
   - `"<company>" career growth OR promotion OR ladder OR "career path"`
   - `"<company>" news (last 12 months)` — site:news.ycombinator.com OR site:techcrunch.com OR site:bloomberg.com OR site:theinformation.com

2. **Community sentiment.** Up to **5 results each** from:
   - Reddit — `r/cscareerquestions`, `r/ExperiencedDevs`, `r/csMajors`, `r/recruitinghell`, and `r/india` / `r/developersIndia` for IN.
   - **Blind** (`teamblind.com`) — when accessible.
   - **Glassdoor** (regional).
   Each = `{ content (≤ 20 words), link, source, date? }`. `WebFetch` the promising ones; quote sparingly.

3. **News pass** — `WebSearch` last-90-days news; surface **4–6 items** with date + 1-line summary + link.

4. **Compose the report** per [`reference/report-schema.md`](reference/report-schema.md):
   - `compensation` — `salaryBenchmarks.{baseSalary, totalCompensation}` (verbatim source strings) + `benefitsOverview[]`.
   - `jobSummary.{jobDescriptionSummary[], dayToDayResponsibilities[], careerGrowthOpportunities[]}` — 4–6 bullets each, drawn from sources (not invented).
   - `news.recentNews[]` — 4–6 items.
   - `discussions.{reddit[], blind[], glassdoor[]}` — what people *who work there* say. Honest: positive AND negative.
   - **`red_flags[]`** — 0–4 specific, sourced concerns. *"Glassdoor 2.8 with consistent WLB complaints (link)"*; *"Two CFOs in 18 months (TechCrunch, 2026-03)"*. Skip if nothing material.
   - **`fit_for_user[]`** — 2–3 bullets each linking a profile fact to a company fact. Reads `context:` for direction; **never echoes**.

5. **Cite everything.** Markdown report has links inline; JSON has explicit `link` / `source` fields per item, and a deduped `sources[]` at the root.

## Output
- `companies/<slug>.md` — human-readable; sections mirror the JSON; "Sources" footer lists every URL.
- `companies/<slug>.json` — schema-compliant per [`reference/report-schema.md`](reference/report-schema.md). Consumed by `prep-interview`, `coach-negotiation`.
- Console: 5-line summary — comp band · growth signal · top red flag · top fit · next suggested skill (`prep-interview` if pre-interview, `coach-negotiation` if pre-offer).

## Anti-patterns
- Compensation ranges without a source. If none found, set to `null`; don't write "$180k–$220k" with no link backing it.
- News older than 18 months (unless the user is researching a founding / legal / deal story).
- Empty arrays filled with placeholder strings ("No information found"). Use `[]`.
- Echoing `context.career_goal` / `context.additional_info` into `fit_for_user`.
- Pretending small samples are representative ("everyone on Blind says X" when there are 3 posts).
- Emoji.

## Rubric
- [ ] Every claim in the markdown has a source URL.
- [ ] `salaryBenchmarks` are verbatim from sources; if absent, `null`, not invented.
- [ ] Sentiment is balanced (positive + negative) where both exist.
- [ ] `red_flags` are specific and sourced (or absent).
- [ ] `fit_for_user` cites both a profile fact and a company fact per bullet.
- [ ] `sources[]` at root deduplicates every URL used.
