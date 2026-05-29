#!/usr/bin/env python3
"""Adzuna adapter (free tier). Reads ADZUNA_APP_ID / ADZUNA_APP_KEY from the environment.
Get free credentials at https://developer.adzuna.com/.

Usage:
  python3 adzuna.py --what "product manager" --where "New York" --results 50 --country us

Prints a JSON array in the JobClaw job schema to stdout. If keys are missing, prints [].
"""
import argparse, hashlib, json, os, sys, urllib.parse, urllib.request

UA = {"User-Agent": "JobClaw-Skills/0.0 (+https://github.com/jobclaw)"}


def _id(company, title, location):
    return hashlib.sha1(f"adzuna|{company}|{title}|{location}".lower().encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", required=True)
    ap.add_argument("--where", default="")
    ap.add_argument("--results", type=int, default=50)
    ap.add_argument("--country", default="us")
    ap.add_argument("--remote", default="", help="true to restrict to remote")
    a = ap.parse_args()

    app_id, app_key = os.environ.get("ADZUNA_APP_ID"), os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        print("[adzuna] ADZUNA_APP_ID / ADZUNA_APP_KEY not set — skipping.", file=sys.stderr)
        json.dump([], sys.stdout)
        return

    per = min(max(a.results, 1), 50)
    params = {
        "app_id": app_id, "app_key": app_key, "results_per_page": per,
        "what": a.what, "content-type": "application/json",
    }
    if a.where:
        params["where"] = a.where
    if a.remote.lower() == "true":
        params["what_phrase"] = "remote"
    url = (f"https://api.adzuna.com/v1/api/jobs/{a.country}/search/1?"
           + urllib.parse.urlencode(params))

    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[adzuna] request failed: {e}", file=sys.stderr)
        json.dump([], sys.stdout)
        return

    out = []
    for j in data.get("results", []):
        company = (j.get("company") or {}).get("display_name", "")
        loc = (j.get("location") or {}).get("display_name", "")
        title = j.get("title", "")
        smin, smax = j.get("salary_min"), j.get("salary_max")
        salary = f"${int(smin):,}–${int(smax):,}" if smin and smax else None
        out.append({
            "id": _id(company, title, loc),
            "title": title, "company": company, "location": loc,
            "remote": "remote" if "remote" in (title + loc).lower() else "unknown",
            "url": j.get("redirect_url", ""), "source": "adzuna",
            "posted_date": (j.get("created") or "")[:10] or None, "salary": salary,
            "employment_type": j.get("contract_time", "unknown") or "unknown",
            "description": (j.get("description") or "")[:4000], "tags": [], "fit_rank": 0,
        })

    json.dump(out, sys.stdout, indent=2)
    print(f"\n[adzuna] {len(out)} jobs", file=sys.stderr)


if __name__ == "__main__":
    main()
