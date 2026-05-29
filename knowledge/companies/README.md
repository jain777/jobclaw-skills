# Company list

A catalog of employers `find-jobs` sources from, spanning **all industries** (not just tech) for
each supported region. `find-jobs` filters it by the user's `target.regions` + `target.industries`,
resolves each company's board, and pulls listings.

## Files

- **`companies.csv`** — the canonical, machine-readable catalog (1000+ rows). One row per company
  per region. **This is the source of truth** — add a row and it's picked up; no code changes.
- **`resolved.json`** — machine-written cache mapping each company `key` → its verified board(s)
  and `fetchable` status. Written by `resolve_companies.py`; never hand-edited.
- **`SOURCES.md`** — where the rows come from (indices), the sector vocabulary, and the refresh policy.
- **`seed.md`** — a thin human-readable highlight of verified notable boards (the CSV supersedes the
  old full table).

## `companies.csv` schema

`key, name, region, sector, tracks, domain, careers_url, ats, token, source_index, notes`

| column | required | notes |
|---|---|---|
| `key` | yes | stable lowercase slug `[a-z0-9-]`, unique. Join key to `resolved.json`. |
| `name` | yes | display name. |
| `region` | yes | `US` or `IN` (region-pack code). Duplicate the company across rows if it hires in both. |
| `sector` | yes | one value from the controlled vocab in `SOURCES.md`. |
| `tracks` | no | finer comma-tags (`fintech,ai,devtools,...`); quote if it contains commas. |
| `domain` | yes | apex domain — used for token guessing + careers-page sniffing. |
| `careers_url` | no | careers page for the sniff path; blank → `https://<domain>/careers`. |
| `ats` | no | verified ATS if known (`greenhouse|lever|ashby|workday|smartrecruiters|icims|taleo|oracle|successfactors`); blank = resolve lazily. |
| `token` | no | verified board token/slug/CXS when `ats` is known. |
| `source_index` | no | provenance tag (see `SOURCES.md`). |
| `notes` | no | free text. |

## Resolving boards (the cache flow)

1. **Batch-resolve** the slice you need into the cache:
   `python3 ../../skills/find-jobs/scripts/resolve_companies.py --csv companies.csv --cache resolved.json --region US,IN --sector technology --stale-only`
2. `resolve_companies.py` uses, per company: CSV-verified token → `discover_ats.py` token guess
   (Greenhouse/Lever/Ashby/SmartRecruiters) → `sniff_careers.py` on the careers page
   (detects Workday/iCIMS/Taleo/Oracle/SuccessFactors too, with a `fetchable` flag).
3. `find-jobs` reads `resolved.json` and fans out: `fetchable` boards → the matching ATS adapter;
   `detected_unfetchable` (iCIMS/Taleo/Oracle/SuccessFactors) → SerpApi(company) / `firecrawl.py`.

`target.industries` → `sector` mapping (e.g. `fintech` → `technology`+`finance-banking`) is handled
by `find-jobs`/the resolver so users never need to learn the sector vocab.

Region/source nuances live in [`../regions/`](../regions/); the adapter contract is in
[`../../skills/find-jobs/reference/sources.md`](../../skills/find-jobs/reference/sources.md).
