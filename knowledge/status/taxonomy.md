# Status taxonomy

Canonical enums + decision table for the recruiter loop. `triage-inbox`, `infer-status`, and `draft-reply` all consume this file — they do not re-derive these values.

## Email class (10)

What each inbound email **is**. Mutually exclusive; pick the most specific match. `triage-inbox` emits one of these per email.

| class | meaning | typical signals |
|---|---|---|
| `rejection` | application is closed out, regardless of reason or phrasing. | "unfortunately", "not moving forward", "after careful consideration" |
| `screen` | a recruiter wants an initial conversation (call, video, intake). | "30-minute chat", "recruiter screen", proposing call times |
| `interview-invite` | an interview round (after screen) is being scheduled. | "next round", "technical interview", "with the hiring manager / panel" |
| `assessment` | a take-home / OA / coding test is being requested. | "complete this assessment", HackerRank/CoderPad/Karat link, 48-hour window |
| `offer` | a formal or informal offer is being extended (or a verbal offer email). | "offer letter", "we'd like to extend", base / equity / start-date language |
| `recruiter-outbound` | unsolicited cold inbound from an external/internal recruiter — *no prior application by the user*. | "came across your profile", "would you be open" |
| `info` | acknowledgement / auto-confirmation / status update with no action required. | "we received your application", "we are reviewing", "thank you for applying" |
| `request-info` | recruiter is asking the candidate for something — CTC, notice, availability, updated CV, work auth. | "could you share your expected CTC", "please send notice period" |
| `spam` | not a real recruiting email; not relevant to the user's job hunt. | mass blasts, irrelevant industries, obvious phishing |
| `other` | doesn't fit cleanly — flag for human review. | ambiguous, multi-intent, unclear sender |

## Application status (10)

The **canonical state of one application**. `infer-status` emits one of these. Ordered roughly by funnel position; `accepted`/`rejected`/`withdrawn`/`ghosted` are terminal.

| status | meaning |
|---|---|
| `applied` | user submitted; no contact yet. |
| `screening` | recruiter screen in flight or scheduled. |
| `assessment` | take-home / OA in flight. |
| `interview` | technical / hiring-manager interviews in flight. |
| `final-round` | onsite / superday / leadership round. |
| `offer` | offer extended; not yet accepted/declined. |
| `accepted` | offer accepted (terminal). |
| `rejected` | rejected by employer (terminal). |
| `withdrawn` | user withdrew (terminal). |
| `ghosted` | non-terminal status with no contact for ≥ 14 days (terminal-ish; treat as soft close). |

## Suggested action (9)

What `triage-inbox` recommends and `draft-reply` uses as its `intent`. Each maps to one reply template (or none).

| action | meaning | who consumes |
|---|---|---|
| `reply-schedule` | propose / accept times for a screen or interview. | `draft-reply` |
| `reply-accept` | accept a scheduling, an assessment, or an offer (each has a distinct template — see `draft-reply`). | `draft-reply` |
| `reply-decline` | politely decline (graceful, door open). | `draft-reply` |
| `reply-ask` | ask 1 specific clarifying question. | `draft-reply` |
| `reply-info` | provide requested data (CTC, notice, availability, updated CV). | `draft-reply` |
| `acknowledge` | log the email; no reply needed but record the interaction. | tracker only |
| `ignore` | spam or irrelevant — drop. | tracker only |
| `escalate` | low-confidence triage or `other` class — human review. | `request-human-input` (later) |
| `follow-up` | proactive nudge after silence (set by `infer-status` ghost rule, not by triage). | `draft-reply` |

## Decision table — (email-class × current-status) → (next-status, suggested-action)

Read in priority order: terminal email classes (rejection, offer) trump status; `info`/`request-info`/`spam` never change status. Where the table says "**no change**" for next-status, retain the existing status; only the action moves.

