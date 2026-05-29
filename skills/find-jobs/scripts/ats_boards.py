#!/usr/bin/env python3
"""ATS-direct adapter: pull job postings straight from Greenhouse, Lever, and Ashby public
boards. Structured, fresh, and ToS-clean (these JSON endpoints are public).

Usage:
  python3 ats_boards.py --greenhouse stripe,airbnb --lever netflix --ashby Ramp,Linear --query "product manager"

Prints a JSON array in the JobClaw job schema to stdout. Network/parse errors for one
board never abort the rest — they're reported on stderr.
"""
import argparse, hashlib, html, json, re, sys, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "JobClaw-Skills/0.0 (+https://github.com/jobclaw)"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _strip_html(s):
    if not s:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").strip()


def _id(source, company, title, location):
    raw = f"{source}|{company}|{title}|{location}".lower()
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _remote(text):
    t = (text or "").lower()
    if "remote" in t:
        return "remote"
    if "hybrid" in t:
        return "hybrid"
    return "unknown"


def greenhouse(token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    out = []
    for j in _get(url).get("jobs", []):
        title = j.get("title", "")
        loc = (j.get("location") or {}).get("name", "")
        desc = _strip_html(j.get("content", ""))
        posted = (j.get("updated_at") or "")[:10] or None
        out.append({
            "id": _id("greenhouse", token, title, loc),
            "title": title, "company": token, "location": loc,
            "remote": _remote(loc + " " + desc), "url": j.get("absolute_url", ""),
            "source": "greenhouse", "posted_date": posted, "salary": None,
            "employment_type": "unknown", "description": desc[:4000], "tags": [], "fit_rank": 0,
        })
    return out


def lever(slug):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    out = []
    for j in _get(url):
        title = j.get("text", "")
        cats = j.get("categories") or {}
        loc = cats.get("location", "")
        desc = _strip_html(j.get("descriptionPlain") or j.get("description") or "")
        created = j.get("createdAt")
        posted = (datetime.fromtimestamp(created / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                  if created else None)
        out.append({
            "id": _id("lever", slug, title, loc),
            "title": title, "company": slug, "location": loc,
            "remote": _remote(loc + " " + (cats.get("commitment") or "")),
            "url": j.get("hostedUrl", ""), "source": "lever", "posted_date": posted,
            "salary": None, "employment_type": cats.get("commitment", "unknown") or "unknown",
            "description": desc[:4000], "tags": [cats.get("team", "")] if cats.get("team") else [],
            "fit_rank": 0,
        })
    return out


def ashby(token):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true"
    out = []
    for j in _get(url).get("jobs", []):
        title = j.get("title", "")
        loc = j.get("location", "") or ""
        desc = _strip_html(j.get("descriptionHtml") or j.get("descriptionPlain") or "")
        posted = (j.get("publishedDate") or j.get("publishedAt") or "")[:10] or None
        out.append({
            "id": _id("ashby", token, title, loc),
            "title": title, "company": token, "location": loc,
            "remote": "remote" if j.get("isRemote") else _remote(loc + " " + desc),
            "url": j.get("jobUrl") or j.get("applyUrl") or "",
            "source": "ashby", "posted_date": posted, "salary": None,
            "employment_type": j.get("employmentType", "unknown") or "unknown",
            "description": desc[:4000],
            "tags": [j.get("department", "")] if j.get("department") else [], "fit_rank": 0,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--greenhouse", default="", help="comma-separated board tokens")
    ap.add_argument("--lever", default="", help="comma-separated company slugs")
    ap.add_argument("--ashby", default="", help="comma-separated Ashby board names")
    ap.add_argument("--query", default="", help="case-insensitive title filter")
    a = ap.parse_args()

    jobs = []
    for fn, names in ((greenhouse, a.greenhouse), (lever, a.lever), (ashby, a.ashby)):
        for tok in [t.strip() for t in names.split(",") if t.strip()]:
            try:
                jobs += fn(tok)
            except Exception as e:
                print(f"[ats_boards] {fn.__name__} '{tok}' failed: {e}", file=sys.stderr)

    if a.query:
        q = a.query.lower()
        jobs = [j for j in jobs if q in j["title"].lower()]

    json.dump(jobs, sys.stdout, indent=2)
    print(f"\n[ats_boards] {len(jobs)} jobs", file=sys.stderr)


if __name__ == "__main__":
    main()
