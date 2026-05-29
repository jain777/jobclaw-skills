#!/usr/bin/env python3
"""Career-path transition discovery via Google Custom Search (CSE). Stdlib only.

Reads GOOGLE_API_KEY + CSE_ID from env. Runs 4 query templates restricted to LinkedIn
(plus one broad one), filters for transition relevance, dedups, prints a JSON array of
{name, title, link, snippet}. The map-career-path SKILL falls back to WebSearch with the
same query templates when keys aren't set.

Usage:
  python3 career_paths.py --current "Product Manager" --target "Director of Product" --region US
"""
import argparse, json, os, sys, urllib.parse, urllib.request

UA = {"User-Agent": "JobClaw-Skills/0.0 (+https://github.com/jobclaw)"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def cse(api_key, cx, q, n=10):
    params = {"key": api_key, "cx": cx, "q": q, "num": min(n, 10)}
    url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode(params)
    try:
        return _get(url).get("items", []) or []
    except Exception as e:
        print(f"[career_paths] CSE query failed for '{q[:60]}…': {e}", file=sys.stderr)
        return []


def relevant(item, current, target):
    snip = ((item.get("snippet") or "") + " " + (item.get("title") or "")).lower()
    return current.lower() in snip and target.lower() in snip


def queries(current, target):
    return [
        f'"{current}" "{target}" site:linkedin.com/in',
        f'from "{current}" to "{target}" site:linkedin.com',
        f'"{target}" "previously {current}" site:linkedin.com',
        f'career transition "{current}" "{target}"',
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--region", default="")  # unused for now; reserved for future locale tuning
    a = ap.parse_args()

    key, cx = os.environ.get("GOOGLE_API_KEY"), os.environ.get("CSE_ID")
    if not key or not cx:
        print("[career_paths] GOOGLE_API_KEY / CSE_ID not set — use the SKILL's WebSearch fallback.",
              file=sys.stderr)
        json.dump([], sys.stdout)
        return

    seen, out = set(), []
    for q in queries(a.current, a.target):
        for item in cse(key, cx, q):
            link = item.get("link", "")
            if not link or link in seen:
                continue
            if not relevant(item, a.current, a.target):
                continue
            seen.add(link)
            title = item.get("title", "")
            name = title.split(" - ")[0] if " - " in title else title
            out.append({"name": name, "title": title, "link": link,
                        "snippet": item.get("snippet", "")})
            if len(out) >= 10:
                break
        if len(out) >= 10:
            break

    out = out[:10]
    json.dump(out, sys.stdout, indent=2)
    print(f"\n[career_paths] {len(out)} transitions", file=sys.stderr)


if __name__ == "__main__":
    main()
