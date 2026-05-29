---
# --- Identity ---
name: Jane Doe
title: Senior Product Manager
location: New York, NY
region: US
timezone: America/New_York
years_exp: 7
work_auth: US citizen            # e.g. US citizen / Green card / H-1B / needs sponsorship
open_to_relocation: false
remote_pref: hybrid              # remote / hybrid / onsite / any

# --- Links — populate everything you have. Unknown networks go under `other:`. ---
links:
  email: jane@example.com
  phone: "+1 555 0100"
  linkedin: https://linkedin.com/in/janedoe
  github: https://github.com/janedoe
  portfolio: https://janedoe.com
  website: ""
  twitter: https://x.com/janedoe
  scholar: ""
  orcid: ""
  huggingface: ""
  kaggle: ""
  medium: https://medium.com/@janedoe
  substack: ""
  dribbble: ""
  behance: ""
  stackoverflow: ""
  bluesky: ""
  mastodon: ""
  youtube: ""
  blog: ""
  calendar: ""
  dev_to: ""
  other:
    speakerdeck: https://speakerdeck.com/janedoe
    talks: https://janedoe.com/talks

# Optional: explicit ordering for the rendered contact line.
# If absent, render-resume uses the track preset's contact_order_default.
contact_priority: [email, phone, linkedin, github, portfolio, medium]

# --- What she's targeting (read by find-jobs & score-fit) ---
target:
  tracks: [product]             # product | software | finance | quant | marketing | founders-office | hr
  regions: [US]                 # where she's hunting
  roles: ["Senior Product Manager", "Group PM", "Principal PM"]
  locations: ["New York, NY", "Remote (US)"]
  remote_only: false
  min_base_salary: 180000
  seniority: senior             # junior | mid | senior | staff | lead | exec
  industries: ["fintech", "developer tools", "AI"]
  company_size: ["startup", "growth", "midsize"]
  exclude_companies: []

# --- Application autonomy hints (used later by JobClaw) ---
preferences:
  needs_sponsorship: false
  willing_to_travel: "up to 25%"
  earliest_start: "2 weeks notice"

# --- CONTEXT-ONLY — never rendered in PDFs, cover letters, or outreach.
# Read by find-jobs (tie-break), score-fit (goal-alignment sub-score),
# tailor-resume (bias Summary direction without quoting), career-coach.
context:
  career_goal: |
    Looking to lead an API/platform product at a developer-tools or AI-infra
    company over the next 12–18 months. Want scope that combines DX, pricing
    & packaging, and platform extensibility. Prefer growth-stage (Series B–D)
    over big-tech; willing to be a Group PM if the org has real platform
    surface area.
  additional_info: |
    Open to onsite NYC, hybrid 3 days, or fully remote — not relocating.
    Partner's medical residency runs through 2027, so geo is fixed.
---

## Summary

Product leader with 7 years building fintech and developer-tools products. Took two 0→1 products to $10M+ ARR; led teams of 6–10 across PM, design, and eng. Strong on developer experience, payments, and AI-assisted workflows.

## Experience

### Stripe — Senior Product Manager (2021–present)
- Led the developer onboarding product; cut time-to-first-API-call by 40% (12 min → 7 min).
- Shipped a usage-based billing self-serve flow that drove $14M incremental ARR.
- Managed 3 PMs; ran the quarterly roadmap for a 25-person product group.

### Plaid — Product Manager (2018–2021)
- Owned the identity-verification API; grew adoption from 200 → 1,400 active integrations.
- Defined the data-access consent flow now used by 80% of partners.

## Education
- B.S. Computer Science, Carnegie Mellon University (2014–2018)

## Skills
- Product: roadmapping, discovery, experimentation, pricing & packaging, PRDs
- Technical: SQL, API design literacy, A/B testing, basic Python
- Domains: payments, fintech compliance, developer tools, AI/LLM products

## Projects
- **OpenLedger** (side project) — open-source double-entry ledger library, 2.1k GitHub stars.

## Achievements
- Speaker, Fintech Devcon 2023 — "Designing APIs developers love."

## Notes / voice
- Prefers concise, metric-led writing. Avoids buzzwords. First-person, confident but not boastful.
- Hard constraints: no relocation; will not consider non-remote roles outside NYC.
