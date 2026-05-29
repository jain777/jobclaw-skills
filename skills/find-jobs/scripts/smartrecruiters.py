#!/usr/bin/env python3
"""SmartRecruiters adapter: pull postings straight from the public Posting API. Many large
non-tech employers (retail, healthcare, manufacturing) run SmartRecruiters, so this widens
coverage well beyond the Greenhouse/Lever/Ashby startup set. No key required — the
posting-list endpoint is public.

Resolve a company identifier with discover_ats.py (it now probes SmartRecruiters) or
sniff_careers.py (careers.smartrecruiters.com/<Company>).

Usage:
  python3 smartrecruiters.py --companies "Visa,IKEA,Bosch" --query "product manager" --limit 50 [--full]

Prints a JSON array in the JobClaw job schema. Per-company errors go to stderr and never
abort the rest. --full fetches each posting's detail for a richer description (slower; N+1).
"""
import argparse, hashlib, html, json, re, sys, urllib.parse, urllib.request

UA = {"User-Agent": "JobClaw-Skills/0.0 (+https://github.com/jobclaw)", "Accept": "application/json"}
API = "https://api.smartrecruiters.com/v1/companies"


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _strip_html(s):
    if not s:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").strip()


def _id(company, title, location):
    return hashlib.sha1(f"smartrecruiters|{company}|{title}|{location}".lower().encode()).hexdigest()[:16]


def _location(loc):
    if not loc:
        return "", "unknown"
    parts = [loc.get("city"), loc.get("region"), loc.get("country")]
    text = ", ".join(p for p in parts if p)
    return text, ("remote" if loc.get("remote") else "unknown")


def _description(company_id, posting_id, summary):
    """summary text from the list entry; richer jobAd only fetched in --full mode."""
    try:
        detail = _get(f"{API}/{company_id}/postings/{posting_id}")
        sections = (detail.get("jobAd") or {}).get("sections") or {}
        chunks = [(_strip_html((sections.get(k) or {}).get("text", "")))
                  for k in ("jobDescription", "qualifications", "additionalInformation")]
        joined = "  ".join(c for c in chunks if c)
        return joined[:4000] or summary
    except Exception:
        return summary


def company(company_id, query, limit, full):
    out, offset = [], 0
    while len(out) < limit:
        params = {"limit": 100, "offset": offset}
        if query:
            params["q"] = query
        data = _get(f"{API}/{company_id}/postings?" + urllib.parse.urlencode(params))
        postings = data.get("content", [])
        if not postings:
            break
        for j in postings:
            title = j.get("name", "")
            loc_text, remote = _location(j.get("location"))
            summary = _strip_html((j.get("jobAd") or {}).get("sections", {}).get("jobDescription", {}).get("text", ""))
            pid = j.get("id", "")
            desc = _description(company_id, pid, summary) if full else summary
            out.append({
                "id": _id(company_id, title, loc_text),
                "title": title, "company": (j.get("company") or {}).get("name") or company_id,
                "location": loc_text, "remote": remote,
                "url": f"https://jobs.smartrecruiters.com/{company_id}/{pid}" if pid else "",
                "source": "smartrecruiters", "posted_date": (j.get("releasedDate") or "")[:10] or None,
                "salary": None,
                "employment_type": (j.get("typeOfEmployment") or {}).get("label", "unknown") or "unknown",
                "description": desc[:4000], "tags": [j.get("function", {}).get("label", "")] if j.get("function") else [],
                "fit_rank": 0,
            })
        offset += 100
        if offset >= data.get("totalFound", 0):
            break
    return out[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--companies", required=True, help="comma-separated SmartRecruiters company identifiers")
    ap.add_argument("--query", default="", help="case-insensitive keyword filter (server-side q)")
    ap.add_argument("--limit", type=int, default=50, help="max postings per company")
    ap.add_argument("--full", action="store_true", help="fetch each posting's full description (slower)")
    a = ap.parse_args()

    jobs = []
    for cid in [c.strip() for c in a.companies.split(",") if c.strip()]:
        try:
            jobs += company(cid, a.query, a.limit, a.full)
        except Exception as e:
            print(f"[smartrecruiters] '{cid}' failed: {e}", file=sys.stderr)

    json.dump(jobs, sys.stdout, indent=2)
    print(f"\n[smartrecruiters] {len(jobs)} jobs", file=sys.stderr)


if __name__ == "__main__":
    main()
