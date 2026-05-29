# Test report — jobclaw-skills

Last run: 2026-05-29. Re-run the automated layer with `python3 tests/smoke.py`.

## 1. Automated smoke tests (`tests/smoke.py`) — ✅ 16/16

Offline, stdlib-only, no keys. Covers:
- **compile** — 23 scripts under `skills/`+`knowledge/` all `py_compile` clean.
- **_jobposting** — parses schema.org JobPosting JSON-LD; `status_for` returns active/stale/expired correctly; aggregator URLs (Glassdoor SRCH) detected, real postings (Lever) not.
- **extract_links** — finds embedded `/URI` annotations in a synthetic PDF, `status: ok`, classifies LinkedIn.
- **jobstore** — `merge` stamps `is_new`/`first_seen`; re-run yields 0 new; `filter` drops a 2023 posting, keeps undated.
- **answer.py** — `--validate-pair` accepts a valid yes_no + numeric output.
- **to_rendercv** — `build_cv_document` produces a valid rendercv document (no rendercv install needed).
- **fixtures** — all 12 email + 2 offer fixtures parse and carry their `_expected`/offer blocks.

## 2. triage-inbox vs fixtures — ✅ 12/12

Classified each fixture independently against `knowledge/status/taxonomy.md`, then compared to `_expected`. **All 12 match** on `class` + `suggested_action`, including the two deliberate stress cases:
- `11-ambiguous-screen-vs-info` → **info / acknowledge** (positive tone + "in touch in 5–7 days" but **no action requested** → not a screen). ✓
- `12-rejection-soft` → **rejection / acknowledge** (warm praise — "genuinely impressed" — but "after comparing across candidates" closes it out). ✓

| fixture | expected (class / action) | triage result | ✓ |
|---|---|---|---|
| 01-rejection | rejection / acknowledge | rejection / acknowledge | ✓ |
| 02-screen | screen / reply-schedule | screen / reply-schedule | ✓ |
| 03-interview-invite | interview-invite / reply-schedule | interview-invite / reply-schedule | ✓ |
| 04-assessment | assessment / reply-accept (normal) | assessment / reply-accept | ✓ |
| 05-offer | offer / reply-ask | offer / reply-ask (no auto-accept) | ✓ |
| 06-recruiter-outbound | recruiter-outbound / reply-info | recruiter-outbound / reply-info | ✓ |
| 07-info | info / acknowledge | info / acknowledge | ✓ |
| 08-request-info | request-info / reply-info | request-info / reply-info | ✓ |
| 09-spam | spam / ignore | spam / ignore | ✓ |
| 10-other | other / escalate | other / escalate | ✓ |
| 11-ambiguous | info / acknowledge | info / acknowledge | ✓ |
| 12-rejection-soft | rejection / acknowledge | rejection / acknowledge | ✓ |

## 3. coach-negotiation vs offer fixtures — ✅ region-correct, guardrail held

- **offer-mercury-us** → US structure: base $215k / 8,500 ISO equity (4y, 1y cliff) / 20% target bonus / $25k signing. Counter anchors on base + equity refresh; leverage from JD-match + recruiter interest. **Draft only — never auto-sends** ("you send it").
- **offer-meesho-india** → IN structure: **CTC in LPA** (₹42 fixed + ₹8 variable + ESOPs + ₹2 retention = ₹52 total), **not USD**; **notice period (30d) is a lever**; counter anchors `fixed_lpa` first. Draft only.

Both respect `knowledge/work-authorization.md` region handling and the "human sends" rule.

## 4. score-fit — ✅ subscores + work-auth verdict

Scored a sample Senior PM (API) role against the example profile: graded met/partial/missing requirements, subscores summed to the headline score, `work_auth_verdict` applied against the **job's** region per `knowledge/work-authorization.md`. Sidecar shape matches `skills/score-fit/reference/score-schema.md`.

## 5. Resume pipeline (render-resume) — ✅ executed

Rendered a sample JSON-Resume (`product`/US/senior) with `render.py --theme engineeringresumes --max-pages 1`: produced a 1-page PDF, stdout reported `ATS-safe: yes`. Confirms the rendercv path is green standalone (requires the `.venv` install per README).

## Notes / known gaps
- The reasoning skills (triage/score-fit/coach-negotiation/etc.) are exercised by running them in Claude Code against fixtures; `smoke.py` covers the deterministic script layer + fixture integrity, not the reasoning (which has no offline oracle).
- India consumer/FMCG job recall remains thin without `SERPAPI_KEY`/`FIRECRAWL_API_KEY` (documented in `docs/JOB_SEARCH.md`).
