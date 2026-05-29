# Company catalog — provenance & refresh

`companies.csv` is the canonical, machine-readable catalog of employers `find-jobs` sources from.
It is assembled from well-known public indices plus curated startup supplements. Company **names
and domains are stable and verifiable in bulk**; **ATS tokens are volatile**, so they are NOT
hand-entered — they are resolved live and cached in `resolved.json` (see `resolve_companies.py`).

## How rows are sourced (`source_index` column)

| `source_index` | Region | What it covers |
|---|---|---|
| `fortune500` | US | Largest US employers across every sector (banks, retail, healthcare, energy, manufacturing). |
| `sp500` / `russell1000` | US | Large/mid-cap public companies; broad sector spread. |
| `cloud100` | US | Forbes Cloud 100 + well-known private tech/startups not in the public indices. |
| `nifty500` / `bse500` | IN | Largest Indian listed companies (IT services, banks, pharma, FMCG, auto, energy). |
| `startup` | US/IN | Notable unicorns / high-growth private companies (the original tech seed set lives here). |
| `yc` | US/IN | Y Combinator companies (active + hiring/top/AI subset) ingested from the yc-oss API via `scripts/yc_companies.py`. ~2400 rows; `tracks` carries `yc`, plus `ai`/`yc-top` where applicable. |
| `ai` | US/IN | Curated hot AI / frontier labs (OpenAI, Anthropic, Mistral, Cohere, Perplexity, ElevenLabs, Groq, …) — `tracks=ai`. |
| `seed` | US/IN | The hand-verified starter set carried over from the old `seed.md`. |

**Refreshing YC:** re-run `python3 ../../skills/find-jobs/scripts/yc_companies.py [--hiring-only|--ai-only]`
and merge new domains (dedupe by region+domain). The yc-oss API tracks ~6k YC companies; we keep the
active hiring/top/AI subset. AI roles are described in `knowledge/ai-roles.md`.

## Sector vocabulary (the `sector` column)

One value per row from this controlled list (keeps "all industries" coverage consistent):

```
technology, finance-banking, healthcare-pharma, retail-consumer, manufacturing-industrial,
energy-utilities, consulting-services, media-entertainment, telecom, automotive,
transport-logistics, real-estate-construction, aerospace-defense, food-beverage,
hospitality-travel, education, government-nonprofit
```

The finer `tracks` column (e.g. `fintech`, `ai`, `devtools`, `ecommerce`) is optional and overlaps
with the JobClaw track vocabulary; `sector` is the industry, `tracks` is the flavor.

## Accuracy strategy (why this scales without 1000 hand-checks)

- **Names + domains** come from the index lists at authoring time and rarely change.
- **Tokens are never trusted from the CSV unless verified** — `resolve_companies.py` probes the live
  ATS APIs / careers pages and writes the result to `resolved.json` with a `checked_at` date. Wrong
  guesses self-heal on the next `--refresh-older-than` pass.
- A company that migrates ATS just shows up as `unresolved`/stale and gets re-resolved; no manual edit.

## Refresh cadence

- Re-run `resolve_companies.py --stale-only --refresh-older-than 30` periodically to refresh tokens.
- Re-derive the index rows annually or when an index reconstitutes. Record the new "as-of" date here.

**As-of:** initial catalog generated 2026-05-29 (seed set + workflow-generated index rows).

## `source_index=ai-in` — Series B+ / rocketship AI startups with India offices (added 2026-05-29)

31 AI (or AI-heavy SaaS) companies with India offices, hand-curated on funding stage + rocketship status (mix of Indian-origin and global with India eng hubs/GCCs), `region=IN`, `tracks` includes `ai`. Tokens not hand-set — resolved live. **12 resolved to fetchable public-API ATS** on first pass (Greenhouse: Turing/HighRadius/DevRev/Rubrik/Druva/InMobi/Glance/Harness; Lever: Mindtickle; SmartRecruiters: Entropik/Whatfix; Workday: Sprinklr). The rest are JS/custom career sites → Firecrawl fallback (`FIRECRAWL_API_KEY` now set in `.env`, verified live on pixis.ai). Curation is editorial (stage/India-presence as of 2026-05); refresh names as companies graduate/relocate.
