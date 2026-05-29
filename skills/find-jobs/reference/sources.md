# Job-search sources (adapter catalog)

`find-jobs` is a **source-adapter** system: each source returns rows in the [job schema](job-schema.md); the skill merges, dedupes, and ranks. Add sources over time — search quality is an ongoing effort. Strategy + caveats also in [`../../../docs/JOB_SEARCH.md`](../../../docs/JOB_SEARCH.md).

## Tiers

| Tier | Source | Key | Quality | Notes |
|---|---|---|---|---|
| 0 (default) | **Claude web search** (`WebSearch`/`WebFetch`) | none | medium | Broad recall; unstructured; parse per-page. |
| 0 | **ATS-direct** (Greenhouse, Lever, Ashby) | none | **high** | Straight from the company; structured; ToS-clean. `ats_boards.py`. Resolve tokens via `discover_ats.py`. |
| 0 | **SmartRecruiters** (public Posting API) | none | **high** | `smartrecruiters.py --companies <id,...>`. Big non-tech footprint (retail/healthcare/manufacturing). Resolve via `discover_ats.py` / `sniff_careers.py`. |
| 0 | **Teamtailor** (public jobs RSS) | none | medium | `teamtailor.py --companies <slug>`. Common at startups/EU; resolve slug via `sniff_careers.py`. |
| 0 | **Workday** (per-tenant) | none | **high** | `workday.py --cxs <url>`; get the CXS endpoint from `sniff_careers.py`. |
| 0 | **Hacker News "Who is hiring"** (Algolia API) | none | medium | Great for startups; monthly thread. |
| 1 | **Adzuna** | free | medium | Aggregator; salary data; decent filters. `adzuna.py`. |
| 1 | **SerpApi Google Jobs** | freemium (100 free) | **high** | `serpapi.py` **(built)** — best single aggregator (Indeed/LinkedIn/ZipRecruiter/Workday). Budget-cap to a few queries/run. |
| 1 | **Firecrawl** (scrape fallback) | freemium | medium | `firecrawl.py --url <careers>` — renders JS / enterprise-ATS pages to markdown; Claude extracts. The routing target for `fetchable:false`. |
| 2 | **TheirStack / Coresignal / Bright Data** | paid | premium | 315k+ sources, 16k+ ATS, dedup. Adapter deferred. |

## LinkedIn — read this

LinkedIn has **no third-party jobs API** (Talent API is partner-only) and **prohibits scraping** in its ToS; it blocks aggressively and litigates (Proxycurl was sued and shut down in 2025 for fake-account scraping). Public-data scraping was held not to violate the CFAA (hiQ v. LinkedIn, 2022), but that does not waive LinkedIn's ToS.

**So JobClaw does not scrape LinkedIn directly.** LinkedIn coverage comes via, in order of preference:
1. **SerpApi Google Jobs** — surfaces many LinkedIn-origin listings legitimately.
2. **The user's own authenticated session** — later, JobClaw's Playwright can read listings the *user* is logged in to see (defensible: their own account, their own data). Out of scope for this skill.
3. **LinkedIn job-alert emails** → forwarded to AgentMail → parsed (JobClaw, later).
4. **Paid compliant datasets** (Bright Data, Coresignal) for those who want them.

Never add a raw-scrape LinkedIn adapter here.

## Cross-cutting caveats
- **Dedup** is essential — the same role appears across many sources. Dedupe by `company+title+location` and canonical URL.
- **Freshness** varies; trust `posted_date` only when the source provides it.
- **Cost/limits** — native search is rate-limited; SerpApi free tier is 100/mo; Tier-2 is paid. Run free tiers first, escalate only if recall is poor.
- **Coverage ≠ quality** — prefer ATS-direct and curated company lists for "premium" roles over broad aggregators.

## Enterprise ATS (iCIMS / Taleo / Oracle Recruiting / SuccessFactors)
Most large non-tech employers run these, and **none expose a clean public JSON API**. So they are
**detect-only**: `sniff_careers.py` recognizes them and returns `fetchable: false`. `find-jobs` reaches
their roles via the fallback chain — SerpApi (company-filtered) → `firecrawl.py` (render + Claude
extracts) → `WebFetch`. This is a real coverage gap vs. the API-direct ATSes; surface it honestly in
the run summary rather than pretending the catalog is uniformly fetchable. (SmartRecruiters is the
exception — it *does* have a public API, so it gets a real adapter.)

## Resolving a company's board
1. `resolve_companies.py --csv companies.csv --cache resolved.json --stale-only` — the batch resolver;
   caches each company's board(s) so find-jobs doesn't re-probe every run. Uses 2–3 below internally.
2. `discover_ats.py --companies "..."` — guesses the token and probes Greenhouse/Lever/Ashby/SmartRecruiters.
3. `sniff_careers.py --urls "<careers_url>"` — for misses: fetches the careers page and detects the
   embedded ATS (Workday CXS, SmartRecruiters, iCIMS/Taleo/Oracle/SuccessFactors) with a `fetchable`
   flag, even when the token ≠ company name.
4. The canonical catalog is [`knowledge/companies/companies.csv`](../../../knowledge/companies/companies.csv)
   (1000+ companies, all industries); filter by the user's region + industry.

## Adding an adapter
Write `scripts/<source>.py` that prints a JSON array in the [job schema](job-schema.md) and reads its key from env. Then list it in §2 of `SKILL.md`. That's the whole contract.
