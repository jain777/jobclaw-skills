# Job search — design, sources & caveats

> Search quality is the part of these skills that **never stops improving**. This doc is the strategy + the running caveats list. The implementation is the `find-jobs` skill ([`skills/find-jobs`](../skills/find-jobs)), built as a pluggable **source-adapter** system so new/better sources drop in without touching the rest.

## The problem
No single source has good *coverage*, *quality*, and *legality* at once. Aggregators are broad but noisy and stale; ATS-direct is pristine but per-company; the source everyone wants (LinkedIn) is the most hostile to automation. So `find-jobs` blends sources by tier and dedupes, and we keep adding "premium" sources over time.

## Source tiers

| Tier | Source | Key | Quality | Status | Notes |
|---|---|---|---|---|---|
| 0 | **Claude web search** (`WebSearch`/`WebFetch`) | none | medium | ✅ built (in SKILL) | Broad recall; unstructured; parse per page. |
| 0 | **ATS-direct** — Greenhouse, Lever, Ashby, Workday | none | **high** | ✅ built + **live-verified** (`ats_boards.py`, `workday.py`) | Straight from the company; structured; ToS-clean. Tokens resolved + cached by `resolve_companies.py`. |
| 0 | **SmartRecruiters** (public Posting API) | none | **high** | ✅ built + live-verified (`smartrecruiters.py`, Visa) | Big non-tech footprint; resolved via `discover_ats.py`/`sniff_careers.py`. |
| 0 | **Teamtailor** (public jobs RSS) | none | medium | ✅ built + live-verified (`teamtailor.py`, polestar=30) | Startup/EU; slug via `sniff_careers.py`. |
| 0 | **YC companies** (yc-oss API) | none | n/a (catalog feed) | ✅ built (`yc_companies.py`) | Ingests ~2400 active/hiring/AI YC cos into the catalog; most use GH/Lever/Ashby → fetchable. |
| 0 | **Hacker News "Who is hiring"** (Algolia) | none | medium | ✅ built + verified (`hn_hiring.py`) | Startup-heavy; monthly thread; loose `Company \| Role \| Loc \| Remote` format. |
| 0 | **Cutshort** (category → JSON-LD postings) | none | medium | ✅ built (`cutshort.py`) | Strong IN consumer/marketing/startup recall; self-verifying + fresh-only. |
| 1 | **Adzuna** | free | medium | ✅ built (`adzuna.py`, graceful skip w/o key) | Aggregator; salary data; decent filters. |
| 1 | **SerpApi Google Jobs** | freemium (100/mo) | **high** | ✅ built (`serpapi.py`) | Best single aggregator — Indeed/LinkedIn/ZipRecruiter/Workday. Budget-cap a few queries/run. |
| 1 | **Firecrawl** (scrape fallback) | freemium | medium | ✅ built (`firecrawl.py`) | Renders JS / enterprise-ATS pages → markdown; Claude extracts. Fallback for `fetchable:false`. |
| — | **Enterprise ATS** — iCIMS / Taleo / Oracle / SuccessFactors | none | n/a | ✅ detect-only (`sniff_careers.py`) | No clean public API → routed to SerpApi/Firecrawl/WebFetch. |
| 2 | **TheirStack / Coresignal / Bright Data** | paid | premium | ⬜ deferred | 315k+ sources, 16k+ ATS, dedup. The "more & better listings" upgrade. |

## LinkedIn — the central caveat
- **No third-party jobs API.** LinkedIn's Talent API is partner-only — hard to get, priced by quote, not realistic for an OSS tool.
- **Scraping breaks ToS and is actively fought.** Public-data scraping was held *not* to violate the US CFAA (hiQ Labs v. LinkedIn, 9th Cir., 2022), but that doesn't waive LinkedIn's Terms. LinkedIn blocks aggressively and litigates — **Proxycurl was sued (Jan 2025) and shut down (mid-2025)** for scraping via fake accounts.
- **Therefore these skills never raw-scrape LinkedIn.** LinkedIn coverage comes, in order of preference:
  1. **SerpApi Google Jobs** — surfaces LinkedIn-origin listings legitimately (Tier 1).
  2. **The user's own authenticated session** — an optional agent's browser can read listings the *user* is logged in to see (their account, their data — defensible). Out of scope for the standalone skill.
  3. **LinkedIn job-alert emails → parsed** — ToS-friendly; for the optional agent.
  4. **Paid compliant datasets** (Bright Data has defended scraping in US courts; Coresignal) for users who opt in.

