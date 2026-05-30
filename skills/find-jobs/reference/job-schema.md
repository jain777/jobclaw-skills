# Normalized job schema

Every adapter maps its results to this shape. Saved as a JSON array to `jobs/found-<date>.json`.

```json
{
  "id": "string — stable hash of source+company+title+location",
  "title": "string",
  "company": "string",
  "location": "string",
  "remote": "remote | hybrid | onsite | unknown",
  "url": "string — direct apply/listing URL",
  "source": "string — adapter name (web | greenhouse | lever | hn | adzuna | serpapi | ...)",
  "posted_date": "YYYY-MM-DD | null",
  "salary": "string | null — as published, e.g. '$180k–$220k'",
  "employment_type": "full-time | contract | part-time | internship | unknown",
  "description": "string — full or summarized text (keep enough for score-fit)",
  "tags": ["string"],
  "fit_rank": "0-100 — Claude-ranker relevance over the top-N (knowledge/relevance.md); sort key. A fast estimate, NOT the authoritative score-fit.",
  "fit_reason": "string | null — one line (≤120 chars) why; describes the JOB, never echoes context.*",
  "prerank_score": "0-100 | absent — transient deterministic pre-rank from prerank.py (stage A); not authoritative",
  "first_seen": "YYYY-MM-DD | null — set by jobstore.py; the date this id first appeared",
  "is_new": "boolean — set by jobstore.py; true if unseen before this run",
  "verified": "boolean — set by verify_postings.py/cutshort.py; true if a real JobPosting was parsed",
  "status": "active | stale | expired | closed | not_a_posting | unverifiable | fetch_error",
  "live": "boolean | null — true only when status == active",
  "valid_through": "YYYY-MM-DD | null — JobPosting validThrough (expiry)",
  "jd_source": "jsonld | snippet | adapter — provenance of `description`"
}
```

`first_seen` and `is_new` are optional — present only after `jobstore.py merge` runs. Adapters
leave them unset; the orchestrator stamps them. `verified`/`status`/`live`/`valid_through`/`jd_source`
are set by the **fetch-to-verify** step (`verify_postings.py`) or by adapters that self-verify
(`cutshort.py`, ATS-direct). Treat only `status == active` as a live, applyable posting; a real
`posted_date` (not a snippet) is what makes the recency filter meaningful.

## Normalization rules
- `location`: "City, ST" or "Remote (Region)"; set `remote` from the listing language.
- `posted_date`: ISO; null if unknown (don't guess).
- `salary`: keep the source string verbatim; null if absent.
- `description`: preserve enough for `score-fit` to work without re-fetching; summarize only if very long.
- `id`: deterministic so re-runs dedupe against prior saves.
