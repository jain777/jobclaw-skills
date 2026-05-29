# Test fixtures

Real-shaped inputs for validating Batch 2 + 3 skills (and useful for Batch 1 too). Each fixture includes an `_expected` block — the result `triage-inbox` / `infer-status` / `coach-negotiation` should produce — so a smoke run can self-check.

## Layout
- `emails/` — 12 recruiter emails covering all 10 taxonomy classes + 2 ambiguous edge cases (`triage-inbox`, `infer-status`, `draft-reply`).
- `offers/` — 2 offer specs, one US and one IN (`coach-negotiation`).

## Email coverage
| File | Class | Notes |
|---|---|---|
| `emails/01-rejection.json` | `rejection` | clean US-style rejection |
| `emails/02-screen.json` | `screen` | recruiter screen with 3 proposed time slots (Pacific) |
| `emails/03-interview-invite.json` | `interview-invite` | technical round; asks for windows |
| `emails/04-assessment.json` | `assessment` | take-home with 5-day deadline → `priority: urgent` |
| `emails/05-offer.json` | `offer` | US offer w/ base + equity + bonus + signing |
| `emails/06-recruiter-outbound.json` | `recruiter-outbound` | cold inbound, no prior application |
| `emails/07-info.json` | `info` | auto-confirmation ("we received your application") |
| `emails/08-request-info.json` | `request-info` | India recruiter asking CTC + notice + relocation |
| `emails/09-spam.json` | `spam` | obvious phishing |
| `emails/10-other.json` | `other` | multi-intent: outbound + referral ask + post-event follow-up → `escalate` |
| `emails/11-ambiguous-screen-vs-info.json` | `info` (NOT `screen`) | positive tone, no time asked, no action — naive classifier fail |
| `emails/12-rejection-soft.json` | `rejection` | very polite phrasing ("impressed", "stay in touch") — naive classifier fail |

11 & 12 are the **classification-stress cases** — `triage-inbox` must not be fooled.

## Offer coverage
| File | Region | Structure |
|---|---|---|
| `offers/offer-mercury-us.json` | US | base + equity (ISOs/4y/1y-cliff) + bonus + signing |
| `offers/offer-meesho-india.json` | IN | CTC LPA (fixed + variable + ESOPs + retention) + notice period |

## How to use

**Smoke-test `triage-inbox`** against the 12 emails — compare your output's `class` + `suggested_action` to each fixture's `_expected`. All 12 must match, including the 2 ambiguous ones.

**Smoke-test `infer-status`** by composing `(triage_class × current_status)` tuples from the email fixtures and verifying the decision-table transitions.

**Smoke-test `coach-negotiation`** by passing each offer JSON and a profile → strategy + counter email; check that the counter never auto-sends, ranges cite a source, and the IN offer uses LPA structure (not USD).

Fixtures are gitignored by default; remove `tests/` from the repo `.gitignore` if you want them tracked.
