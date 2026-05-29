#!/usr/bin/env python3
"""Hacker News "Ask HN: Who is hiring?" adapter (free, no key). Finds the latest monthly
thread via the Algolia HN API and extracts top-level comments as job postings. Great for
startup roles. Posting format is loosely "Company | Role | Location | Remote | ...".

Usage:
  python3 hn_hiring.py --query "backend engineer" --remote true --limit 60

Prints a JSON array in the JobClaw job schema to stdout.
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
    s = s.replace("<p>", "\n").replace("<br>", "\n")
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").strip()


def _id(company, title):
    return hashlib.sha1(f"hn|{company}|{title}".lower().encode()).hexdigest()[:16]


def latest_thread_id():
    # The monthly thread is posted by user "whoishiring".
    url = "https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&query=hiring&hitsPerPage=10"
    for hit in _get(url).get("hits", []):
        if "who is hiring" in (hit.get("title", "").lower()):
            return hit["objectID"]
    raise RuntimeError("no 'Who is hiring?' thread found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="")
    ap.add_argument("--remote", default="", help="true|false to filter")
    ap.add_argument("--limit", type=int, default=60)
    a = ap.parse_args()

    try:
        tid = latest_thread_id()
        thread = _get(f"https://hn.algolia.com/api/v1/items/{tid}")
    except Exception as e:
        print(f"[hn_hiring] failed: {e}", file=sys.stderr)
        json.dump([], sys.stdout)
        return

    q = a.query.lower()
    want_remote = a.remote.lower() == "true"
    out = []
    for c in thread.get("children", []):
        text = _strip_html(c.get("text", ""))
        if not text or len(text) < 20:
            continue
        if q and q not in text.lower():
            continue
        low = text.lower()
        if want_remote and "remote" not in low:
            continue
        first = text.split("\n", 1)[0]
        parts = [p.strip() for p in re.split(r"\s*\|\s*", first) if p.strip()]
        company = parts[0] if parts else "(see post)"
        title = parts[1] if len(parts) > 1 else (a.query or "(see post)")
        location = parts[2] if len(parts) > 2 else ""
        url_m = re.search(r"https?://\S+", text)
        created = c.get("created_at_i")
        posted = (datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m-%d")
                  if created else None)
        out.append({
            "id": _id(company, title),
            "title": title[:120], "company": company[:80], "location": location[:80],
            "remote": "remote" if "remote" in low else "unknown",
            "url": url_m.group(0) if url_m else f"https://news.ycombinator.com/item?id={c.get('id')}",
            "source": "hn", "posted_date": posted, "salary": None,
            "employment_type": "unknown", "description": text[:4000], "tags": [], "fit_rank": 0,
        })
        if len(out) >= a.limit:
            break

    json.dump(out, sys.stdout, indent=2)
    print(f"\n[hn_hiring] {len(out)} postings", file=sys.stderr)


if __name__ == "__main__":
    main()
