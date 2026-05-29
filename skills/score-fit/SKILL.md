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
2. The job: a pasted description, a URL to fetch, or an entry from `jobs/found-<date>.json` (ask which if unclear).

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
     and `must_haves` sub-scores toward that archetype's proof points, and note the archetype in
     `strengths`/`gaps`. Distinguish genuine AI roles from "AI" used only as a buzzword (title filter
     in ai-roles.md).

2. **Grade each requirement** as **met / partial / missing**, citing profile evidence:
   - **met** — clear evidence in the resume; **partial** — adjacent/transferable experience, or only
     part of a compound requirement is shown; **missing** — no evidence. Don't credit skills not shown.
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
   `score` = sum(subscores) + sum(penalties), clamped to 0–100.

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
