#!/usr/bin/env python3
"""Firecrawl fallback fetcher — for JS-rendered career pages and enterprise ATSes with no
clean public API (iCIMS, Taleo, Oracle Recruiting, SuccessFactors). Firecrawl renders the
page and returns clean markdown + links; the find-jobs skill (Claude) then extracts listings
into the job schema, exactly like the WebFetch fallback but for JS-heavy pages.

This is the routing target for sniff_careers.py detections with `fetchable: false`.

Reads FIRECRAWL_API_KEY from env. Missing key → prints {"status":"no_key"} and a stderr note.

Usage:
  python3 firecrawl.py --url "https://careers-acme.icims.com/jobs" [--query "product manager"]

Prints a JSON envelope to stdout (NOT a normalized job array — Claude parses the markdown):
  {"status":"ok|no_key|error","source":"firecrawl","url":...,"markdown":"...","links":[...],"note":...}
"""
import argparse, json, os, sys, urllib.request

API = "https://api.firecrawl.dev/v1/scrape"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="careers / listings page to render")
    ap.add_argument("--query", default="", help="role hint passed through for Claude's extraction")
    ap.add_argument("--only-main", action="store_true", help="ask Firecrawl for main content only")
    a = ap.parse_args()

    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        print("[firecrawl] FIRECRAWL_API_KEY not set — skipping.", file=sys.stderr)
        json.dump({"status": "no_key", "source": "firecrawl", "url": a.url}, sys.stdout)
        return

    payload = {"url": a.url, "formats": ["markdown", "links"], "onlyMainContent": bool(a.only_main)}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "User-Agent": "JobClaw-Skills/0.0 (+https://github.com/jobclaw)"}
    try:
        req = urllib.request.Request(API, data=json.dumps(payload).encode(), headers=headers)
        with urllib.request.urlopen(req, timeout=90) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[firecrawl] request failed: {e}", file=sys.stderr)
        json.dump({"status": "error", "source": "firecrawl", "url": a.url, "note": str(e)}, sys.stdout)
        return

    data = resp.get("data", resp) or {}
    md = data.get("markdown", "") or ""
    links = data.get("links", []) or []
    out = {
        "status": "ok", "source": "firecrawl", "url": a.url, "query": a.query,
        "markdown": md[:200000], "links": links[:500],
        "note": "Claude: extract listings from `markdown` into the job schema; use `links` for apply URLs.",
    }
    json.dump(out, sys.stdout, indent=2)
    print(f"\n[firecrawl] scraped {len(md)} chars, {len(links)} links", file=sys.stderr)


if __name__ == "__main__":
    main()
