#!/usr/bin/env python3
"""Persistent cross-run dedup + recency for find-jobs. Job ids are deterministic hashes
(see reference/job-schema.md), so cross-run dedup is an id-set check against jobs/seen.json.

Two subcommands:

  merge  — stamp each job with first_seen (preserved across runs) and is_new (id unseen
           before this run), update last_seen in the store, and print the enriched array.
    python3 jobstore.py merge --in jobs/found-2026-05-29.json --store jobs/seen.json --today 2026-05-29

  filter — drop jobs older than --max-age-days by posted_date. Undated jobs are kept by
           default (schema says don't guess dates); --drop-undated to exclude them.
    python3 jobstore.py filter --in jobs/found-2026-05-29.json --max-age-days 30 --today 2026-05-29

Both read the array from --in (or stdin) and print the result array to stdout. --today is
passed in (scripts shouldn't read the clock); defaults to the newest posted_date seen, else
the store is just not date-stamped.
"""
import argparse, json, sys
from datetime import date, timedelta


def _load(path):
    if not path or path == "-":
        return json.load(sys.stdin)
    with open(path) as f:
        return json.load(f)


def _load_store(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _parse_iso(s):
    try:
        return date.fromisoformat(s[:10])
    except (TypeError, ValueError):
        return None


def cmd_merge(a):
    jobs = _load(a.infile)
    store = _load_store(a.store)
    today = a.today
    for j in jobs:
        jid = j.get("id")
        if not jid:
            continue
        rec = store.get(jid)
        if rec:
            j["first_seen"] = rec.get("first_seen")
            j["is_new"] = False
            rec["last_seen"] = today or rec.get("last_seen")
        else:
            j["first_seen"] = today
            j["is_new"] = True
            store[jid] = {"first_seen": today, "last_seen": today,
                          "title": j.get("title", ""), "company": j.get("company", "")}
    if a.store and a.store != "-":
        with open(a.store, "w") as f:
            json.dump(store, f, indent=2)
    new_count = sum(1 for j in jobs if j.get("is_new"))
    json.dump(jobs, sys.stdout, indent=2)
    print(f"\n[jobstore] merged {len(jobs)} jobs — {new_count} new, store has {len(store)} ids",
          file=sys.stderr)


def cmd_filter(a):
    jobs = _load(a.infile)
    today = _parse_iso(a.today) if a.today else None
    if today is None:
        # fall back to the newest posted_date in the batch so filtering is still deterministic
        dates = [d for d in (_parse_iso(j.get("posted_date")) for j in jobs) if d]
        today = max(dates) if dates else None
    if today is None:
        json.dump(jobs, sys.stdout, indent=2)
        print("[jobstore] filter: no dates available — passed through unchanged", file=sys.stderr)
        return
    cutoff = today - timedelta(days=a.max_age_days)
    kept = []
    dropped = 0
    for j in jobs:
        d = _parse_iso(j.get("posted_date"))
        if d is None:
            if a.drop_undated:
                dropped += 1
                continue
            kept.append(j)
        elif d >= cutoff:
            kept.append(j)
        else:
            dropped += 1
    json.dump(kept, sys.stdout, indent=2)
    print(f"\n[jobstore] filter: kept {len(kept)}, dropped {dropped} older than {a.max_age_days}d "
          f"(cutoff {cutoff})", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("merge")
    m.add_argument("--in", dest="infile", default="-")
    m.add_argument("--store", default="jobs/seen.json")
    m.add_argument("--today", default="", help="YYYY-MM-DD for first_seen/last_seen stamps")
    m.set_defaults(func=cmd_merge)

    f = sub.add_parser("filter")
    f.add_argument("--in", dest="infile", default="-")
    f.add_argument("--max-age-days", type=int, default=30)
    f.add_argument("--today", default="", help="YYYY-MM-DD reference date (default: newest posted_date)")
    f.add_argument("--drop-undated", action="store_true", help="also drop jobs with no posted_date")
    f.set_defaults(func=cmd_filter)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
