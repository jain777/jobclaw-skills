#!/usr/bin/env python3
"""Teamtailor adapter — pulls postings from a company's public jobs RSS feed
(`https://<company>.teamtailor.com/jobs.rss`). No key (the RSS is public). Teamtailor is
common at European + startup employers; resolve the `<company>` slug via sniff_careers.py.

Usage:
  python3 teamtailor.py --companies "lego,acme" --query "engineer"

Prints a JSON array in the JobClaw job schema. Per-company errors go to stderr, never abort
the batch. (Adapter contract identified from the career-ops project.)
"""
import argparse, hashlib, html, json, re, sys, urllib.request
from xml.etree import ElementTree as ET

UA = {"User-Agent": "JobClaw-Skills/0.0 (+https://github.com/jobclaw)"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _strip_html(s):
    if not s:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").strip()


def _id(company, title, loc):
    return hashlib.sha1(f"teamtailor|{company}|{title}|{loc}".lower().encode()).hexdigest()[:16]


def _remote(text):
    t = (text or "").lower()
    if "remote" in t:
        return "remote"
    if "hybrid" in t:
        return "hybrid"
    return "unknown"


def company(slug):
    xml = _get(f"https://{slug}.teamtailor.com/jobs.rss")
    root = ET.fromstring(xml)
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = _strip_html(item.findtext("description") or "")
        # Teamtailor RSS often puts location in a namespaced/extra tag or in the description.
        loc = ""
        for child in item:
            tag = child.tag.split("}")[-1].lower()
            if tag in ("location", "region", "city") and child.text:
                loc = child.text.strip()
                break
        pub = (item.findtext("pubDate") or "")
        out.append({
            "id": _id(slug, title, loc),
            "title": title, "company": slug, "location": loc,
            "remote": _remote(loc + " " + title + " " + desc),
            "url": link, "source": "teamtailor",
            "posted_date": None,  # pubDate is RFC822; leave null rather than mis-parse
            "salary": None, "employment_type": "unknown",
            "description": desc[:4000], "tags": [], "fit_rank": 0,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--companies", required=True, help="comma-separated Teamtailor slugs")
    ap.add_argument("--query", default="", help="case-insensitive title filter")
    a = ap.parse_args()

    jobs = []
    for slug in [c.strip() for c in a.companies.split(",") if c.strip()]:
        try:
            jobs += company(slug)
        except Exception as e:
            print(f"[teamtailor] '{slug}' failed: {e}", file=sys.stderr)

    if a.query:
        q = a.query.lower()
        jobs = [j for j in jobs if q in j["title"].lower()]

    json.dump(jobs, sys.stdout, indent=2)
    print(f"\n[teamtailor] {len(jobs)} jobs", file=sys.stderr)


if __name__ == "__main__":
    main()
