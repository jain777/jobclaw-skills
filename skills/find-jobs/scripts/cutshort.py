#!/usr/bin/env python3
"""Cutshort adapter — strong recall for Indian consumer / marketing / startup roles
that aren't on Greenhouse/Lever/Ashby (the gap the Snigdha reruns exposed).

Cutshort category pages list individual `/job/<slug>` postings; each posting embeds
a schema.org JobPosting (real JD + datePosted + validThrough). So this adapter:
  1. fetches one or more category pages,
  2. regex-extracts the individual posting URLs,
  3. fetches each posting and parses its JobPosting JSON-LD into the job schema,
  4. drops expired postings (validThrough < today) unless --include-expired.

  # category URLs come from WebSearch, e.g. site:cutshort.io <role> <location>
  python3 cutshort.py --url https://cutshort.io/jobs/social-media-marketing-smm-jobs \
          --query "social media,content" --location Delhi --max 15 --today 2026-05-29

Output: JSON array on stdout (job-schema; source="cutshort", verified=true). Stdlib only.
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _jobposting as JP  # noqa: E402

BASE = "https://cutshort.io"
_SLUG_RE = re.compile(r'/job/[A-Za-z0-9][A-Za-z0-9\-]{6,}')


def _slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def candidate_category_urls(query, location):
    """Best-effort category URLs from query/location (Cutshort's slug conventions)."""
    urls = []
    q = _slugify(query)
    loc = _slugify(location)
    if q:
        urls.append(f"{BASE}/jobs/{q}-jobs")
        if loc:
            urls.append(f"{BASE}/jobs/{q}-jobs-in-{loc}")
    return urls


def posting_urls_from_category(cat_url):
    """Fetch a category page and return absolute individual posting URLs (deduped)."""
    try:
        html = JP.fetch(cat_url)
    except Exception as e:  # noqa: BLE001
        print(f"[cutshort] category fetch failed {cat_url}: {e}", file=sys.stderr)
        return []
    seen, out = set(), []
    for path in _SLUG_RE.findall(html):
        if path not in seen:
            seen.add(path)
            out.append(BASE + path)
    return out


def scrape_posting(url, today, query_terms):
    """Fetch one posting, parse JobPosting JSON-LD -> job-schema dict (or None)."""
    try:
        html = JP.fetch(url)
    except Exception as e:  # noqa: BLE001
        print(f"[cutshort] posting fetch failed {url}: {e}", file=sys.stderr)
        return None
    jp = JP.first_jobposting(html)
    if not jp or not jp.get("title"):
        return None
    if query_terms and not any(t in jp["title"].lower() for t in query_terms):
        return None
    status = JP.status_for(jp["posted_date"], jp["valid_through"], today,
                           max_age_days=scrape_posting.max_age_days,
                           closed=JP.has_closed_marker(html))
    return {
        "title": jp["title"], "company": jp["company"], "location": jp["location"],
        "remote": "onsite", "url": url, "source": "cutshort",
        "posted_date": jp["posted_date"], "valid_through": jp["valid_through"],
        "salary": jp["salary"], "employment_type": jp["employment_type"],
        "description": jp["description"], "tags": jp["tags"],
        "verified": True, "status": status, "live": status == "active",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", default=[], help="Cutshort category URL(s).")
    ap.add_argument("--query", default="", help="Comma terms; keep only titles containing one.")
    ap.add_argument("--location", default="", help="Used only to build a category URL guess.")
    ap.add_argument("--max", type=int, default=15, help="Max postings to fetch in total.")
    ap.add_argument("--today", required=True, help="YYYY-MM-DD (freshness reference).")
    ap.add_argument("--max-age-days", type=int, default=45,
                    help="Drop postings older than this by datePosted (default 45).")
    ap.add_argument("--include-expired", action="store_true",
                    help="Keep expired/stale postings too.")
    args = ap.parse_args()
    scrape_posting.max_age_days = args.max_age_days

    cats = list(args.url) or candidate_category_urls(args.query, args.location)
    if not cats:
        print("[cutshort] no category URL (give --url, or --query[/--location])", file=sys.stderr)
        return 2

    posting_urls, seen = [], set()
    for c in cats:
        for u in posting_urls_from_category(c):
            if u not in seen:
                seen.add(u)
                posting_urls.append(u)
    print(f"[cutshort] {len(posting_urls)} posting URLs from {len(cats)} category page(s)", file=sys.stderr)

    terms = [t.strip().lower() for t in args.query.split(",") if t.strip()]
    jobs = []
    for u in posting_urls:
        if len(jobs) >= args.max:
            break
        rec = scrape_posting(u, args.today, terms)
        if not rec:
            continue
        if rec["status"] in ("expired", "stale") and not args.include_expired:
            print(f"[cutshort] skip {rec['status']} ({rec['posted_date']}): "
                  f"{rec['company']} — {rec['title']}", file=sys.stderr)
            continue
        jobs.append(rec)
        time.sleep(0.3)  # be polite

    print(f"[cutshort] returning {len(jobs)} live postings", file=sys.stderr)
    print(json.dumps(jobs, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
