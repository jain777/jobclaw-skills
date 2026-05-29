# score-fit structured output (sidecar)

`score-fit` always prints a human-readable verdict. When a job has a stable `id` (it came from
`jobs/found-<date>.json`) or score-fit is invoked inside a pipeline (by `find-jobs` or
`tailor-resume`), it **also** writes a machine-readable sidecar so downstream skills consume the
result without re-parsing prose. Pure pasted-JD scoring stays human-readable-only unless the user
asks for the file.

**Path:** `scores/<job-id>.score.json` (create `scores/` if needed). For pasted jobs with no id,
use a slug like `<company>-<role-slug>` and tell the user where it was written.

## Schema

```jsonc
{
  "job": { "id": "...", "company": "...", "role": "...", "url": "..." },
  "scored_at": "YYYY-MM-DD",
  "profile_path": "profile/master-profile.md",
  "score": 0,                         // 0–100, = sum(subscores) − hard-constraint penalties
  "subscores": {                      // mirror the rubric weights exactly
    "must_haves": 0,                  // /45
    "seniority": 0,                   // /20
    "domain": 0,                      // /15
    "keywords": 0,                    // /15
    "location_work_auth": 0           // /5
  },
  "penalties": [                      // hard-constraint deductions, itemized
    { "reason": "onsite role, profile is remote-only", "points": -10 }
  ],
  "recommendation": "apply | apply_if_tailored | skip",
  "requirements": [                   // every must-have / nice-to-have, graded
    {
      "text": "5+ years product management",
      "kind": "must | nice",
      "status": "met | partial | missing",
      "evidence": "3 yrs PM + 2 yrs APM at ...",   // cite profile; empty if missing
      "is_dealbreaker": false
    }
  ],
  "matched_keywords": ["..."],        // present in the profile
  "missing_keywords": ["..."],        // an ATS would screen on these — feeds tailor-resume
  "strengths": ["..."],
  "gaps": ["..."],
  "work_auth_verdict": "non_issue | minor_note | major_filter | disqualifier",
  "profile_stale": false,             // true if [VERIFY] fields or staleness affected scoring
  "profile_missing": false            // true if scored against a pasted snippet, no master profile
}
```

## Rules
- `subscores` must sum to the pre-penalty total; `score = sum(subscores) + sum(penalties.points)`,
  clamped to `[0, 100]`.
- `requirements[].status`: **met** = clear profile evidence; **partial** = adjacent/transferable or
  only some of a compound requirement; **missing** = no evidence. Never credit `[VERIFY]` facts as met.
- `missing_keywords` is the contract `tailor-resume` reads (its SKILL.md reuses this list). Keep it
  to keywords the resume could honestly incorporate — not aspirational skills the candidate lacks.
- `work_auth_verdict` comes from `knowledge/work-authorization.md` applied to the **job's** region.
