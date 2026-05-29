#!/usr/bin/env python3
"""Shared helper for the fetch-to-verify step and the Cutshort adapter.

Most job boards (Cutshort, Greenhouse-hosted pages, many ATS/aggregator *posting*
pages) embed a schema.org `JobPosting` as JSON-LD — which carries the real JD
`description`, `datePosted` (freshness) and `validThrough` (expiry). Parsing it
lets us, with zero keys and stdlib only, (a) confirm a URL is a real individual
posting (not a search/landing page), (b) date it, and (c) capture the true JD
instead of a search snippet.

Stdlib only. Imported by verify_postings.py and cutshort.py.
"""
import datetime as _dt
import html as _html
import json
import re
import urllib.request

UA = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36")}

# URL shapes that are search/category/landing pages, not a single req.
_AGGREGATOR_RE = re.compile(
    r"(/q-|SRCH|[?&]q=|/search|/jobs(/|$|\?)|-jobs(-in-|/|$)|/l-|glassdoor\.[^/]+/Job/)",
    re.I,
)
# Text that means a real posting is no longer open.
_CLOSED_MARKERS = (
    "no longer accepting applications", "this job has expired", "posting has expired",
    "position has been filled", "applications are closed", "job is no longer available",
    "this position is closed", "no longer available",
)


def fetch(url, timeout=25):
    """GET a URL with a browser UA; returns decoded HTML (raises on error)."""
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def clean_html(s):
    """JSON-LD descriptions are HTML — strip tags, unescape entities, collapse space."""
    if not s:
        return ""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", str(s))
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|li|div|h[1-6])>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = _html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def iso_to_date(s):
    """'2026-05-25T07:25:26Z' or '2026-05-25' -> 'YYYY-MM-DD' (None if unparseable)."""
    if not s or not isinstance(s, str):
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s.strip())
    return m.group(0) if m else None


def _iter_jsonld(html):
    """Yield every parsed JSON-LD object (flattening @graph)."""
    for block in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                            html, re.S | re.I):
        try:
            data = json.loads(block.strip())
        except Exception:  # noqa: BLE001
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and isinstance(it.get("@graph"), list):
                yield from (g for g in it["@graph"] if isinstance(g, dict))
            elif isinstance(it, dict):
                yield it


def _salary_str(base):
    """Normalize a schema.org MonetaryAmount to a short display string, or None."""
    if not isinstance(base, dict):
        return None
    cur = base.get("currency") or ""
    val = base.get("value") or {}
    if isinstance(val, dict):
        lo, hi = val.get("minValue"), val.get("maxValue")
        unit = (val.get("unitText") or "").lower()
        per = {"year": "/yr", "month": "/mo", "hour": "/hr"}.get(unit, "")
        if lo and hi:
            return f"{cur} {lo}–{hi}{per}".strip()
        if lo or hi:
            return f"{cur} {lo or hi}{per}".strip()
    return None


def _place_str(loc):
    """schema.org jobLocation (Place or list) -> 'City, Region' display string."""
    if isinstance(loc, list):
        parts = [_place_str(x) for x in loc]
        return "; ".join(p for p in parts if p)
    if isinstance(loc, dict):
        addr = loc.get("address") or {}
        if isinstance(addr, dict):
            bits = [addr.get("addressLocality"), addr.get("addressRegion"),
                    addr.get("addressCountry")]
            return ", ".join(str(b) for b in bits if b)
    return ""


def normalize_jobposting(jp):
    """Map a JSON-LD JobPosting dict to our normalized fields (subset of job-schema)."""
    org = jp.get("hiringOrganization") or {}
    et = jp.get("employmentType")
    if isinstance(et, list):
        et = ", ".join(str(x) for x in et)
    return {
        "title": jp.get("title") or "",
        "company": (org.get("name") if isinstance(org, dict) else org) or "",
        "location": _place_str(jp.get("jobLocation")),
        "posted_date": iso_to_date(jp.get("datePosted")),
        "valid_through": iso_to_date(jp.get("validThrough")),
        "salary": _salary_str(jp.get("baseSalary")),
        "employment_type": (et or "").lower().replace("_", "-") or "unknown",
        "description": clean_html(jp.get("description")),
        "tags": [s for s in (jp.get("skills") or "").split(",") if s][:12]
        if isinstance(jp.get("skills"), str) else [],
    }


def first_jobposting(html):
    """Return the normalized first JSON-LD JobPosting in `html`, or None."""
    for it in _iter_jsonld(html):
        if it.get("@type") == "JobPosting" or (
            isinstance(it.get("@type"), list) and "JobPosting" in it["@type"]
        ):
            return normalize_jobposting(it)
    return None


def looks_like_aggregator(url):
    """True if the URL is a search / category / landing page (not a single req)."""
    return bool(_AGGREGATOR_RE.search(url or ""))


def has_closed_marker(html):
    """True if the page text says the posting is closed/expired/filled."""
    low = html.lower()
    return any(m in low for m in _CLOSED_MARKERS)


def status_for(posted_date, valid_through, today, max_age_days, closed=False):
    """Classify freshness: active | stale | expired | closed."""
    if closed:
        return "closed"
    if valid_through and valid_through < today:
        return "expired"
    if posted_date:
        try:
            d0 = _dt.date.fromisoformat(posted_date)
            d1 = _dt.date.fromisoformat(today)
            if (d1 - d0).days > max_age_days:
                return "stale"
        except ValueError:
            pass
    return "active"