## Architecture
- **Adapter contract:** a source = `scripts/<name>.py` that prints a JSON array in the [job schema](../skills/find-jobs/reference/job-schema.md) and reads its key from env. Native-web-search "adapters" are instructions in the SKILL instead of a script.
- **Pipeline:** run enabled adapters → normalize → **dedupe** (`company+title+location` + canonical URL) → filter (`exclude_companies`, hard constraints) → cheap **fit rank** → save to `jobs/found-<date>.json`.
- **Degrade gracefully:** every source is optional; missing keys just shrink the result set, never error.
- **Scripts are Python 3 stdlib only** (urllib/json/argparse) — zero `pip install`, runs anywhere.

## Roadmap (how search keeps improving)
1. ✅ **Squeeze the free tier first:** per-user ATS discovery (`discover_ats.py`), Ashby + **SmartRecruiters** + **Teamtailor** boards, **SerpApi** + **Firecrawl** + **Cutshort** built, enterprise-ATS detection (iCIMS/Taleo/Oracle/SuccessFactors).
2. ✅ **Shipped company catalog** (`companies.csv`, all industries, US+IN) + batch resolver + token cache (`resolved.json`). Includes **~2400 YC companies** (`yc_companies.py`) + a curated **hot-AI/frontier** set; AI roles handled via `knowledge/ai-roles.md`. Per-user discovery still appends profile-named companies.
3. ✅ **Persistent job store + cross-run dedup** (`jobstore.py` — first-seen + `is_new` + recency filter) + **fetch-to-verify** (`verify_postings.py` — real JD + freshness via schema.org JobPosting JSON-LD).
4. **More regions** — add a `knowledge/regions/<code>.md` pack + catalog rows (Canada, EU, SG).
5. **Naukri / Internshala adapters** — biggest India consumer/FMCG recall gap (those employers aren't on fetchable ATS boards).
6. **Smarter ranking** — embed profile + listings for semantic match instead of keyword sort.
7. **Enterprise-ATS direct adapters** (iCIMS/Taleo/Oracle/SuccessFactors OData) — currently fallback-only.
8. **Paid adapters** (TheirStack) — see requirements below; only if free-tier recall proves insufficient.

## Paid-API requirements (evaluate before integrating)
When free-tier recall proves insufficient, evaluate a paid source against:
- **Coverage** — does it actually add roles the free tier misses (esp. LinkedIn-origin)? Measure overlap vs. uplift on real searches.
- **Cost model** — per-search vs. per-record vs. subscription; predictable at one-user scale.
- **Freemium ceiling** — SerpApi = 100 searches/mo free (enough to validate); TheirStack = paid-only.
- **Dedup quality** — does it pre-dedup across sources (TheirStack does) or do we?
- **ToS / legality** — provider's standing (Bright Data has defended scraping in US courts; avoid fake-account providers like the defunct Proxycurl).
- **Schema fit** — fields map cleanly to the [job schema](../skills/find-jobs/reference/job-schema.md); structured salary/remote/date.

## Sources
- [Guide to LinkedIn API and Alternatives — Scrapfly](https://scrapfly.io/blog/posts/guide-to-linkedin-api-and-alternatives)
- [Best Job APIs and Data Providers to Use in 2026 — Bright Data](https://brightdata.com/blog/web-data/best-job-apis)
- [Google Jobs API — SerpApi](https://serpapi.com/google-jobs-api)
- [Job Postings API — TheirStack](https://theirstack.com/en/job-posting-api)
