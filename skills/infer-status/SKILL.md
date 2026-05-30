---
name: infer-status
description: >
  Resolve the canonical application status from signals (triage class + current status +
  days-since-apply / days-since-last-contact + optional portal state) using the taxonomy
  decision table. Emits {status, next_action, next_action_due_on, rationale}; optionally
  updates a flat tracker.json. Honours the offer-accept guardrail and the ghosting rule.
when_to_use: >
  Use after triage-inbox classifies new emails, before draft-reply chooses an intent
  template, or any time the user wants to refresh the funnel state for one or many
  applications.
user-invocable: true
allowed-tools: Read, Write
---

# infer-status

Map signals → status using the **taxonomy decision table** — no invention. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md). All enums, the decision table, the ghosting rule, and the offer-accept guardrail live in [`../../knowledge/status/taxonomy.md`](../../knowledge/status/taxonomy.md).

## Inputs

### Per-application signals (JSON; single or array)
```jsonc
{
  "job":                    { "company": "...", "role": "...", "job_id": "..." },
  "current_status":         "applied | screening | assessment | interview | final-round | offer | accepted | rejected | withdrawn | ghosted",
  "triage_class":           "rejection | screen | interview-invite | assessment | offer | recruiter-outbound | info | request-info | spam | other | null",
  "days_since_apply":       "number | null",
  "days_since_last_contact":"number | null",
  "portal_state":           "string | null",     // verbatim portal label if scraped, e.g. "Application Rejected"
  "as_of":                  "YYYY-MM-DD"
}
```

Or `--in inbox/triage-<date>.json` to read triage records directly; the skill joins triage → applications by `(company, role)` or `job_id` and pulls `current_status` from `tracker.json` if present.

### Flags
- `--ghost-days N` — override the 14-day ghosting threshold.
- `--update tracker.json` — write the new status back into `tracker.json` (only fields that changed).
- `--confirm-accept` — **the only way** to transition `offer → accepted`. Without it, an offer stays at `offer`.

## Method

0. **Read the taxonomy** decision table and the ghosting rule.

1. **Resolve `triage_class` if absent** by reading the latest `inbox/triage-<date>.json` for this job (if present). Otherwise skip the email branch and use only portal + recency signals.

2. **Apply the decision table.** `(triage_class × current_status) → (next_status, suggested_action)`. Terminal email classes (`rejection`, `offer`) trump current status; `info` / `request-info` / `spam` never change status.

3. **Override on portal signal** if present. Portal labels are ground truth when they exist (e.g., `portal_state: "Application Rejected"` → `rejected` regardless of email). Record the override in `rationale`.

4. **Apply the ghosting rule.** If current_status is non-terminal AND `days_since_last_contact ≥ ghost_days` (default 14): status → `ghosted`; action depends on funnel position (applied/screening → `follow-up`; interview/final-round/offer → `escalate`).

5. **Apply the offer-accept guardrail.** Never transition to `accepted` automatically. Without `--confirm-accept`, an `offer` stays at `offer` with action `reply-ask`. With `--confirm-accept` *and* current_status `offer`, transition to `accepted`.

6. **Compute `next_action_due_on`** based on the action:
   - `reply-schedule` / `reply-info` / `reply-ask` → today + 1 business day.
   - `reply-accept` (assessment) → respect the email's `deadline` if any, else +3 days.
   - `follow-up` → today + 0 (nudge now).
   - `acknowledge` / `ignore` → `null`.
   - `escalate` → today (route to `request-human-input` with the optional JobClaw agent).

7. **Write a rationale.** One sentence per non-trivial decision (which table row fired, what triggered the override, what the ghosting rule did).

## Output

### Per-application result
```jsonc
{
  "job":                  { "company": "...", "role": "...", "job_id": "..." },
  "prior_status":         "applied",
  "status":               "screening",
  "next_action":          "reply-schedule",
  "next_action_due_on":   "YYYY-MM-DD",
  "rationale":            "interview-invite × screening → final-round per taxonomy table; deadline 2026-06-02 noted",
  "as_of":                "YYYY-MM-DD"
}
```

Single input → object; batch input → array.

### Stdout
Tight table: `job · prior → next · action · due · rationale (truncated)`. Flag `escalate` rows + any status reverting (e.g., `interview → ghosted`).

### Optional tracker update
With `--update tracker.json`: read JSON `{applications: [{job_id, ...}]}`; merge new `status` / `next_action` / `next_action_due_on` / `last_status_change` into the matching record. Don't overwrite fields you didn't compute; preserve user notes.

## Anti-patterns
- Inventing a status from a noisy thread; default to `unchanged` + `acknowledge` when signals are weak.
- Treating `recruiter-outbound` (cold inbound, no prior application) as `screening`.
- Transitioning `offer → accepted` without `--confirm-accept`.
- Ignoring the portal signal when present.
- Using more than `--ghost-days` for the ghosting threshold without recording it in `rationale`.
- Emoji.

## Rubric
- [ ] Status ∈ taxonomy enum; action ∈ taxonomy action enum.
- [ ] `rationale` cites the table row or the override that fired.
- [ ] No `accepted` without `--confirm-accept` *and* a prior `offer`.
- [ ] `ghosted` only set when `days_since_last_contact ≥ ghost_days` AND current_status is non-terminal.
- [ ] `next_action_due_on` is set when `next_action` is reply-ish; `null` when not.

## Next steps
Status updated. Next: `/draft-reply` with the suggested intent (or `/coach-negotiation` if it's an offer).
