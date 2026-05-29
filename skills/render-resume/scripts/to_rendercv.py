#!/usr/bin/env python3
"""Convert a JSON-Resume intermediate (see ../reference/json-resume-schema.md)
into a rendercv input document (a plain dict, JSON-serializable -> valid YAML).

rendercv validates strictly and fails the whole render on any bad field, so the
guiding rule here is *never emit something that won't validate*: header social
links are only emitted when their extracted username passes the same regex
rendercv enforces; everything else (the long tail, unknown networks, anything
that won't parse cleanly) lands in a body "Links" section as a Markdown link, so
every link in the profile survives and stays clickable without ever hard-failing.

Stdlib only. Imported by render.py; also runnable for debugging:
    python3 to_rendercv.py --data resumes/x.json [--theme ...] [--paper ...]
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"))
import _common as C  # noqa: E402

# ---------------------------------------------------------------------------
# Dates: JSON-Resume freeform strings -> rendercv ISO (YYYY / YYYY-MM) or freeform
# ---------------------------------------------------------------------------

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
_PRESENT = {"present", "current", "now", "ongoing", "till date", "to date"}


def _to_iso(s):
    """Return an ISO date string rendercv accepts, 'present', or None if unparseable."""
    if not s:
        return None
    s = str(s).strip()
    if s.lower() in _PRESENT:
        return "present"
    m = re.fullmatch(r"(\d{4})-(\d{1,2})(?:-(\d{1,2}))?", s)
    if m:
        y, mo = m.group(1), int(m.group(2))
        return f"{y}-{mo:02d}" if not m.group(3) else f"{y}-{mo:02d}-{int(m.group(3)):02d}"
    if re.fullmatch(r"\d{4}", s):
        return s
    m = re.fullmatch(r"(\d{1,2})[/-](\d{4})", s)  # MM/YYYY or MM-YYYY
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    m = re.fullmatch(r"([A-Za-z]+)\.?\s+(\d{4})", s)  # Mon YYYY / Month YYYY
    if m and m.group(1).lower()[:4] in _MONTHS or (m and m.group(1).lower()[:3] in _MONTHS):
        key = m.group(1).lower()
        mo = _MONTHS.get(key[:4]) or _MONTHS.get(key[:3])
        return f"{m.group(2)}-{mo:02d}"
    return None


def _date_fields(start, end):
    """Map (startDate, endDate) -> a dict of rendercv date keys.

    Both parse -> start_date/end_date range. Otherwise fall back to a freeform
    `date` string so the render never fails on an exotic date format.
    """
    if start and end:
        sd, ed = _to_iso(start), _to_iso(end)
        if sd and sd != "present" and ed:
            return {"start_date": sd, "end_date": ed}
        return {"date": f"{start} – {end}"}
    if start and not end:
        return {"date": str(start)}
    if end and not start:
        return {"date": str(end)}
    return {}


# ---------------------------------------------------------------------------
# Social networks: our open link keys -> rendercv's fixed enum + username
# ---------------------------------------------------------------------------

# our profile key (lowercased) -> rendercv network enum name
_NETWORK_ENUM = {
    "linkedin": "LinkedIn", "github": "GitHub", "gitlab": "GitLab",
    "instagram": "Instagram", "orcid": "ORCID", "mastodon": "Mastodon",
    "stackoverflow": "StackOverflow", "researchgate": "ResearchGate",
    "youtube": "YouTube", "scholar": "Google Scholar", "googlescholar": "Google Scholar",
    "google_scholar": "Google Scholar", "telegram": "Telegram", "leetcode": "Leetcode",
    "twitter": "X", "x": "X", "bluesky": "Bluesky", "reddit": "Reddit", "imdb": "IMDB",
}

# username validators mirroring rendercv/schema/models/cv/social_network.py so we
# only emit social_networks entries that will pass rendercv's own validation.
_USERNAME_OK = {
    "ORCID": lambda u: re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", u),
    "StackOverflow": lambda u: re.fullmatch(r"\d+/[^/]+", u),
    "Mastodon": lambda u: re.fullmatch(r"@[^@]+@[^@]+", u),
    "Bluesky": lambda u: re.fullmatch(
        r"([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", u),
    "Reddit": lambda u: re.fullmatch(r"[a-zA-Z0-9_-]{3,23}", u),
    "IMDB": lambda u: re.fullmatch(r"nm\d{7}", u),
    "YouTube": lambda u: not u.startswith("@"),
}


def _strip_url(url):
    """Return (host_without_www, path) for a URL, scheme-insensitive."""
    s = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", url.strip())
    s = s.split("?", 1)[0].split("#", 1)[0]
    host, _, path = s.partition("/")
    return host.lower().lstrip("www.") if host.lower().startswith("www.") else host.lower(), path.strip("/")


def _extract_username(enum_name, url):
    """Best-effort username for a rendercv social network. None -> route to Links."""
    host, path = _strip_url(url)
    segs = [p for p in path.split("/") if p]
    try:
        if enum_name == "LinkedIn":
            # .../in/<user> or .../pub/<user>
            if "in" in segs:
                u = segs[segs.index("in") + 1]
            elif "pub" in segs:
                u = segs[segs.index("pub") + 1]
            else:
                u = segs[-1] if segs else ""
        elif enum_name == "Google Scholar":
            m = re.search(r"user=([^&/]+)", url)
            u = m.group(1) if m else ""
        elif enum_name == "StackOverflow":
            # .../users/<id>/<name>
            if "users" in segs:
                i = segs.index("users")
                u = "/".join(segs[i + 1:i + 3])
            else:
                u = ""
        elif enum_name == "Mastodon":
            # https://<domain>/@<user>  ->  @<user>@<domain>
            user = segs[-1].lstrip("@") if segs else ""
            u = f"@{user}@{host}" if user and host else ""
        elif enum_name == "YouTube":
            u = (segs[-1] if segs else "").lstrip("@")
        elif enum_name in ("Telegram", "Reddit", "Leetcode"):
            # t.me/<user>, reddit.com/user/<user>, leetcode.com/u/<user>
            skip = {"user", "u"}
            tail = [s for s in segs if s.lower() not in skip]
            u = tail[-1] if tail else ""
        else:
            # GitHub, GitLab, Instagram, X, ORCID, Bluesky, ResearchGate, IMDB
            u = segs[0] if segs else ""
    except (IndexError, ValueError):
        return None
    u = u.strip()
    if not u:
        return None
    validator = _USERNAME_OK.get(enum_name)
    if validator and not validator(u):
        return None
    return u


# keys that should populate cv.website rather than a social/Links entry
_WEBSITE_KEYS = ("portfolio", "website", "personal", "homepage", "site", "blog")


def _ensure_scheme(url):
    return url if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url.strip()) else "https://" + url.strip()


def _pretty(key):
    return key.replace("_", " ").replace("-", " ").strip().title()


# ---------------------------------------------------------------------------
# Top-level conversion
# ---------------------------------------------------------------------------

def build_cv_document(data, *, theme, paper, region):
    """Return a rendercv document dict (cv/design/locale) from a JSON-Resume dict."""
    basics = data.get("basics", {}) or {}
    meta = data.get("meta", {}) or {}

    cv = {}
    if basics.get("name"):
        cv["name"] = basics["name"]
    if basics.get("label"):
        cv["headline"] = basics["label"]
    loc = basics.get("location", {}) or {}
    locstr = ", ".join(x for x in (loc.get("city"), loc.get("region")) if x)
    if locstr:
        cv["location"] = locstr
    if basics.get("email") and "@" in str(basics["email"]):
        cv["email"] = basics["email"]
    if basics.get("phone"):
        # A hyphen right after the country code (e.g. "+91-7014486372") defeats
        # rendercv's phonenumbers parse — it drops "+91" and reformats as a local
        # number with a leading 0. Turn that hyphen into a space so it parses clean.
        cv["phone"] = re.sub(r"^(\+\d{1,3})-", r"\1 ", str(basics["phone"]).strip())

    # --- Collect link keys (profiles[] + other{}), excluding email/phone --------
    links = {}  # key(lower) -> url
    for p in basics.get("profiles", []) or []:
        net = (p.get("network") or "").strip().lower()
        url = (p.get("url") or "").strip()
        if net and url and net not in ("email", "phone"):
            links.setdefault(net, url)
    for k, v in (basics.get("other") or {}).items():
        k = (k or "").strip().lower()
        if k and v and k not in ("email", "phone"):
            links.setdefault(k, str(v).strip())

    order = C.resolve_contact_order(
        meta.get("track"),
        sidecar_order=meta.get("contact_order"),
        profile_priority=meta.get("contact_priority"),
    )
    ordered_keys = C.order_link_keys(links.keys(), order, contact_hidden=meta.get("contact_hidden"))

    social_networks = []
    other_links = []  # (label, url) -> Links section
    website_set = False
    for key in ordered_keys:
        url = links[key]
        enum_name = _NETWORK_ENUM.get(key)
        if enum_name:
            username = _extract_username(enum_name, url)
            if username:
                social_networks.append({"network": enum_name, "username": username})
                continue
        if key in _WEBSITE_KEYS and not website_set:
            cv["website"] = _ensure_scheme(url)
            website_set = True
            continue
        other_links.append((_pretty(key), _ensure_scheme(url)))

    if social_networks:
        cv["social_networks"] = social_networks

    # --- Sections (insertion order == render order) -----------------------------
    sections = {}
    if basics.get("summary"):
        sections["Summary"] = [basics["summary"]]

    work = data.get("work", []) or []
    if work:
        entries = []
        for w in work:
            e = {}
            if w.get("company"):
                e["company"] = w["company"]
            if w.get("position"):
                e["position"] = w["position"]
            if w.get("location"):
                e["location"] = w["location"]
            e.update(_date_fields(w.get("startDate"), w.get("endDate")))
            hl = [h for h in (w.get("highlights") or []) if h]
            if hl:
                e["highlights"] = hl
            entries.append(e)
        sections["Experience"] = entries

    skills = data.get("skills", []) or []
    if skills:
        rows = []
        for s in skills:
            # OneLineEntry requires both label and details.
            label = s.get("name") or ""
            details = ", ".join(k for k in (s.get("keywords") or []) if k)
            if label or details:
                rows.append({"label": label, "details": details})
        if rows:
            sections["Skills"] = rows

    edu = data.get("education", []) or []
    if edu:
        entries = []
        for e in edu:
            # EducationEntry requires institution + area; degree is optional.
            # When the field of study is blank, promote the degree onto the area
            # line so the entry reads "Institution, B.Tech" (no trailing comma).
            ent = {"institution": e.get("institution") or "", "area": ""}
            area, study = e.get("area"), e.get("studyType")
            if area:
                ent["area"] = area
                if study:
                    ent["degree"] = study
            elif study:
                ent["area"] = study
            if e.get("location"):
                ent["location"] = e["location"]
            ent.update(_date_fields(e.get("startDate"), e.get("endDate")))
            if e.get("score"):
                ent["highlights"] = [e["score"]]
            entries.append(ent)
        sections["Education"] = entries

    projs = data.get("projects", []) or []
    if projs:
        entries = []
        for p in projs:
            ent = {}
            if p.get("name"):
                ent["name"] = p["name"]
            if p.get("description"):
                ent["summary"] = p["description"]
            hl = [h for h in (p.get("highlights") or []) if h]
            if hl:
                ent["highlights"] = hl
            if ent:
                entries.append(ent)
        if entries:
            sections["Projects"] = entries

    # Free-form bullet sections (Achievements, Activities, Certifications, …).
    # Each {"name": "...", "bullets": [...]} renders as a section of bullet entries.
    for sec in data.get("extra_sections", []) or []:
        name = (sec.get("name") or "").strip()
        bullets = [b for b in (sec.get("bullets") or []) if b]
        if name and bullets:
            sections[name] = [{"bullet": b} for b in bullets]

    if other_links:
        sections["Links"] = [
            {"label": label, "details": f"[{re.sub(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', '', url).rstrip('/')}]({url})"}
            for label, url in other_links
        ]

    # India-relevant extras (only if upstream populated them)
    extras = []
    if meta.get("noticePeriod"):
        extras.append({"label": "Notice period", "details": str(meta["noticePeriod"])})
    if meta.get("expectedCtc"):
        extras.append({"label": "Expected CTC", "details": str(meta["expectedCtc"])})
    if meta.get("currentCtc"):
        extras.append({"label": "Current CTC", "details": str(meta["currentCtc"])})
    if extras:
        sections["Additional"] = extras

    if sections:
        cv["sections"] = sections

    page_size = "a4" if paper == "a4" else "us-letter"
    document = {
        "cv": cv,
        "design": {"theme": theme, "page": {"size": page_size}},
        "locale": {"language": "english"},
    }
    return document


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--theme", default=C.DEFAULT_THEME)
    ap.add_argument("--paper", default="us-letter")
    args = ap.parse_args()
    with open(args.data) as f:
        d = json.load(f)
    doc = build_cv_document(d, theme=args.theme, paper=args.paper,
                            region=(d.get("meta") or {}).get("region", "US"))
    print(json.dumps(doc, indent=2, ensure_ascii=False))
