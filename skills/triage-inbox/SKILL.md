---
name: triage-inbox
description: >
  Classify a recruiting email (or a batch) into one of the 10 canonical email classes,
  extract structured fields (company / role / dates / links / asks / deadline / sentiment),
  and suggest the next action. Writes inbox/triage-<YYYY-MM-DD>.json — consumed by
  infer-status and draft-reply.
when_to_use: >
  Use when the user pastes one recruiter email OR JobClaw passes a batch from the
  AgentMail inbox. Front of the recruiter loop.
user-invocable: true
allowed-tools: Read, Write
---

# triage-inbox

Tell the user (or JobClaw) what each email **is** and what to do about it. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md). All enums, the decision table, the extraction-fields shape, and the suggested-action vocabulary live in [`../../knowledge/status/taxonomy.md`](../../knowledge/status/taxonomy.md) — read it first; don't re-derive.

## Inputs

### Single mode
- A pasted email: `from`, `subject`, `body`, optional `thread` (prior messages), optional `date`.

### Batch mode
- `--in inbox/incoming.json`:
  ```jsonc
  { "emails": [ { "email_id": "...", "from": "...", "subject": "...", "body": "...", "date": "YYYY-MM-DD", "thread": ["..."] } ] }
  ```

If the input has only a body (no from/subject), warn but proceed — class confidence will be `low` unless body is decisive.

## Method

0. **Read the taxonomy.** [`../../knowledge/status/taxonomy.md`](../../knowledge/status/taxonomy.md) — the 10 classes, the extraction-fields contract, the suggested-action vocab.

1. **For each email, classify** into exactly one class. Mutually exclusive; pick the most specific match (e.g., a "we received your application" auto-message is `info`, not `screen`; a take-home request is `assessment`, not `interview-invite`). Use the body + subject + sender domain together — sender alone is unreliable.

2. **Extract fields** per the taxonomy's `Extraction fields` block (only fields the email genuinely provides — never invent):
   - `company`, `role`, `job_id`
   - `dates[]` — proposed slots / deadlines / start dates (ISO + time + tz + label)
   - `links[]` — `{ url, kind ∈ schedule|assessment|portal|other }`
   - `asks[]` — verbatim recruiter asks ("send updated CV", "share notice period")
   - `deadline` — single hard cutoff if explicit
   - `sentiment ∈ {neutral, positive, negative}`
   - `confidence ∈ {high, medium, low}` — your own confidence in the classification

3. **Suggest one action** from the taxonomy's vocab (`reply-schedule | reply-accept | reply-decline | reply-ask | reply-info | acknowledge | ignore | escalate`). Map per the decision table; **always** suggest `escalate` for class `other` or any classification with `confidence: low`.

4. **Apply guardrails.**
   - `offer` emails → suggest `reply-ask` (acknowledge + buy time + recommend `/coach-negotiation`). **Never** suggest `reply-accept` directly.
   - `assessment` / `interview-invite` emails with a deadline within 48h → bump the email's `priority` field to `urgent` in the output (extension on the schema; downstream tooling can sort by it).
   - If the body looks like phishing (suspicious domain, prize wording, urgency + a link) → class `spam` regardless of subject.

## Output

### `inbox/triage-<YYYY-MM-DD>.json`
```jsonc
{
  "as_of": "YYYY-MM-DD",
  "triaged": [
    {
      "email_id": "...",
      "from": "...",
      "subject": "...",
      "class": "rejection | screen | interview-invite | assessment | offer | recruiter-outbound | info | request-info | spam | other",
      "extraction": {
        "company": "...", "role": "...", "job_id": "...",
        "dates": [...], "links": [...], "asks": [...],
        "deadline": "YYYY-MM-DD | null",
        "sentiment": "neutral | positive | negative",
        "confidence": "high | medium | low"
      },
      "suggested_action": "...",
      "priority": "normal | urgent",
      "notes": "string | null"
    }
  ]
}
```

### Stdout
A concise table per email: `id · class · company/role · action · priority · confidence`. Highlight `urgent` rows and any `escalate` rows for the user to review.

## Anti-patterns
- Treating "we received your application" as `screen` (it's `info`).
- Collapsing `screen` and `interview-invite` — they trigger different downstream actions.
- Inventing `job_id`, `dates`, or `company` not in the source text.
- Setting `confidence: high` on ambiguous emails just to clear the queue. Be honest — `low` is more useful.
- Suggesting `reply-accept` for an `offer` (must be `reply-ask` + recommend `/coach-negotiation`).
- Emoji.

## Rubric
- [ ] Class is one of the 10 taxonomy values, exactly.
- [ ] Every `extraction.*` field is sourced from the email (or `null`/`[]`).
- [ ] Suggested action is from the taxonomy vocab and consistent with the decision table.
- [ ] No `offer` is paired with `reply-accept`.
- [ ] `confidence: low` rows are flagged with `suggested_action: escalate`.
- [ ] Urgent items (assessment / interview-invite with ≤48h deadline) marked `priority: urgent`.

## Next steps
Triaged. Next: `/infer-status` to update the funnel, then `/draft-reply` for the suggested action.
