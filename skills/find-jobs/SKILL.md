---
name: find-jobs
description: >
  Find relevant job listings for the user by combining multiple sources — Claude web
  search, ATS-direct boards (Greenhouse/Lever/Ashby/Workday/SmartRecruiters), Hacker News
  hiring, and optional APIs (Adzuna, SerpApi) with a Firecrawl scrape fallback — then
  normalize, dedupe across runs, and rank against the master profile.
when_to_use: >
  Use when the user wants to find or refresh job listings, search a role/location, or
  feed candidates to score-fit. Runs after build-profile.
user-invocable: true
allowed-tools: Read, WebSearch, WebFetch, Bash, Write
---

# find-jobs

Pull listings from several **source adapters**, normalize them to one schema, dedupe, rank by fit, and save. Search quality is meant to keep improving — adapters are pluggable. Full design + caveats: [reference/sources.md](reference/sources.md) and [`docs/JOB_SEARCH.md`](../../docs/JOB_SEARCH.md).

## 1. Read the target

Read `profile/master-profile.md` frontmatter `target.*` (roles, locations, remote_only, industries, seniority, min_base_salary, exclude_companies) **and `target.regions`**. If no profile exists, ask for role + location, then suggest running `/build-profile`. Let the user override any criterion for this run.

**Then read the region pack(s)** in [`../../knowledge/regions/`](../../knowledge/regions/) for each target region — it lists which sources/adapters apply there (e.g., `US` → ATS-direct + Adzuna(`us`) + HN; `IN` → Indian ATS-direct startups + Adzuna(`in`), with Naukri/Instahyre/LinkedIn-India as user-session/manual). Source from the **region-appropriate** list, not a US-only default.

## 2. Build the company target set (cache-driven)

The catalog [`../../knowledge/companies/companies.csv`](../../knowledge/companies/companies.csv) lists 1000+ employers across all industries, tagged by `region` + `sector`. Use it instead of probing the web blind:

1. **Filter the catalog** to the user's `target.regions` and `target.industries` (map industries → the `sector` vocab, e.g. `fintech` → `technology`+`finance-banking`; see [`../../knowledge/companies/README.md`](../../knowledge/companies/README.md)). Add any companies named in the profile.
   - **AI targets:** when `target.roles`/`target.tracks` indicate AI/ML (see [`../../knowledge/ai-roles.md`](../../knowledge/ai-roles.md)), prioritize catalog rows tagged **`ai`** or **`yc`** in `tracks`, and pull fresh YC AI startups: `python3 scripts/yc_companies.py --ai-only` (or `--hiring-only` for currently-hiring). The catalog already carries 2400+ YC companies + curated frontier labs (`source_index` ∈ `yc`/`ai`).
2. **Resolve boards from the cache.** Refresh just the slice you need, then read it:
   ```
   python3 scripts/resolve_companies.py --csv ../../knowledge/companies/companies.csv \
       --cache ../../knowledge/companies/resolved.json \
       --region <US,IN> --sector <...> --stale-only --max 300
   ```
   This populates [`resolved.json`](../../knowledge/companies/resolved.json) with each company's
   `boards[]` (`ats`, `token`, `board_url`, `fetchable`) and `status`
   (`verified` / `detected_unfetchable` / `unresolved`). It reuses `discover_ats.py` +
   `sniff_careers.py` and is cached, so most runs are near-instant.

## 3. Run the adapters

Use every source available; **none are required** — degrade gracefully. Output of all adapters maps to [reference/job-schema.md](reference/job-schema.md). Read `.env` (do not print secrets); skip any adapter whose key is absent and note it.

**ATS-direct (highest-quality free tier).** Group the cache's `fetchable` boards by `ats` and fan out:
- `python3 scripts/ats_boards.py --greenhouse <gh,...> --lever <lever,...> --ashby <ashby,...> --query "<role>"`
- `python3 scripts/smartrecruiters.py --companies "<id,...>" --query "<role>"` (big non-tech coverage)
- `python3 scripts/teamtailor.py --companies "<slug,...>" --query "<role>"` (RSS; common at startups)
- `python3 scripts/workday.py --cxs "<board_url>" --query "<role>"` (one call per Workday tenant)

