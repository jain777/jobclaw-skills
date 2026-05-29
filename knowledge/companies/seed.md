# Seed company list (highlights)

> **The canonical catalog is now [`companies.csv`](companies.csv)** (1000+ companies, all industries,
> US + IN). This file is just a human-readable highlight of verified, ready-to-fetch boards. See
> [`README.md`](README.md) for the schema and [`SOURCES.md`](SOURCES.md) for provenance.

Resolve a board with `resolve_companies.py` (writes [`resolved.json`](resolved.json)); `find-jobs`
reads the cache and fans out adapters. Verified tokens below are carried in the CSV.

## Verified notable boards

| Company | Region | ATS | Token |
|---|---|---|---|
| Anthropic | US | greenhouse | anthropic |
| Databricks | US | greenhouse | databricks |
| Stripe | US | greenhouse | stripe |
| Mercury | US | greenhouse | mercury |
| Brex | US | greenhouse | brex |
| Ramp | US | ashby | Ramp |
| Postman | IN | greenhouse | postman |
| Groww | IN | greenhouse | groww |
| Meesho | IN | lever | meesho |
| CRED | IN | lever | cred |

Everything else (Fortune 500, NIFTY 500, the long tail) lives in `companies.csv` with `ats`/`token`
blank — resolved lazily and cached. JS-only / enterprise-ATS pages (iCIMS/Taleo/Oracle/SuccessFactors)
are detected by `sniff_careers.py` and fetched via SerpApi / `firecrawl.py`.
