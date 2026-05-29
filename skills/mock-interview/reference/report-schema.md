# mock-interview report schema

The structured report `mock-interview` writes to `interviews/<slug>-<YYYY-MM-DD>.report.json` after a session. Ported from the original platform's mock-interview report shape, with two tightening rules and one extension.

## Schema

```jsonc
{
  "session": {
    "company": "string | null",         // null for role-only mocks
    "role": "string",
    "date": "YYYY-MM-DD",
    "rounds": ["string"],               // e.g. ["behavioral","system-design"]
    "difficulty": "easy | medium | hard",
    "duration_minutes": "number"
  },

  "overallScore": "number — 1.0–10.0, one decimal",
  "strengths": [                        // 3–5 bullets, profile-grounded
    "string"
  ],
  "improvements": [                     // 3–5 bullets, specific + actionable
    "string"
  ],

  "questions": [
    {
      "id": "number — 1-indexed in ask order",
      "question": "string — exact text asked",
      "userAnswer": "string — verbatim user response; empty string if skipped",
      "aiFeedback": "string — 1–3 sentences; what was strong / what to add / how to structure",
      "score": "number — 0–10 integer",
      "round": "string — one of session.rounds"
    }
  ],

  "next_steps": [                       // optional, 0–3 bullets — what to drill next
    "string"
  ]
}
```

## Rules

1. **Unanswered question → `score: 0`.** If `userAnswer` is empty (user said `/skip`, gave a non-answer like "I don't know", or ran out of time), `score` is **0** — not 1, not null. This matches the Go original (`handlers.go` rule, line 617) and prevents the report from flattering silence.

2. **Score range is 0–10 integer** for per-question scores; `overallScore` is a 1.0–10.0 float with one decimal. The Go original used 1–10 integer for both; the float on overall is the only tightening, so a session of 6×7 and 1×9 doesn't collapse to a flat 7.

3. **No fabricated quotes.** `userAnswer` is the user's words verbatim (preserve typos / fillers — they're signal). `aiFeedback` may paraphrase the user's answer in commentary but must not invent things the user did not say.

## Strength / improvement bullets — style

- **Specific, not generic.** Bad: "good communicator." Good: "answered the system-design question by leading with the read/write ratio — strong instinct that anchored the rest of the design."
- **Cite the question** by id where relevant: *(Q3)*.
- **Improvements are actionable** — they tell the user what to *do* next time, not just what was missing.
- Apply [`../../_shared/RULES.md`](../../_shared/RULES.md) — never fabricate user experience the answers don't show.

## Session metadata

`session.rounds` should be drawn from the track-typical loop (see `build-profile/reference/track-presets.md`):
- `software` — coding · system-design · behavioral
- `product` — product-sense · execution · strategy · behavioral
- `quant` — math-stats · research · coding · behavioral
- `finance` — technical · case · fit
- `marketing` — case · craft · behavioral
- `founders-office` — case · ops · behavioral
- `hr` — case · craft · behavioral
- `design` — portfolio-review · whiteboard/app-critique · behavioral
- `data` — coding/SQL · ML/stats · case · behavioral
- `sales` — discovery/role-play · pitch/demo · behavioral
- `operations` — case · execution · behavioral
- `customer-success` — scenario/role-play · case · behavioral
- `content` — portfolio/clips-review · writing-exercise · behavioral

If the session covered rounds outside the track default, list them as-given; don't normalize away the user's choice.

## Versioning

If this schema changes, bump a `schema_version` field at the root (omitted in v0 = implicit `1`). An optional agent can persist these reports in a tracker; a stable schema is the contract.
