# Master profile schema

`profile/master-profile.md` = **YAML frontmatter** (structured, machine-read for form-filling & search) + **markdown body** (narrative, human- and Claude-read). See `profile/master-profile.example.md` for a filled example.

## Frontmatter (required block)

```yaml
# Identity
name: string
title: string                 # current/most-recent title
location: string              # "City, ST"
region: string                # region code: US | IN | ... → selects knowledge/regions/<code>.md (infer from location)
timezone: string              # IANA, optional
years_exp: number
work_auth: string             # enum from ../../../knowledge/work-authorization.md:
                              # US citizen | Green card | H-1B | OPT/CPT (F-1) | TN |
                              # Indian citizen/OCI | needs sponsorship | other
open_to_relocation: boolean
remote_pref: remote|hybrid|onsite|any

# Links — extensible. All keys optional; populate whatever build-profile extracts
# or the user provides. Unknown networks live under `other:`.
links:
  # Always-prompted basics
  email: string
  phone: string
  # Canonical well-known keys (kept as named fields so track-presets can target them)
  linkedin: string            # URL only — never scraped
  github: string
  portfolio: string
  website: string
  twitter: string             # X/Twitter
  scholar: string             # Google Scholar
  orcid: string
  huggingface: string
  kaggle: string
  medium: string
  substack: string
  dribbble: string
  behance: string
  stackoverflow: string
  bluesky: string
  mastodon: string
  youtube: string
  blog: string                # generic personal blog
  calendar: string            # Cal.com / Calendly / scheduling link
  dev_to: string
  # Escape hatch for anything else (LeetCode, Patents, Awwwards, a custom domain, ...)
  other:
    <freeform_label>: <url>   # e.g. leetcode: "https://leetcode.com/u/..."

# Optional: per-user override for the rendered contact-line ordering.
# Precedence: sidecar contact_order > this > track default (render-resume/templates/_common.py:
# DEFAULT_CONTACT_ORDER_BY_TRACK) > fallback. Omit unless the user has a clear preference.
contact_priority: [email, phone, linkedin, github, portfolio]

# Target — READ BY find-jobs AND score-fit (keep accurate)
target:
  tracks: [product|software|finance|quant|marketing|founders-office|hr|design|data|sales|operations|customer-success|content]
  regions: [US|IN|...]        # where you're hunting (may differ from your region)
  roles: [string]             # titles to search for
  locations: [string]
  remote_only: boolean
  min_base_salary: number     # in local currency, annual
  seniority: junior|mid|senior|staff|lead|exec
  industries: [string]
  company_size: [startup|growth|midsize|enterprise]
  exclude_companies: [string]

# Application hints (used later by JobClaw)
preferences:
  needs_sponsorship: boolean
  willing_to_travel: string
  earliest_start: string
  # India-relevant — collect when region/target includes IN (see knowledge/regions/india.md):
  current_ctc: string         # e.g. "₹28 LPA"
  expected_ctc: string        # e.g. "₹40 LPA"
  notice_period: string       # e.g. "60 days"

# CONTEXT-ONLY — never rendered in PDFs, cover letters, outreach, or any external message.
# Read by find-jobs (rank ties), score-fit (goal-alignment sub-score), tailor-resume
# (bias Summary direction without quoting), and career-coach. Renderers skip both.
context:
  career_goal: |              # ≤ 600 chars (~100 words). First-person; what you're
                              # optimizing for over the next 12–24 months and why.
                              # Mention domains/role types/tradeoffs; avoid naming
                              # specific target companies unless they're hard targets.
  additional_info: |          # ≤ 400 chars. Soft constraints / context the resume should NOT
                              # show (e.g. "spouse in healthcare, geo flexibility limited",
                              # "exploring a masters in 2027", "optimizing for sane hours").
```

## Body (markdown sections, in this order)

- `## Summary` — 2–4 sentence positioning, metric-led.
- `## Experience` — `### Company — Title (start–end)` then 2–4 quantified bullets each.
- `## Education`
- `## Skills` — grouped (technical / domain / track-specific).
- `## Projects` — name, one line, link.
- `## Achievements` — awards, talks, publications.
- `## Certifications` / `## Languages` — if any.
- `## Notes / voice` — writing tone, things to avoid, **hard constraints** (relocation, sponsorship, comp floor). Downstream skills read this.

## Rules
- Unknown → empty/omit; uncertain → inline `[VERIFY]`.
- No fabrication of roles, dates, or metrics.
- Frontmatter `target.*` and the Notes constraints are the most load-bearing fields for the rest of the system — get them right.
- `region` / `target.regions` select the geographic knowledge pack (`knowledge/regions/`) every downstream skill applies (sources, sponsorship logic, resume conventions). Set them from the user's location and where they're hunting.
- **`links:` is extensible** — populate every link the user has, including ones in `links.other`. Track presets (`reference/track-presets.md`) decide which canonical keys `build-profile` insists on prompting for vs. lets pass.
- **`context.career_goal` and `context.additional_info` are context-only.** Downstream skills read them to bias direction; renderers (`render-resume`, cover-letter, outreach) MUST NOT quote, paraphrase, or echo their contents into any external artifact.
