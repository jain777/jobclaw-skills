# Track presets

Each track sets the **emphasis**, the **links that matter most**, and the **gap questions** to prioritize. Default to these but adapt to the individual.

| Track | Emphasize | Push for links | Track-specific gap questions |
|---|---|---|---|
| **software** | Languages/stack, systems built, scale, OSS | **GitHub** (must), portfolio | Primary stack? Backend/frontend/ML/infra? Biggest system by scale? On-call/leadership? |
| **product** | Outcomes/metrics, 0→1 vs scaling, domains, team size | **GitHub** (if technical PM), portfolio/case studies | Which products & metrics moved? B2B/B2C? Team size managed? Technical depth? |
| **finance** | Deals, modeling, P&L, certifications (CFA), coverage | LinkedIn, deal sheet | IB/PE/corp-fin/FP&A? Deal sizes? Sectors? CFA/CPA progress? |
| **quant** | Math/stats, languages (Python/C++/R), research, returns | **GitHub**, papers | Research vs trading vs dev? Asset classes? Publications? Comp tooling? |
| **marketing** | Channels, growth metrics, campaigns, brand vs perf | **Portfolio** (must), case studies | Growth/brand/content/product mktg? Channels owned? Metrics (CAC, ROAS, MQLs)? |
| **founders-office** | Range, ambiguity, ops/strategy/special-projects, founder-adjacency | Portfolio, writing | Stage worked at? Strategy vs ops vs BD? Founder/CEO-adjacent scope? |
| **hr** | Recruiting/HRBP/L&D/comp, headcount scaled, systems | LinkedIn | Recruiting/generalist/specialist? Headcount supported? Tools (Workday/Greenhouse)? |
| **design** | Portfolio & case studies, design process, shipped products + user/business impact, craft, tooling | **Portfolio** (must), Dribbble/Behance | UX/UI/product/graphic/brand? Tools (Figma/Sketch/Adobe)? Shipped products & measurable impact? Research vs visual vs interaction depth? |
| **data** | Models/analyses & impact, stack (Python/SQL/Spark/cloud), data scale, experimentation, research | **GitHub**, Kaggle, scholar | DS / ML-eng / analytics / data-eng? Primary stack? Models shipped & business impact? Kaggle/publications? |
| **sales** | Quota attainment %, revenue/ARR closed, deal/ACV size, segment, ramp, ranking/President's Club | **LinkedIn** (must) | AE/SDR/BD/AM? Segment (SMB/mid/enterprise)? Quota & % attainment? Avg deal size/ACV? CRM (Salesforce/Outreach)? |
| **operations** | Process/efficiency gains, cost/time saved, cross-functional programs delivered, scale/headcount, systems | LinkedIn, portfolio (if PM artifacts) | Biz-ops / program / project / supply-chain? Scope (budget/headcount/regions)? Efficiency or cost metrics moved? Tools (Jira/Asana/SQL)? Certs (PMP/Six Sigma)? |
| **customer-success** | Retention/NRR/churn, NPS/CSAT, book of business, expansion/upsell, onboarding/time-to-value | LinkedIn | CSM/support/implementation/AM? Book size & segment? Retention/NRR/churn moved? CSAT/NPS? Tools (Gainsight/Zendesk)? |
| **content** | Published work & reach/engagement, portfolio/clips, SEO/traffic, voice/brand, formats owned | **Portfolio/clips** (must), Substack/Medium | Content strategy / copywriting / editorial / technical writing / comms? Formats? Traffic/engagement metrics? CMS/SEO tools? |
| **default** | Balanced; infer from resume | LinkedIn, portfolio | Target role & seniority? Must-have vs nice-to-have in next role? |

Across all tracks, always confirm the load-bearing `target.*` fields and hard constraints (work auth, relocation, comp floor, remote preference) — `find-jobs` and `score-fit` depend on them.

---

## Link gap matrix per track

Drives the **single optional closing prompt** in `build-profile` (step 3). After exhaustively extracting every URL from the user's resume / LinkedIn export / pasted text (see `scripts/extract_links.py` for PDFs), compare against this matrix and, in **one** track-aware question, surface what's missing — never interrogate.

