# Region pack schema

Every `knowledge/regions/<code>.md` follows this structure. Keep rules **explicit and actionable** — skills apply them directly.

```
# <Country> (<CODE>)

## Meta
- code, name, currency, currency_format (how comp is written), date_format, english_variant, timezone(s)

## Job sources (ranked)
A ranked list of where roles live in this region, each tagged with how JobClaw reaches it:
  - [api] free/structured (an adapter exists or is trivial)
  - [user-session] only via the user's own logged-in browser (ToS-sensitive) — JobClaw-side, conservative
  - [manual] no automation path yet; user pastes / future adapter
Note which `find-jobs` adapters apply and any country params (e.g., Adzuna country code).

## Work authorization & sponsorship
- Link to `../work-authorization.md` for the canonical `work_auth` enum, the cross-region
  resolution rule (judge against the **job's** region), and the effect verbs
  (NON-ISSUE / MINOR-NOTE / MAJOR-FILTER / DISQUALIFIER). This section holds only the
  country-specific *rows*.
- DECISION RULES as a table: (applicant authorization) × (job country = this region) → effect verb.
- The key local norm (e.g., "local employers assume you're already authorized; sponsorship is a disqualifier if you need it").

## Resume conventions
- Length; sections expected; **what to OMIT**; personal fields (photo/DOB/marital/etc.) with a modern-vs-traditional note; region-specific fields (e.g., CTC, notice period); date format; spelling variant; file format preferences.

## Compensation norms
- Unit & format (e.g., USD annual base+equity vs INR LPA CTC fixed+variable); whether current/expected pay is asked up front; negotiation norms.

## Application norms
- Cover letter prevalence; notice-period expectations; referral culture; portal quirks.

## Decision rules (consumed by skills)
A short, numbered list of imperative rules each skill should apply for this region. This is the part skills act on.
```
