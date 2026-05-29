#!/usr/bin/env python3
"""Sniff a company's careers page to detect which ATS it embeds and extract the board
token/endpoint. Catches companies discover_ats.py misses (token != company name).

Detects, with a `fetchable` flag telling find-jobs whether a direct adapter exists:
  fetchable=true  → greenhouse / lever / ashby (ats_boards.py), workday (workday.py),
                    smartrecruiters (smartrecruiters.py), teamtailor (teamtailor.py)
  fetchable=false → icims / taleo / oracle / successfactors — no clean public JSON API;
                    find-jobs falls back to SerpApi (company-filtered) or firecrawl.py.

Usage:
  python3 sniff_careers.py --urls "https://ramp.com/careers,https://nvidia.com/en-us/about-nvidia/careers/"

Prints JSON: [{"url","ats","token","board_url","fetchable"}] for detections. JS-only career
pages that don't reference the ATS in their HTML can't be sniffed (use firecrawl.py / WebFetch).
"""
import argparse, json, re, sys, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; JobClaw-Skills/0.0; +https://github.com/jobclaw)"}

# (ats, regex, fetchable). Order matters — more specific hosts first.
PATTERNS = [
    ("greenhouse",     re.compile(r"(?:boards|job-boards|boards-api)\.greenhouse\.io/(?:embed/job_board\?for=)?([a-z0-9_]+)", re.I), True),
    ("lever",          re.compile(r"jobs\.lever\.co/([a-z0-9_-]+)", re.I), True),
    ("ashby",          re.compile(r"jobs\.ashbyhq\.com/([a-z0-9_-]+)", re.I), True),
    ("smartrecruiters", re.compile(r"(?:careers|jobs)\.smartrecruiters\.com/([A-Za-z0-9_-]+)", re.I), True),
    ("teamtailor",     re.compile(r"([a-z0-9-]+)\.teamtailor\.com", re.I), True),
    ("icims",          re.compile(r"(?:careers-)?([a-z0-9-]+)\.icims\.com", re.I), False),
    ("taleo",          re.compile(r"([a-z0-9-]+)\.taleo\.net", re.I), False),
    ("oracle",         re.compile(r"([a-z0-9-]+)\.oraclecloud\.com/hcmUI/CandidateExperience", re.I), False),
    ("successfactors", re.compile(r"(?:([a-z0-9-]+)\.successfactors\.(?:com|eu)|jobs\.sap\.com|career(?:s)?\.sap\.com)", re.I), False),
]
WORKDAY = re.compile(r"([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z-]+/)?(?:wday/cxs/[^/]+/)?([a-z0-9_-]+)", re.I)
_SKIP = {"embed", "v1", "boards", "job_board", "en-us", "www", "careers"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore"), r.geturl()


def sniff(url):
    try:
        body, final = fetch(url)
    except Exception as e:
        print(f"[sniff] {url} failed: {e}", file=sys.stderr)
        return None
    hay = final + "\n" + body
    wd = WORKDAY.search(hay)
    if wd:
        tenant, dc, site = wd.group(1), wd.group(2), wd.group(3)
        base = f"https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"
        return {"url": url, "ats": "workday", "token": f"{tenant}/{site}",
                "board_url": base, "fetchable": True}
    for ats, pat, fetchable in PATTERNS:
        m = pat.search(hay)
        if not m:
            continue
        token = next((g for g in m.groups() if g), "")  # SAP branch may have no capture group
        if token.lower() in _SKIP:
            continue
        return {"url": url, "ats": ats, "token": token,
                "board_url": m.group(0), "fetchable": fetchable}
    print(f"[sniff] {url}: no known ATS in HTML (may be JS-rendered)", file=sys.stderr)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", required=True, help="comma-separated careers URLs")
    a = ap.parse_args()
    out = [r for u in a.urls.split(",") if u.strip() for r in [sniff(u.strip())] if r]
    json.dump(out, sys.stdout, indent=2)
    print(f"\n[sniff] {len(out)} detected", file=sys.stderr)


if __name__ == "__main__":
    main()