**Enterprise-ATS fallback (honest gap).** Boards marked `detected_unfetchable` (iCIMS / Taleo / Oracle / SuccessFactors — no clean public API) and `unresolved` JS-only pages don't have a direct adapter. Reach them via, in order:
- `python3 scripts/serpapi.py --query "<role>" --company "<name>" --location "<loc>"` (if `SERPAPI_KEY`), then
- `python3 scripts/firecrawl.py --url "<careers_url>"` (if `FIRECRAWL_API_KEY`) → renders the page; **you** extract listings from the returned `markdown` into the job schema, then
- plain `WebFetch` of the careers page as the last resort.

**Cutshort (zero key — strong IN consumer / marketing / startup recall).** Category pages list individual `/job/` postings whose JSON-LD carries the real JD + dates. Get category URLs from `WebSearch` (`site:cutshort.io <role> <location>`) and pass them in:
- `python3 scripts/cutshort.py --url "<category_url>" [--url ...] --query "<terms>" --max 15 --today <YYYY-MM-DD>` → returns only **fresh** postings (≤`--max-age-days`, default 45; drops stale/expired by `datePosted`/`validThrough`), already `verified:true` with `posted_date`. Best non-ATS path for beauty/D2C/FMCG/agency roles.

**Aggregators & always-on (zero key):**
- **Claude web search** — `WebSearch` for `"<role>" jobs <location>`; `WebFetch` promising listing pages. **Prefer individual posting URLs over aggregator landing pages** (Glassdoor/Indeed/Naukri *search* pages aren't single reqs — the verify step in §4 drops them as `not_a_posting`).
- **Hacker News "Who is hiring"** — `python3 scripts/hn_hiring.py --query "<role>" --remote <true|false>`.
- **Adzuna** (`ADZUNA_APP_ID`/`ADZUNA_APP_KEY`) — `python3 scripts/adzuna.py --what "<role>" --where "<location>" --results 50 --country <us|in>`.
- **SerpApi Google Jobs** (`SERPAPI_KEY`) — best single aggregator (Indeed/LinkedIn/etc.). **Budget-capped**: ~5 queries/run max (free tier is 100/mo) — use role+location aggregate queries plus a few targeted `--company` lookups for unfetchable enterprise boards.

## 4. Verify (fetch-to-verify), normalize, dedupe across runs, recency, rank

- **Fetch-to-verify (do this before ranking — it's the freshness + real-JD gate).** Web-search/snippet results are undated and may be evergreen landing pages or long-dead reqs (a Cutshort posting from 2020 stays "listed"). Pipe candidates through:
  ```
  python3 scripts/verify_postings.py --in <found>.json --out <found>.json --today <YYYY-MM-DD> [--max-age-days 45] [--drop-stale]
  ```
  It fetches each `url`, parses the schema.org `JobPosting` JSON-LD, and stamps `verified`, `status` (`active`/`stale`/`expired`/`closed`/`not_a_posting`/`unverifiable`/`fetch_error`), `posted_date`, `valid_through`, and replaces the snippet `description` with the **real JD**. Adapters that already verify (cutshort, ATS-direct) can skip re-verification. For `unverifiable` (JS-rendered) pages, `WebFetch` them as a fallback before discarding. **Do not present `stale`/`expired`/`not_a_posting` as live** — `--drop-stale` removes them.
- Map every result to the job schema; drop entries missing a title or company.
- **Within-run dedupe** by normalized `company + title + location` (and canonicalized URL); keep the richest entry / most direct apply URL.
- **Cross-run dedupe + first-seen:** pipe the merged array through
  `python3 scripts/jobstore.py merge --in <found>.json --store jobs/seen.json --today <YYYY-MM-DD>` —
  it stamps `first_seen` and flags `is_new` so refreshes surface what's actually new.
- **Recency:** `python3 scripts/jobstore.py filter --in <found>.json --max-age-days 30 --today <YYYY-MM-DD>` drops stale postings (undated kept by default).
- **Filter** out `exclude_companies` and hard-constraint violations (onsite when `remote_only`; comp clearly below `min_base_salary` when known).
- **Rank** by fit (role/seniority/industry/location match, recency, `is_new`). Don't run a full `score-fit` here — that's a separate per-job step; this is a cheap relevance sort.

## 5. Present & save

- Show a ranked table: title · company · location · remote · source · posted · link (mark `is_new`).
- Save the full normalized list to `jobs/found-<YYYY-MM-DD>.json` (create `jobs/` if needed).
- Note which adapters ran vs. were skipped (and which key would unlock more), and how many companies were `detected_unfetchable` (reached via fallback or not).
- Suggest `/score-fit` on the top results. Be concise; no emoji.
