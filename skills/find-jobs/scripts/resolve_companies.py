#!/usr/bin/env python3
"""Batch-resolve companies.csv into a verified board cache (resolved.json) so find-jobs never
re-probes 1000 companies per run. Reuses discover_ats.py (token guessing) and sniff_careers.py
(careers-page detection, incl. the fetchable flag).

Per company (skipped if cached & fresh under --stale-only):
  1. CSV already has ats+token   → seed cache, status=verified, resolved_via=csv
  2. discover_ats token guesses  → greenhouse/lever/ashby/smartrecruiters
  3. sniff the careers_url       → any detected ATS (+ fetchable flag), incl. workday
  4. nothing                     → status=unresolved

Polite: ThreadPoolExecutor capped (default 6), per-request jitter, urllib timeouts, 1 retry.
Incremental + resumable: the cache is rewritten after each completion, so a killed run is safe
to re-run (it continues from unresolved/expired rows).

Usage:
  python3 resolve_companies.py --csv knowledge/companies/companies.csv \
      --cache knowledge/companies/resolved.json --region US,IN --sector technology \
      --max 200 --concurrency 6 --refresh-older-than 30 --stale-only
"""
import argparse, csv, json, os, random, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import discover_ats as D          # noqa: E402
from sniff_careers import sniff   # noqa: E402

FETCHABLE = {"greenhouse", "lever", "ashby", "workday", "smartrecruiters", "teamtailor"}
BOARD_URL = {
    "greenhouse": "https://boards.greenhouse.io/{t}",
    "lever": "https://jobs.lever.co/{t}",
    "ashby": "https://jobs.ashbyhq.com/{t}",
    "smartrecruiters": "https://jobs.smartrecruiters.com/{t}",
    "teamtailor": "https://{t}.teamtailor.com",
}
_lock = threading.Lock()


def _board(ats, token, board_url=""):
    return {"ats": ats, "token": token,
            "board_url": board_url or BOARD_URL.get(ats, "").format(t=token),
            "fetchable": ats in FETCHABLE}


def _discover(name, domain):
    """Token-guess greenhouse/lever/ashby/smartrecruiters (mirrors discover_ats.main)."""
    token = D.normalize(name)
    variants = list(dict.fromkeys([name, name.replace(" ", ""), token]))
    if D.try_greenhouse(token):
        return _board("greenhouse", token)
    if D.try_lever(token):
        return _board("lever", token)
    for v in variants:
        if D.try_ashby(v):
            return _board("ashby", v)
    for v in variants:
        if D.try_smartrecruiters(v):
            return _board("smartrecruiters", v)
    return None


def resolve_row(row, today):
    name = row.get("name", "").strip()
    rec = {"name": name, "region": row.get("region", "").strip(),
           "sector": row.get("sector", "").strip(), "boards": [],
           "status": "unresolved", "resolved_via": None, "checked_at": today}

    # 1. CSV-verified token
    ats, token = row.get("ats", "").strip().lower(), row.get("token", "").strip()
    if ats and token:
        rec["boards"] = [_board(ats, token)]
        rec["status"] = "verified" if ats in FETCHABLE else "detected_unfetchable"
        rec["resolved_via"] = "csv"
        return rec

    time.sleep(random.uniform(0.05, 0.25))  # politeness jitter

    # 2. discover
    try:
        b = _discover(name, row.get("domain", "").strip())
    except Exception:
        b = None
    if b:
        rec["boards"] = [b]
        rec["status"] = "verified"
        rec["resolved_via"] = "discover"
        return rec

    # 3. sniff the careers page
    careers = row.get("careers_url", "").strip() or (
        f"https://{row['domain'].strip()}/careers" if row.get("domain", "").strip() else "")
    if careers:
        try:
            s = sniff(careers if careers.startswith("http") else "https://" + careers)
        except Exception:
            s = None
        if s:
            rec["boards"] = [{"ats": s["ats"], "token": s["token"],
                              "board_url": s["board_url"], "fetchable": s["fetchable"]}]
            rec["status"] = "verified" if s["fetchable"] else "detected_unfetchable"
            rec["resolved_via"] = "sniff"
            return rec
    return rec


def is_fresh(rec, today, max_age):
    if not rec or rec.get("status") == "unresolved":
        return False
    checked = rec.get("checked_at")
    if not checked:
        return False
    try:
        age = (date.fromisoformat(today) - date.fromisoformat(checked)).days
    except ValueError:
        return False
    return age < max_age


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--region", default="", help="comma filter, e.g. US,IN")
    ap.add_argument("--sector", default="", help="comma filter of sector vocab")
    ap.add_argument("--keys", default="", help="comma filter of specific company keys")
    ap.add_argument("--max", type=int, default=0, help="cap rows resolved this pass (0 = all)")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--refresh-older-than", type=int, default=30, help="re-resolve entries older than N days")
    ap.add_argument("--stale-only", action="store_true", help="skip rows already fresh in the cache")
    ap.add_argument("--today", default=date.today().isoformat())
    a = ap.parse_args()

    regions = {x.strip().upper() for x in a.region.split(",") if x.strip()}
    sectors = {x.strip().lower() for x in a.sector.split(",") if x.strip()}
    keys = {x.strip().lower() for x in a.keys.split(",") if x.strip()}

    with open(a.csv, newline="") as f:
        rows = list(csv.DictReader(f))

    cache = {"version": 1, "generated_at": a.today, "companies": {}}
    if os.path.exists(a.cache):
        try:
            with open(a.cache) as f:
                cache = json.load(f)
            cache.setdefault("companies", {})
        except json.JSONDecodeError:
            pass
    companies = cache["companies"]

    todo = []
    for r in rows:
        key = (r.get("key") or "").strip().lower()
        if not key:
            continue
        if regions and r.get("region", "").strip().upper() not in regions:
            continue
        if sectors and r.get("sector", "").strip().lower() not in sectors:
            continue
        if keys and key not in keys:
            continue
        if a.stale_only and is_fresh(companies.get(key), a.today, a.refresh_older_than):
            continue
        todo.append((key, r))
        if a.max and len(todo) >= a.max:
            break

    def write_cache():
        cache["generated_at"] = a.today
        with open(a.cache, "w") as f:
            json.dump(cache, f, indent=2)

    print(f"[resolve] {len(todo)} companies to resolve (concurrency {a.concurrency})", file=sys.stderr)
    done = 0
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        futs = {ex.submit(resolve_row, r, a.today): key for key, r in todo}
        for fut in as_completed(futs):
            key = futs[fut]
            try:
                companies[key] = fut.result()
            except Exception as e:
                print(f"[resolve] {key} errored: {e}", file=sys.stderr)
                continue
            done += 1
            with _lock:
                write_cache()  # incremental + resumable
            if done % 25 == 0:
                print(f"[resolve] {done}/{len(todo)} done", file=sys.stderr)

    write_cache()
    verified = sum(1 for c in companies.values() if c.get("status") == "verified")
    unfetch = sum(1 for c in companies.values() if c.get("status") == "detected_unfetchable")
    unresolved = sum(1 for c in companies.values() if c.get("status") == "unresolved")
    print(f"[resolve] cache now: {verified} verified, {unfetch} detected-unfetchable, "
          f"{unresolved} unresolved ({len(companies)} total)", file=sys.stderr)


if __name__ == "__main__":
    main()
