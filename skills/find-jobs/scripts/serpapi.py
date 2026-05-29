#!/usr/bin/env python3
"""SerpApi Google Jobs adapter — the best single aggregator (covers Indeed, LinkedIn,
ZipRecruiter, Workday-origin listings) reached legitimately. Reads SERPAPI_KEY from env;
free tier is 100 searches/month, so the find-jobs orchestrator should budget-cap calls
(a few queries per run, not one per company).

Usage:
  python3 serpapi.py --query "product manager" --location "New York" --num 20 [--company "Stripe"] [--country us]

Prints a JSON array in the JobClaw job schema to stdout. Missing key → prints [] and a
stderr note (graceful skip, like adzuna.py).
"""
import argparse, hashlib, json, os, sys, urllib.parse, urllib.request

UA = {"User-Agent": "JobClaw-Skills/0.0 (+https://github.com/jobclaw)"}


def _id(company, title, location):
    return hashlib.sha1(f"serpapi|{company}|{title}|{location}".lower().encode()).hexdigest()[:16]


def _remote(text):
    t = (text or "").lower()
    if "remote" in t:
        return "remote"
    if "hybrid" in t:
        return "hybrid"
    return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--location", default="")
    ap.add_argument("--num", type=int, default=20, help="cap results (best-effort)")
    ap.add_argument("--company", default="", help="narrow to one company (appended to the query)")
    ap.add_argument("--country", default="us", help="gl param: us | in | ...")
    a = ap.parse_args()

    key = os.environ.get("SERPAPI_KEY")
    if not key:
        print("[serpapi] SERPAPI_KEY not set — skipping.", file=sys.stderr)
        json.dump([], sys.stdout)
        return

    q = f"{a.query} {a.company}".strip() if a.company else a.query
    params = {"engine": "google_jobs", "q": q, "api_key": key, "gl": a.country, "hl": "en"}
    if a.location:
        params["location"] = a.location
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[serpapi] request failed: {e}", file=sys.stderr)
        json.dump([], sys.stdout)
        return

    out = []
    for j in data.get("jobs_results", [])[:a.num]:
        title = j.get("title", "")
        comp = j.get("company_name", "")
        loc = j.get("location", "")
        ext = j.get("detected_extensions", {}) or {}
        apply_opts = j.get("apply_options") or []
        url_out = (apply_opts[0].get("link") if apply_opts else "") or j.get("share_link", "")
        out.append({
            "id": _id(comp, title, loc),
            "title": title, "company": comp, "location": loc,
            "remote": _remote(loc + " " + j.get("description", "")),
            "url": url_out, "source": "serpapi",
            "posted_date": None,  # Google Jobs gives relative ("3 days ago"); don't guess an ISO date
            "salary": ext.get("salary"),
            "employment_type": (ext.get("schedule_type") or "unknown").lower(),
            "description": (j.get("description") or "")[:4000],
            "tags": [t for t in [ext.get("schedule_type")] if t], "fit_rank": 0,
        })

    json.dump(out, sys.stdout, indent=2)
    print(f"\n[serpapi] {len(out)} jobs (1 search used)", file=sys.stderr)


if __name__ == "__main__":
    main()
