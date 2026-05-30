---
name: score-fit
description: >
  Score how well the user's master profile fits a specific job — an ATS-style match
  percentage with matched/missing keywords, strengths, gaps, and a clear apply-or-skip
  recommendation. Optionally writes a structured sidecar that tailor-resume consumes.
when_to_use: >
  Use to evaluate a single job (or a few) against the user's profile before they spend
  effort applying — typically on the top results from find-jobs, or any job description
  the user pastes.
user-invocable: true
allowed-tools: Read, Write
---

# score-fit

Judge a job against the user's profile the way a good recruiter + ATS would, and give a decision — not just a number.

## Inputs
1. The profile: read `profile/master-profile.md`.
   - **Missing** → offer a degraded one-shot mode: score against a resume/profile snippet the user
     pastes now, and set `profile_missing: true` in the sidecar. Suggest `/build-profile` for next time.
   - **Stale** → if fields the score depends on are marked `[VERIFY]`, warn in the output and set
     `profile_stale: true`. Never credit `[VERIFY]` facts toward must-haves.
2. The job: a pasted description, a URL to fetch, or an entry from `jobs/found-<date>.json`.
   **Known-info gate (RULES §6):** if no job is given inline, read `jobs/current.json` (the job under
   work) and use its `jd_text`/`url` — do not re-ask for the JD if it's already captured. After
   resolving the job, **write/refresh `jobs/current.json`** (`{company, role, url, job_id, jd_text,
   region, source, captured_at}`) so `tailor-resume` / `write-cover-letter` / `answer-application-questions`
   reuse it without asking again. Only ask the user for a job if none is supplied and `current.json` is absent.

## Method (think like an ATS, then like a hiring manager)

0. **Apply work-authorization logic first.** Determine the **job's** country and resolve the
   applicant's `work_auth` per [`../../knowledge/work-authorization.md`](../../knowledge/work-authorization.md)
   — it uses the **job's** region pack, not the applicant's, and returns one of
   `NON-ISSUE / MINOR-NOTE / MAJOR-FILTER / DISQUALIFIER`. Record it as `work_auth_verdict`.
   (E.g. India applicant + India job → NON-ISSUE: do not raise or penalize; weight notice-period/CTC
   fit instead. The same applicant + a US "no sponsorship" job → MAJOR-FILTER.)

1. **Extract the job's requirements**: hard requirements (must-haves), preferred (nice-to-haves),
   key skills/keywords, seniority, domain, location/remote, comp if stated.
   - **AI/ML roles:** if the role is AI/ML, detect its **archetype** per
     [`../../knowledge/ai-roles.md`](../../knowledge/ai-roles.md) (AI Platform/LLMOps · Agentic ·
     Technical AI PM · Solutions Architect · Forward-Deployed · Transformation). Weight the `domain`
     and `must_haves` sub-scores toward that archetype's proof points, note it in `strengths`/`gaps`,
     and **record `archetype` in the sidecar**. Distinguish genuine AI roles from "AI" used only as a
     buzzword (title filter in ai-roles.md).

2. **Grade each requirement** as **met / partial / missing**, citing profile evidence:
   - **met** — clear evidence in the resume; **partial** — adjacent/transferable experience, or only
     part of a compound requirement is shown; **missing** — no evidence. Don't credit skills not shown.
   - **Match semantically, not literally** (the shared engine — [`../../knowledge/relevance.md`](../../knowledge/relevance.md)):
     credit a skill demonstrated under a *different name* (a "Visual AI agent" shows computer vision;
     "ran paid campaigns" shows performance marketing; "RAG" ≈ retrieval-augmented). Literal keyword
     absence is **not** the same as missing evidence. But never credit `[VERIFY]` facts — not even as transferable.
   - **"X OR Y" requirements** — satisfied if the profile has *either*. Never penalize for lacking the
     other half of an OR.
   - **Ambiguous / underspecified JDs** — score conservatively, note the ambiguity in `gaps`, and don't
     inflate must-haves. Lower confidence rather than guessing high.
   - Mark `is_dealbreaker: true` for must-haves whose absence alone should drive a Skip.

3. **Keyword coverage**: list keywords present in the profile (`matched_keywords`) vs. missing ones an
   ATS would screen on (`missing_keywords`). Keep `missing_keywords` to terms the resume could
   *honestly* incorporate — this list feeds `tailor-resume`.

4. **Score 0–100** using this weighting (adjust slightly per role) — these are the `subscores`:
   - Must-have requirements met — 45
   - Seniority & scope match — 20
   - Domain/industry relevance — 15
   - Keyword/skills coverage — 15
   - Location / remote / work-auth fit — 5

   Then subtract itemized **penalties** for hard-constraint violations (onsite when remote-only;
   sponsorship not offered when needed per §0; comp clearly below `min_base_salary`). The final
   `score` = sum(subscores) + sum(penalties), clamped to 0–100. (Subscores still sum to 100 — the
   factor weights mirror [`../../knowledge/relevance.md`](../../knowledge/relevance.md), so this
   `score` stays directionally consistent with find-jobs `fit_rank`.)

5. **Goal alignment (directional — not a subscore).** Read `context.career_goal` to judge whether
   this role *advances the candidate's stated direction*; set `goal_alignment` ∈ `strong|neutral|weak`.
   It **breaks ties / nudges the `recommendation`** (e.g. a borderline 70 that strongly serves the goal
   → "apply"; one that pulls away → "apply_if_tailored"). It is **never a numeric subscore** (preserves
   the 100-point sum) and is **never quoted, paraphrased, or echoed** into any output (RULES.md §2) —
   it directs the verdict, it does not appear in it.

## Output

### Human-readable (always)
- **Score: NN/100** + one-line verdict.
- **Recommendation: Apply / Apply if tailored / Skip** — with the single biggest reason.
- **Strengths** (3–5 bullets) — citing profile evidence.
- **Gaps / risks** (3–5 bullets) — missing must-haves or weak areas; note dealbreakers vs. addressable.
- **Missing keywords** — comma list the resume should incorporate (feeds `tailor-resume`).
- If recommending Apply, suggest `/tailor-resume` for this job.

### Structured sidecar (gated)
When the job has an `id` (from `jobs/found-<date>.json`) **or** score-fit runs inside a pipeline,
also write `scores/<job-id>.score.json` per [reference/score-schema.md](reference/score-schema.md)
(`subscores` must sum to the pre-penalty total). For one-off pasted JDs, skip the file unless asked.

Be honest — a low score is more useful than a flattering one. No emoji.

## Next steps
Apply / Apply-if-tailored → `/tailor-resume` for this job (or `/apply-to-job` to assemble the whole package). Skip → move to the next job.
