# JSON Resume intermediate

The structured form `render.py` consumes — a subset of the [JSON Resume](https://jsonresume.org) standard (so it interops with other tools) plus a few optional region/orchestration fields. Write it to `resumes/<name>.json`.

```jsonc
{
  "basics": {
    "name": "Jane Doe",
    "label": "Senior Product Manager — API & Platform",  // role-targeted subtitle
    "email": "jane@example.com",
    "phone": "+1 555 0100",
    "location": { "city": "New York", "region": "NY" },
    "summary": "Product leader with 7 years building API and developer-platform products in fintech...",
    "profiles": [
      // `network` is an OPEN string. Canonical keys (linkedin, github, portfolio,
      // website, twitter, scholar, orcid, huggingface, kaggle, medium, substack,
      // dribbble, behance, stackoverflow, bluesky, mastodon, youtube, blog,
      // calendar, dev_to) get track-aware ordering treatment; unknowns are
      // rendered after canonical ones in declared order.
      { "network": "linkedin",    "url": "https://linkedin.com/in/janedoe" },
      { "network": "github",      "url": "https://github.com/janedoe" },
      { "network": "portfolio",   "url": "https://janedoe.com" },
      { "network": "huggingface", "url": "https://huggingface.co/janedoe" }
    ],
    "other": {                                  // freeform map for anything else
      "speakerdeck": "https://speakerdeck.com/janedoe",
      "talks":       "https://janedoe.com/talks"
    }
  },
  "work": [
    {
      "company": "Stripe",
      "position": "Senior Product Manager",
      "startDate": "Apr 2021",
      "endDate": "Present",
      "location": "Remote",
      "highlights": [
        "Owned developer onboarding; cut time-to-first-API-call 40% (12->7 min).",
        "Shipped usage-based self-serve billing that drove $14M incremental ARR."
      ]
    }
  ],
  "education": [
    { "institution": "Carnegie Mellon University",
      "studyType": "B.S.", "area": "Computer Science",
      "startDate": "2014", "endDate": "2018", "score": "" }
  ],
  "skills": [
    { "name": "API & platform", "keywords": ["API product strategy", "developer experience", "pricing & packaging"] },
    { "name": "Fintech",        "keywords": ["payments", "identity", "compliance"] }
  ],
  "projects": [
    { "name": "OpenLedger", "description": "Open-source double-entry ledger library, 2.1k GitHub stars." }
  ],

  "meta": {
    "region": "US",                             // selects paper / date format
    "paper": "letter",                          // letter | a4
    "dateFormat": "Mon YYYY",
    "track": "product",                         // selects default contact ordering AND the track style preset (accent+font)
    "seniority": "senior",                      // optional, used by --theme auto
    "theme": "classic",                         // optional default rendercv theme (CLI --theme overrides)
    "accent_color": "rgb(140,30,62)",           // optional — overrides the track's default accent (rgb/hex/CSS name)
    "font_family": "Lato",                      // optional — overrides the track's default font (rendercv-bundled family)

    // Per-render overrides (typically set by tailor-resume's sidecar):
    "contact_order": ["email","phone","linkedin","github","portfolio","medium"],
    "contact_hidden": ["twitter"],
    "contact_priority": ["email","phone","linkedin","portfolio"],   // profile-level fallback

    // India-relevant — include only if the upstream content (region pack) calls for it:
    "noticePeriod": "",
    "currentCtc": "",
    "expectedCtc": ""
  }
}
```

## Field notes

- **`basics.profiles[].network`** is an OPEN string. `to_rendercv.py` maps each link: **known networks** (LinkedIn/GitHub/X/…) → rendercv's header `social_networks`; **portfolio/personal site** → `cv.website`; **everything else** (Medium, Substack, personal domains, anything whose username can't be cleanly extracted) → a body **"Links"** section. `email` / `phone` are separate rendercv header connections. Every link survives — there is no fixed set of seven.
- **`meta.contact_order`** comes from the tailor-resume sidecar (highest priority). If absent, **`meta.contact_priority`** from the profile is used. If both absent, the track default in `templates/_common.py DEFAULT_CONTACT_ORDER_BY_TRACK` applies. These order the `social_networks` / Links entries; email/phone/website *placement* is theme-controlled, not orderable.
- **`meta.contact_hidden`** lets `tailor-resume` suppress per-job links (e.g., drop X/Twitter for a finance role) without removing them from the master profile.
- **`meta.region` / `meta.paper`** select the page size (`US` → us-letter; `IN` → a4). `meta.dateFormat` is informational — rendercv controls date display itself; date strings are parsed to ISO (`Mon YYYY`/`YYYY` → `YYYY-MM`/`YYYY`), falling back to a freeform date label if unparseable.
- **`meta.noticePeriod`** / **`currentCtc`** / **`expectedCtc`** are India-relevant; include only when the region pack calls for them. They render as one-line entries in an "Additional" section. Omit empty fields in the render.
- **`basics.label`** is the role-targeted subtitle, aligned to the target role by `tailor-resume`. It becomes rendercv's `cv.headline` (rendered under the name); exact styling depends on the chosen theme.

## What this schema does NOT include

- **`context.career_goal`** and **`context.additional_info`** from the master profile — these are CONTEXT-ONLY and must never appear in the rendered output. The renderer ignores them by design.
- Any URL parsed back from the tailored markdown's contact line — the sidecar / profile is the only source of truth.
