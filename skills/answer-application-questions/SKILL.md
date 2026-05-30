---
name: answer-application-questions
description: >
  Answer one or many application-form questions from the master profile, obeying per-type
  format rules — numeric → number only, yes/no → Yes|No, short → ≤ 2 sentences,
  paragraph → ≤ max_chars, enum → one of options. Batch JSON in/out (for JobClaw form-fill);
  single-question paste mode for interactive use. Flags any question without profile
  evidence rather than fabricating an answer.
when_to_use: >
  Use whenever the user pastes a single application question OR passes a JSON form schema
  (typically scraped by JobClaw's Playwright). Pairs with scripts/answer.py for output
  validation.
user-invocable: true
allowed-tools: Read, Write, Bash
---

# answer-application-questions

Fill an application form from the master profile — **never invent**. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md). Paragraph answers reuse **Communication** verbs from [`../tailor-resume/reference/action-verbs.md`](../tailor-resume/reference/action-verbs.md).

## Inputs

**Known-info gate (RULES §6):** the `job` block (company/role/url) may be omitted — if absent, read
`jobs/current.json` for it. All answers source from `profile/master-profile.md`; never re-ask the user
for a fact (years_exp, work_auth, notice period, CTC) the profile already holds — flag a genuinely
missing one rather than asking mid-form.

### Batch mode (preferred for JobClaw / multi-question forms)
- `--in resumes/<slug>.app-questions.in.json`:
  ```jsonc
  {
    "job":    { "company": "...", "role": "...", "url": "..." },
    "region_hint": "US|IN",          // optional; else derive from job location / profile
    "questions": [
      { "id": "q1", "text": "Years of relevant experience?",           "type": "numeric" },
      { "id": "q2", "text": "Authorized to work without sponsorship?", "type": "yes_no"  },
      { "id": "q3", "text": "Notice period (in days)?",                "type": "short"   },
      { "id": "q4", "text": "Why this role?",                          "type": "paragraph", "max_chars": 600 },
      { "id": "q5", "text": "Work mode?", "type": "enum", "options": ["Remote", "Hybrid", "Onsite"] }
    ]
  }
  ```
- Profile = `profile/master-profile.md`.

### Single mode (paste a question, get an answer)
- Paste the question; the skill infers `type` and answers in markdown.

## Method

0. **Region pack.** Read `knowledge/regions/<code>.md` for phrasing — US: work-auth phrasing; IN: CTC / notice phrasing. For sponsorship verdicts specifically, defer to `knowledge/work-authorization.md` (judged against the **job's** region).

1. **Read profile** — `preferences.*` (notice_period, current_ctc, expected_ctc, willing_to_travel, earliest_start, needs_sponsorship), `work_auth`, `years_exp`, `target.*`, `Notes / voice`.

2. **For each question:**
   - If `type` not declared, classify (`numeric | yes_no | short | paragraph | enum`).
   - Find profile evidence; record `source_field` as a dot-path or YAML key (e.g. `preferences.notice_period`).
   - Apply format rules **strictly**:
     - `numeric` → number only; carry units in a separate `unit` field if needed (no currency / units inside the value).
     - `yes_no` → exactly `Yes` or `No`. No "Yes, because…" — that's a `short`.
     - `short` → ≤ 2 sentences, ≤ 240 chars.
     - `paragraph` → ≤ `max_chars` (default 600). Structure: hook → proof → close.
     - `enum` → one of `options`. If none fit, flag.
   - Assign `confidence`: `high` (direct profile match) · `medium` (inference required) · `low` (best guess; you should usually flag instead).

3. **No evidence?** **Do not invent.** Emit a `flagged` entry `{ id, reason }`. This is the bridge to `request-human-input` (the optional JobClaw agent).

4. **Validate.** Run `python3 scripts/answer.py --validate-pair <in.json> <out.json>` — it checks completeness, types, lengths, and that every `answer` has a `source_field`. Re-draft if validation fails.

## Output

### Batch mode → `resumes/<slug>.app-questions.out.json`
```jsonc
{
  "answers": [
    { "id": "q1", "value": "7",   "confidence": "high",   "source_field": "years_exp" },
    { "id": "q2", "value": "Yes", "confidence": "high",   "source_field": "work_auth + region.work-auth-table" },
    { "id": "q3", "value": "60",  "unit": "days",         "confidence": "high",   "source_field": "preferences.notice_period" },
    { "id": "q4", "value": "…",   "confidence": "medium", "source_field": "summary + experience[0]" }
  ],
  "flagged": [
    { "id": "qN", "reason": "no profile evidence; needs human input" }
  ]
}
```
Plus a tight stdout table summarizing per-question status.

### Single mode
Markdown answer + a one-line `source_field` citation.

## Anti-patterns
- Padding numeric values with currency / units inside the value.
- Long explanations attached to `yes_no` answers.
- Inventing CTC, notice period, years of experience, certifications, work auth.
- Using `context.career_goal` verbatim as the "Why this role?" paragraph (paraphrase your own reasoning from `target.*` + experience).
- Answering a `paragraph` question with a wall of text.
- Emoji.

## Rubric
- [ ] 100% of `answers` have a non-empty `source_field`.
- [ ] Format rules strictly obeyed; `scripts/answer.py --validate-pair` passes.
- [ ] `flagged.length` = number of genuinely-unanswerable questions (the human-input queue).
- [ ] No invented numbers / dates / certifications.
- [ ] Sponsorship verdict derived from `work_auth` × **job's** region pack (not the applicant's region).

## Next steps
Answers ready. Submit the application, then `/infer-status` to log it.