| Track | Must-prompt if missing | Strongly-prompt if missing | Optional / mention-only | Skip |
|---|---|---|---|---|
| software | email, phone, github | linkedin, portfolio | stackoverflow, huggingface, blog, dev_to | scholar, twitter |
| product | email, phone, linkedin | portfolio | github (if technical), medium, twitter | scholar, kaggle |
| quant | email, phone, github | linkedin, scholar | kaggle, orcid, `other.papers` | portfolio, twitter |
| finance | email, phone, linkedin | website | medium (writing samples) | github, portfolio, twitter |
| marketing | email, phone, portfolio | linkedin, twitter | medium, substack, dribbble, youtube | github, scholar |
| founders-office | email, phone, linkedin | portfolio, substack, twitter | website, calendar, medium | scholar, kaggle |
| hr | email, phone, linkedin | website | medium | github, scholar |
| design | email, phone, portfolio | linkedin, dribbble, behance | instagram, medium, website | github (unless design-eng), scholar |
| data | email, phone, github | linkedin, kaggle | scholar, huggingface, medium | dribbble, twitter |
| sales | email, phone, linkedin | website | twitter | github, portfolio, scholar |
| operations | email, phone, linkedin | website | github, medium | dribbble, scholar, twitter |
| customer-success | email, phone, linkedin | website | medium | github, portfolio, scholar |
| content | email, phone, portfolio | linkedin, substack, medium | twitter, blog | github, scholar, dribbble |
| default | email, phone, linkedin | portfolio | github, twitter | — |

The closing prompt shape:
> *"I found these links: <list>. For <track> roles, candidates also commonly include: <strongly + optional gaps>. Want to add any? (Paste or skip.)"*

One prompt. Dismissible. No follow-ups.

---

## Default contact order per track

The per-track render-time ordering is defined **once**, in code, in
[`../../render-resume/templates/_common.py`](../../render-resume/templates/_common.py)
(`DEFAULT_CONTACT_ORDER_BY_TRACK`) — that's what actually runs, so it's the single source of truth.
This file no longer duplicates the table.

`build-profile`'s only job here is to optionally set the per-user override `contact_priority` in the
profile when the user has a clear preference. Precedence at render time:

> sidecar `contact_order` → profile `contact_priority` → track default (`_common.py`) → fallback order

Email + phone always render first (region-pack convention); the track ordering applies after them.
rendercv handles wrapping; links in `links.other` render last unless `contact_priority` lifts them.

## Proof-point coverage per track

Drives build-profile's **§3c proof-point gap prompt** — "what a strong candidate for this target
shows." Shared vocabulary in [`../../../knowledge/relevance.md`](../../../knowledge/relevance.md).
For **AI roles, defer to the archetype proof points** in
[`../../../knowledge/ai-roles.md`](../../../knowledge/ai-roles.md) (don't duplicate). For non-AI
tracks, the 2–3 load-bearing proofs to check coverage for:

| Track | Must-show proof points |
|---|---|
| software | a system built at scale (users/QPS/data), stack depth, OSS or shipped projects |
| product | metrics moved (activation/retention/revenue), a 0→1 or 0→N ship, discovery → decision story |
| marketing | a **portfolio / case study**, channel ownership, growth metrics (CAC, ROAS, reach, +%) |
| design | a **portfolio**, shipped products, measurable UX impact, process (research → iteration) |
| finance | deal/portfolio size, modeling/analysis, quantified outcomes, certifications (CFA/CPA) |
| data | datasets/scale, models or dashboards shipped, a business metric moved, tools (SQL/Python) |
| sales | quota attainment %, deal sizes, pipeline built, segments/markets owned |
| founders-office | 0→1 initiatives owned, cross-functional wins, scope/ambiguity handled, metrics |
| hr | programs run, headcount/retention metrics, systems implemented, stakeholders managed |

Check these against the extracted Experience/Projects/Achievements; surface the **missing** ones in
the single §3c prompt, framed by the target. Never invent the evidence — prompt for it or leave it.
