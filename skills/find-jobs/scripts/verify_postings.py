#!/usr/bin/env python3
"""Fetch-to-verify: confirm each candidate job is a real, *live* individual posting
and capture its true JD + dates — closing the gap where the web path emitted
evergreen aggregator pages and undated, snippet-only "jobs".

For every input job (or --url), fetch the page and parse its schema.org JobPosting
JSON-LD (stdlib, no key):
  * found  -> verified=true; stamp posted_date / valid_through; replace the snippet
             `description` with the real JD; classify status (active/stale/expired/closed).
  * none + aggregator-looking URL -> status="not_a_posting" (a search/landing page).
  * none + real page             -> status="unverifiable" (likely JS-rendered;
             the orchestrator should WebFetch it as a fallback).

  python3 verify_postings.py --in jobs/found-2026-05-29.json --out jobs/found-2026-05-29.json \
          --today 2026-05-29 [--max-age-days 45] [--drop-stale]
  python3 verify_postings.py --url <posting_url> [--url ...] --today 2026-05-29

`--drop-stale` removes expired/stale/closed/not_a_posting/fetch_error entries. Without
it, everything is kept with its `status` so the orchestrator (or score-fit) can decide.
Stdlib only.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _jobposting as JP  # noqa: E402

DROP_STATUSES = {"expired", "stale", "closed", "not_a_posting", "fetch_error"}


def verify_one(job, today, max_age_days):
    """Return the job dict enriched with verification fields."""
    url = job.get("url") or ""
    out = dict(job)
    if not url:
        out.update(verified=False, live=None, status="no_url")
        return out
    try:
        html = JP.fetch(url)
    except Exception as e:  # noqa: BLE001
        out.update(verified=False, live=None, status="fetch_error",
                   verify_note=f"{type(e).__name__}: {e}")
        return out

    jp = JP.first_jobposting(html)
    if jp:
        status = JP.status_for(jp["posted_date"], jp["valid_through"], today,
                               max_age_days, closed=JP.has_closed_marker(html))
        out["verified"] = True
        out["status"] = status
        out["live"] = status == "active"
        out["posted_date"] = jp["posted_date"] or out.get("posted_date")
        out["valid_through"] = jp["valid_through"]
        # Promote the real JD; keep the old text as a snippet for traceability.
        if jp["description"]:
            if out.get("description") and out["description"] != jp["description"]:
                out["description_snippet"] = out["description"]
            out["description"] = jp["description"]
            out["jd_source"] = "jsonld"
        for k in ("title", "company", "location", "salary", "employment_type"):
            if not out.get(k) and jp.get(k):
                out[k] = jp[k]
        if jp.get("tags"):
            out["tags"] = sorted(set((out.get("tags") or []) + jp["tags"]))
        return out

    # No JobPosting JSON-LD.
    if JP.looks_like_aggregator(url):
        out.update(verified=False, live=False, status="not_a_posting")
    else:
        out.update(verified=False, live=None, status="unverifiable",
                   verify_note="no JobPosting JSON-LD; likely JS-rendered — WebFetch fallback")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", help="jobs/found-<date>.json to verify in place.")
    ap.add_argument("--url", action="append", default=[], help="Verify ad-hoc URL(s).")
    ap.add_argument("--out", help="Output path (default: stdout; or overwrite --in).")
    ap.add_argument("--today", required=True, help="YYYY-MM-DD (freshness reference).")
    ap.add_argument("--max-age-days", type=int, default=45)
    ap.add_argument("--drop-stale", action="store_true",
                    help="Remove expired/stale/closed/not_a_posting/fetch_error entries.")
    args = ap.parse_args()

    jobs = []
    if args.infile:
        with open(args.infile) as f:
            jobs = json.load(f)
    jobs += [{"url": u, "source": "verify"} for u in args.url]
    if not jobs:
        print("[verify] nothing to verify (give --in or --url)", file=sys.stderr)
        return 2

    verified = [verify_one(j, args.today, args.max_age_days) for j in jobs]

    # Summary to stderr.
    counts = {}
    for v in verified:
        counts[v["status"]] = counts.get(v["status"], 0) + 1
    print("[verify] " + ", ".join(f"{k}={n}" for k, n in sorted(counts.items())), file=sys.stderr)
    for v in verified:
        flag = "" if v.get("live") else "  <-- not live"
        print(f"[verify] {v['status']:14} {(v.get('company') or '?')[:24]:24} "
              f"{(v.get('title') or '?')[:34]:34} posted={v.get('posted_date')}{flag}", file=sys.stderr)

    if args.drop_stale:
        kept = [v for v in verified if v["status"] not in DROP_STATUSES]
        print(f"[verify] kept {len(kept)}/{len(verified)} after --drop-stale", file=sys.stderr)
        verified = kept

    out_path = args.out or args.infile
    payload = json.dumps(verified, indent=2, ensure_ascii=False)
    if out_path:
        with open(out_path, "w") as f:
            f.write(payload + "\n")
        print(f"[verify] wrote {out_path}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
