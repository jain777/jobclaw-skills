# research-company report schema

Written to `companies/<slug>.json`. The sibling `companies/<slug>.md` mirrors these sections in prose with a "Sources" footer. Consumed by `prep-interview` (jobSummary + news + red_flags) and `coach-negotiation` (compensation + news).

## Schema

```jsonc
{
  "companyName": "string",
  "role": "string | null",
  "as_of": "YYYY-MM-DD",                // when this brief was assembled

  "compensation": {
    "salaryBenchmarks": {
      "baseSalary":         "string | null",   // verbatim from a source, e.g. "$180k–$220k"
      "totalCompensation":  "string | null",   // e.g. "$280k–$380k incl. equity & bonus"
      "currency":           "USD | INR | ...",
      "level_context":      "string | null"    // e.g. "L5 / Sr. PM (levels.fyi)"
    },
    "benefitsOverview": ["string"]             // 0–8 bullets; verbatim themes from sources
  },

  "jobSummary": {
    "jobDescriptionSummary":     ["string"],   // 4–6 bullets — what the role does
    "dayToDayResponsibilities":  ["string"],   // 4–6 bullets — verbs / cadence
    "careerGrowthOpportunities": ["string"]    // 4–6 bullets — promotion paths, ladder
  },

  "news": {
    "recentNews": [
      { "title": "string", "summary": "string", "link": "string", "date": "YYYY-MM-DD | null", "source": "string" }
    ]
  },

  "discussions": {
    "reddit":    [{ "content": "string", "link": "string", "subreddit": "string", "date": "YYYY-MM-DD | null" }],
    "blind":     [{ "content": "string", "link": "string", "date": "YYYY-MM-DD | null" }],
    "glassdoor": [{ "content": "string", "link": "string", "rating": "number | null", "date": "YYYY-MM-DD | null" }]
  },

  "red_flags": [
    { "concern": "string", "source": "string", "link": "string" }
  ],

  "fit_for_user": [
    { "user_evidence": "string", "company_fact": "string", "tie": "string" }
  ],

  "sources": [                                  // every URL cited anywhere above, deduped
    { "url": "string", "kind": "comp | role | news | community | other" }
  ]
}
```

## Rules

1. **Verbatim comp.** `baseSalary` / `totalCompensation` are pulled from a source (levels.fyi range, Blind compsheet, posting). If no source is found, set to `null` — never invent.
2. **Cite everything.** Every content-bearing item has either a `link` field or its source URL in `sources[]`. The markdown sibling repeats links inline.
3. **Empty arrays, not placeholders.** Missing sections → `[]`, not `["No information found"]`.
4. **No `context:` echo.** `fit_for_user[].user_evidence` cites profile facts (experience bullets, skills, projects) — never quotes `context.career_goal` / `context.additional_info`.
5. **Time-bounded news.** Default last 12 months; older items only if topically necessary (founding, major legal/deal). Mark date when known.
6. **Sentiment balance.** Where both positive and negative exist on a platform, include both. Don't cherry-pick.

## Consumers

- `prep-interview` reads `jobSummary` (to ground likely-question generation) + `news.recentNews` (concrete recent moves the user should know) + `red_flags` (honest concerns to surface in the prep doc).
- `coach-negotiation` reads `compensation` (market-comp anchor for the range) + `news` (leverage signals — fundraise, layoffs, product wins) + region-pack comp norms.
- The the optional JobClaw agent reads `as_of` to decide whether to refresh.
