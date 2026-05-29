#!/usr/bin/env python3
"""Discover which ATS (Greenhouse, Lever, or Ashby) a company uses by probing the public
APIs with token variants guessed from the company name. Lets find-jobs build a per-user
ATS-direct target list from the profile's target companies/industries — no hand-curated
tokens. For companies this misses, use sniff_careers.py on their careers URL instead.

Usage:
  python3 discover_ats.py --companies "Vercel,Brex,Ramp,Linear,Mercury"

Prints JSON: [{"company","ats","token","jobs_count"}] for hits only. Misses go to stderr.
"""
import argparse, json, re, sys, urllib.request

UA = {"User-Agent": "JobClaw-Skills/0.0 (+https://github.com/jobclaw)"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def try_greenhouse(token):
    try:
        return len(_get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs").get("jobs", [])) or None
    except Exception:
        return None


def try_lever(token):
    try:
        d = _get(f"https://api.lever.co/v0/postings/{token}?mode=json")
        return len(d) if isinstance(d, list) and d else None
    except Exception:
        return None


def try_ashby(token):
    try:
        return len(_get(f"https://api.ashbyhq.com/posting-api/job-board/{token}").get("jobs", [])) or None
    except Exception:
        return None


def try_smartrecruiters(token):
    try:
        d = _get(f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=1")
        return d.get("totalFound") or (len(d.get("content", [])) or None)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--companies", required=True, help="comma-separated company names")
    a = ap.parse_args()

    out = []
    for name in [c.strip() for c in a.companies.split(",") if c.strip()]:
        token = normalize(name)
        hit = None
        # Ashby + SmartRecruiters board names are often capitalized; try a few variants.
        variants = list(dict.fromkeys([name, name.replace(" ", ""), token]))
        if (n := try_greenhouse(token)):
            hit = ("greenhouse", token, n)
        elif (n := try_lever(token)):
            hit = ("lever", token, n)
        else:
            for variant in variants:
                if (n := try_ashby(variant)):
                    hit = ("ashby", variant, n)
                    break
            else:
                for variant in variants:
                    if (n := try_smartrecruiters(variant)):
                        hit = ("smartrecruiters", variant, n)
                        break
        if hit:
            out.append({"company": name, "ats": hit[0], "token": hit[1], "jobs_count": hit[2]})
        else:
            print(f"[discover_ats] no GH/Lever/Ashby match for '{name}' — try sniff_careers.py",
                  file=sys.stderr)

    json.dump(out, sys.stdout, indent=2)
    print(f"\n[discover_ats] {len(out)} matched", file=sys.stderr)


if __name__ == "__main__":
    main()
