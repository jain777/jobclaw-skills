#!/usr/bin/env python3
"""Workday adapter. Workday boards are per-tenant CXS endpoints, so discovery isn't a token
guess — get the CXS base from sniff_careers.py, then this POSTs the jobs query.

Usage:
  python3 workday.py --cxs "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite" --query "product manager" --limit 50

Prints a JSON array in the JobClaw job schema. Best-effort — Workday tenants vary.
"""
import argparse, hashlib, json, sys, urllib.request

UA = {"User-Agent": "JobClaw-Skills/0.0 (+https://github.com/jobclaw)",
      "Content-Type": "application/json", "Accept": "application/json"}


def _id(company, title, loc):
    return hashlib.sha1(f"workday|{company}|{title}|{loc}".lower().encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cxs", required=True,
                    help="CXS base, e.g. https://t.wd5.myworkdayjobs.com/wday/cxs/t/Site")
    ap.add_argument("--query", default="")
    ap.add_argument("--limit", type=int, default=50)
    a = ap.parse_args()

    base = a.cxs.rstrip("/")
    host = base.split("/wday/cxs/")[0]
    tenant = base.split("/wday/cxs/")[-1].split("/")[0] if "/wday/cxs/" in base else "company"
    out, offset = [], 0
    try:
        while len(out) < a.limit:
            payload = {"limit": 20, "offset": offset, "searchText": a.query, "appliedFacets": {}}
            req = urllib.request.Request(base + "/jobs", data=json.dumps(payload).encode(), headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            posts = data.get("jobPostings", [])
            if not posts:
                break
            for j in posts:
                title, loc = j.get("title", ""), j.get("locationsText", "")
                path = j.get("externalPath", "")
                out.append({
                    "id": _id(tenant, title, loc), "title": title, "company": tenant,
                    "location": loc,
                    "remote": "remote" if "remote" in (title + loc).lower() else "unknown",
                    "url": (host + path) if path.startswith("/") else path,
                    "source": "workday", "posted_date": None, "salary": None,
                    "employment_type": "unknown",
                    "description": " ".join(j.get("bulletFields", []))[:4000], "tags": [], "fit_rank": 0,
                })
            offset += 20
            if offset >= data.get("total", 0):
                break
    except Exception as e:
        print(f"[workday] failed: {e}", file=sys.stderr)

    out = out[:a.limit]
    json.dump(out, sys.stdout, indent=2)
    print(f"\n[workday] {len(out)} jobs", file=sys.stderr)


if __name__ == "__main__":
    main()
