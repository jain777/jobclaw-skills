# Status knowledge

Shared canonical enums + decision table for **email triage**, **application-status inference**, and **reply intent**. Sibling pattern to [`../regions/`](../regions/), [`../work-authorization.md`](../work-authorization.md), and [`../companies/`](../companies/).

## Who reads this
| Skill | Uses it for |
|---|---|
| `triage-inbox` | the email-class enum + extraction-fields list (what to pull from each email) |
| `infer-status` | the application-status enum + the (email-class × current-status) → (next-status, action) decision table |
| `draft-reply` | the suggested-action enum (which intent template to fill — `reply-schedule`, `reply-accept`, …) |

## File
- [`taxonomy.md`](taxonomy.md) — the enums, the decision table, and the extraction fields. Single source of truth; the three consuming skills reference it, never re-derive.
