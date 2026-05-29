#!/usr/bin/env python3
"""Ingest Y Combinator companies from the public yc-oss dataset into the catalog schema.
YC startups overwhelmingly use Greenhouse/Lever/Ashby — boards our resolver already fetches —
so adding them materially widens startup + AI coverage.

Source: https://yc-oss.github.io/api/companies/all.json (community-maintained mirror of YC's
public company directory; no key). ~6k companies; we filter to a hireable, high-signal subset.

Default filter: status=Active AND (isHiring OR top_company OR AI-tagged). Tune with flags.

Usage:
  python3 yc_companies.py [--hiring-only] [--ai-only] [--top-only] [--all-active]
                          [--min-team 0] [--max 0] [--region-default US]

Prints JSON rows ready for the catalog: [{name,domain,region,sector,tracks,careers_url,
source_index,notes}]. Merge into knowledge/companies/companies.csv (dedupe by region+domain).
"""
import argparse, json, sys, urllib.request

API = "https://yc-oss.github.io/api/companies/all.json"
UA = {"User-Agent": "JobClaw-Skills/0.0 (+https://github.com/jobclaw)"}

# YC `industry` -> our controlled sector vocab (best-effort; default technology).
INDUSTRY_SECTOR = {
    "B2B Software and Services": "technology",
    "Engineering, Product and Design": "technology",
    "Consumer": "retail-consumer",
    "Fintech": "finance-banking",
    "Financial": "finance-banking",
    "Healthcare": "healthcare-pharma",
    "Real Estate and Construction": "real-estate-construction",
    "Industrials": "manufacturing-industrial",
    "Education": "education",
    "Government": "government-nonprofit",
}
AI_TAG_HINTS = ("artificial intelligence", "machine learning", "generative ai", "ai", "ml",
                "llm", "nlp", "computer vision", "ai-powered", "aiops")


def _domain(website):
    d = (website or "").lower().strip().replace("https://", "").replace("http://", "")
    d = d.split("/")[0]
    return d[4:] if d.startswith("www.") else d


def _is_ai(c):
    tags = [t.lower() for t in (c.get("tags") or [])]
    sub = (c.get("subindustry") or "").lower()
    if any(t in ("artificial intelligence", "machine learning", "generative ai", "ai", "ml",
                 "aiops", "llm", "nlp", "computer vision") for t in tags):
        return True
    return "artificial intelligence" in sub or "machine learning" in sub


def _region(c, default):
    regions = " ".join(c.get("regions") or []) + " " + (c.get("all_locations") or "")
    r = regions.lower()
    if "india" in r:
        return "IN"
    if "united states" in r or "america" in r:
        return "US"
    return default


def _sector(c):
    return INDUSTRY_SECTOR.get(c.get("industry") or "", "technology")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hiring-only", action="store_true", help="only companies flagged isHiring")
    ap.add_argument("--ai-only", action="store_true", help="only AI/ML-tagged companies")
    ap.add_argument("--top-only", action="store_true", help="only YC top_company")
    ap.add_argument("--all-active", action="store_true", help="all Active companies (large)")
    ap.add_argument("--min-team", type=int, default=0, help="min team_size")
    ap.add_argument("--max", type=int, default=0, help="cap output rows (0 = no cap)")
    ap.add_argument("--region-default", default="US")
    a = ap.parse_args()

    try:
        req = urllib.request.Request(API, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[yc] fetch failed: {e}", file=sys.stderr)
        json.dump([], sys.stdout)
        return

    out, seen = [], set()
    for c in data:
        if c.get("status") != "Active":
            continue
        if (c.get("team_size") or 0) < a.min_team:
            continue
        ai = _is_ai(c)
        if a.top_only and not c.get("top_company"):
            continue
        if a.ai_only and not ai:
            continue
        if a.hiring_only and not c.get("isHiring"):
            continue
        if not (a.all_active or a.top_only or a.ai_only or a.hiring_only):
            # default high-signal subset
            if not (c.get("isHiring") or c.get("top_company") or ai):
                continue
        dom = _domain(c.get("website"))
        if not dom or dom in seen:
            continue
        seen.add(dom)
        tracks = ["yc"]
        if ai:
            tracks.append("ai")
        if c.get("top_company"):
            tracks.append("yc-top")
        out.append({
            "name": c.get("name", "").strip(),
            "domain": dom,
            "region": _region(c, a.region_default),
            "sector": _sector(c),
            "tracks": ",".join(tracks),
            "careers_url": "",
            "source_index": "yc",
            "notes": f"YC {c.get('batch','')}".strip() + (" · hiring" if c.get("isHiring") else ""),
        })
        if a.max and len(out) >= a.max:
            break

    json.dump(out, sys.stdout, indent=2)
    print(f"\n[yc] {len(out)} companies (active, filtered)", file=sys.stderr)


if __name__ == "__main__":
    main()