| email-class \ current-status | `applied` / `screening` | `assessment` / `interview` / `final-round` | `offer` | terminal (`accepted`/`rejected`/`withdrawn`/`ghosted`) |
|---|---|---|---|---|
| `rejection` | → `rejected`, **acknowledge** | → `rejected`, **acknowledge** | → `rejected`, **acknowledge** *(rare: rescinded offer)* | no change, **ignore** |
| `screen` | → `screening`, **reply-schedule** (or **reply-ask** if no times proposed) | no change, **reply-ask** *(new contact mid-loop is unusual; clarify)* | no change, **reply-ask** | no change, **ignore** |
| `interview-invite` | → `interview`, **reply-schedule** | → `final-round` (if current was `interview`) else no change, **reply-schedule** | no change, **reply-ask** | no change, **ignore** |
| `assessment` | → `assessment`, **reply-accept** (acknowledge + commit) | no change *(coupled to a round)*, **acknowledge** | no change, **reply-ask** | no change, **ignore** |
| `offer` | → `offer`, **reply-ask** *(do NOT auto-accept; suggest `/coach-negotiation`)* | → `offer`, **reply-ask** | no change, **reply-ask** | no change, **ignore** |
| `recruiter-outbound` | — *(no record yet)* (action: assess fit; optionally **reply-info** with a soft yes/no) | n/a | n/a | n/a |
| `info` | no change, **acknowledge** | no change, **acknowledge** | no change, **acknowledge** | no change, **ignore** |
| `request-info` | no change, **reply-info** | no change, **reply-info** | no change, **reply-info** | no change, **ignore** |
| `spam` | no change, **ignore** | no change, **ignore** | no change, **ignore** | no change, **ignore** |
| `other` | no change, **escalate** | no change, **escalate** | no change, **escalate** | no change, **escalate** |

### Ghosting rule (overrides the table)

If the current status is **non-terminal** (`applied`/`screening`/`assessment`/`interview`/`final-round`/`offer`) **and** `days_since_last_contact ≥ 14`, set status → `ghosted`. Suggested action:
- `applied` / `screening` → **follow-up** (one polite nudge).
- `interview` / `final-round` / `offer` → **escalate** (something's wrong; human should reach in).

The threshold (14 days) is the default; `infer-status` accepts a `--ghost-days` override.

### Offer-accept guardrail

`offer` → `accepted` is **never** an automatic transition. Always require an explicit user instruction (`infer-status --confirm-accept`) before moving to `accepted`. The default action on an `offer` email is `reply-ask` (acknowledge + buy time + suggest `/coach-negotiation`).

## Extraction fields — what `triage-inbox` pulls per email

When the email class is one of `screen`, `interview-invite`, `assessment`, `offer`, `request-info`, `recruiter-outbound`, or `info` with concrete content, `triage-inbox` populates as many of these as the email genuinely provides. **Do not invent.** Missing values stay `null` / `[]`.

```jsonc
{
  "company": "string | null",
  "role": "string | null",
  "job_id": "string | null",              // ATS req id if findable in subject/body/link
  "dates": [                              // proposed slots, deadlines, start dates
    { "iso": "YYYY-MM-DD", "time": "HH:MM | null", "tz": "IANA | null", "label": "string" }
  ],
  "links": [                              // scheduling, assessment, portal, calendly URLs
    { "url": "string", "kind": "schedule | assessment | portal | other" }
  ],
  "asks": ["string"],                     // verbatim recruiter asks ("send updated CV", "share notice period")
  "deadline": "YYYY-MM-DD | null",        // hard cutoff if explicit
  "sentiment": "neutral | positive | negative",
  "confidence": "high | medium | low"     // triage's own confidence; low → flagged
}
```

## How to add to this file

Adding a new email class, a new status, or a new action **must** update all three: the relevant enum table, the decision table cells, and the consuming skills' anti-patterns where they overlap. Don't add an action without a template path (or `tracker-only` / `escalate`) — orphan actions break `draft-reply`.
