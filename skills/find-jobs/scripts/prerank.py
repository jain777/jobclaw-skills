#!/usr/bin/env python3
"""Stage-A pre-ranker for find-jobs relevance (see ../../../knowledge/relevance.md).

Cheap, DETERMINISTIC scoring + trim so the Claude-as-ranker stage (which assigns the real
`fit_rank` + `fit_reason`) only spends tokens on the top-N. Scores each job 0-100 on the
deterministic slice of the six factors — role_match / seniority / domain / keywords / recency /
location-remote — sorts desc, writes the full sorted list to --out, and prints the top-N to stdout.

  python3 prerank.py --in jobs/found.json --target target.json --today 2026-05-29 \
          --top-n 25 [--out jobs/found.json]

`--target` is a small JSON the orchestrator extracts from profile frontmatter:
  { "roles": [...], "seniority": "mid", "industries": [...], "locations": [...],
    "remote_only": false, "keywords": [...], "ai_titles": {"positive":[...],"negative":[...]} }
The AI title lists are PASSED IN (single-sourced in knowledge/ai-roles.md) — this script stays dumb.

IMPORTANT: this script NEVER reads or emits the profile `context:` block (RULES.md §2). It only
sees the small `--target` slice above. Stdlib only; degrades to passthrough on bad input.
"""
import argparse
import json
import re
import sys
from datetime import date

# True stopwords only. Seniority words are handled separately (_infer_seniority regexes the raw
# title), and role nouns (engineer/manager/…) are KEPT so "ML Engineer" still overlaps
# "Machine Learning Engineer" on "engineer". The Claude stage handles real synonyms (ML ≡ ML).
_STOP = {"the", "a", "an", "and", "or", "of", "for", "to", "in", "at", "on", "with", "&", "-"}

_SENIORITY_RANK = {"intern": 0, "fresher": 0, "junior": 1, "entry": 1, "associate": 2,
                   "mid": 3, "intermediate": 3, "senior": 4, "staff": 5, "lead": 5,
                   "principal": 6, "head": 6, "director": 7, "vp": 8, "exec": 8, "executive": 8}
_SENIORITY_WORDS = {  # words found in a JD title → inferred rank
    "intern": 0, "trainee": 0, "fresher": 0, "junior": 1, "jr": 1, "entry": 1,
    "associate": 2, "mid": 3, "senior": 4, "sr": 4, "staff": 5, "lead": 5,
    "principal": 6, "head": 6, "director": 7, "vp": 8, "chief": 8}


def _tokens(s):
    return [t for t in re.split(r"[^a-z0-9+]+", (s or "").lower()) if len(t) > 1 and t not in _STOP]


def _tokenset(s):
    return set(_tokens(s))


def _best_overlap(title_tokens, phrases):
    """Max fraction of a target phrase's tokens present in the title (0..1)."""
    best = 0.0
    for p in phrases or []:
        pt = _tokenset(p)
        if pt:
            best = max(best, len(title_tokens & pt) / len(pt))
    return best


def _infer_seniority(text):
    low = (text or "").lower()
    found = [r for w, r in _SENIORITY_WORDS.items() if re.search(r"\b" + re.escape(w) + r"\b", low)]
    return max(found) if found else None


def _recency_points(posted, today):
    """0-10; neutral (6) when undated — never bottom-ranked just for lacking a date."""
    try:
        d0 = date.fromisoformat((posted or "")[:10])
        d1 = date.fromisoformat(today[:10])
        days = (d1 - d0).days
    except (TypeError, ValueError):
        return 6.0
    if days < 0:
        return 8.0
    for lim, pts in ((14, 10.0), (30, 8.0), (45, 6.0), (90, 4.0), (180, 2.0)):
        if days <= lim:
            return pts
    return 1.0


def score_job(job, target, today):
    """Deterministic 0-100 prerank estimate. Missing target.* → that factor is NEUTRAL, not zero."""
    title = job.get("title", "") or ""
    desc = job.get("description", "") or ""
    tags = job.get("tags", []) or []
    company = job.get("company", "") or ""
    title_tok = _tokenset(title)
    blob_tok = title_tok | _tokenset(desc) | {t for tag in tags for t in _tokenset(tag)} | _tokenset(company)

    roles = target.get("roles") or []
    ai = target.get("ai_titles") or {}

    # role_match /40
    if roles:
        rm = _best_overlap(title_tok, roles)
    else:
        rm = 0.6  # neutral when no target roles
    role_pts = rm * 40
    low_title = title.lower()
    if any(p.lower() in low_title for p in (ai.get("positive") or [])):
        role_pts = min(40, role_pts + 8)
    if any(n.lower() in low_title for n in (ai.get("negative") or [])):
        role_pts = max(0, role_pts - 8)

    # seniority /15
    tgt_sen = (target.get("seniority") or "").lower().strip()
    if not tgt_sen:
        sen_pts = 0.7 * 15
    else:
        want = _SENIORITY_RANK.get(tgt_sen)
        got = _infer_seniority(title) if _infer_seniority(title) is not None else _infer_seniority(desc)
        if want is None or got is None:
            sen_pts = 0.7 * 15  # neutral if either side unknown
        else:
            gap = abs(want - got)
            sen_pts = {0: 1.0, 1: 0.7}.get(gap, 0.3 if gap == 2 else 0.1) * 15

    # domain /15
    inds = target.get("industries") or []
    if inds:
        ind_tok = {t for i in inds for t in _tokenset(i)}
        dom_pts = (1.0 if ind_tok & blob_tok else 0.2) * 15
    else:
        dom_pts = 0.6 * 15

    # keywords /15 (target.keywords + role tokens present in the JD blob)
    kw = target.get("keywords") or []
    kw_tok = {t for k in kw for t in _tokenset(k)} | {t for r in roles for t in _tokenset(r)}
    if kw_tok:
        kw_pts = (len(kw_tok & blob_tok) / len(kw_tok)) * 15
    else:
        kw_pts = 0.6 * 15

    # recency /10
    rec_pts = _recency_points(job.get("posted_date"), today)

    # location / remote /5 (+ hard deprioritize for remote_only × onsite)
    remote = (job.get("remote") or "unknown").lower()
    loc = (job.get("location") or "").lower()
    penalty = 0.0
    if target.get("remote_only"):
        loc_pts = {"remote": 5.0, "hybrid": 2.0}.get(remote, 0.0)
        if remote in ("onsite", "unknown"):
            penalty = 25.0  # deprioritize, not drop (find-jobs §4 still hard-filters)
    else:
        locs = target.get("locations") or []
        if locs and any(_tokenset(l) & _tokenset(loc) for l in locs):
            loc_pts = 5.0
        elif remote == "remote":
            loc_pts = 4.0
        else:
            loc_pts = 2.0

    total = role_pts + sen_pts + dom_pts + kw_pts + rec_pts + loc_pts - penalty
    return max(0.0, min(100.0, round(total, 1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default="-")
    ap.add_argument("--target", default="", help="JSON file with target.* slice (NO context block)")
    ap.add_argument("--today", required=True, help="YYYY-MM-DD (scripts don't read the clock)")
    ap.add_argument("--top-n", type=int, default=25)
    ap.add_argument("--out", default="", help="Write the FULL sorted list here (top-N still printed to stdout)")
    a = ap.parse_args()

    try:
        jobs = json.load(sys.stdin) if a.infile in ("", "-") else json.load(open(a.infile))
        if not isinstance(jobs, list):
            raise ValueError("input is not a JSON array")
    except Exception as e:  # noqa: BLE001 — graceful degrade, never crash
        print("[]")
        print(f"[prerank] bad input ({e}); passed through empty", file=sys.stderr)
        return 0

    target = {}
    if a.target:
        try:
            target = json.load(open(a.target)) or {}
        except Exception as e:  # noqa: BLE001
            print(f"[prerank] could not read --target ({e}); scoring with neutral target", file=sys.stderr)
    target.pop("context", None)  # belt-and-suspenders: never let a context block influence the script

    for j in jobs:
        if isinstance(j, dict):
            j["prerank_score"] = score_job(j, target, a.today)
    ranked = sorted([j for j in jobs if isinstance(j, dict)],
                    key=lambda j: (j.get("prerank_score", 0), j.get("posted_date") or "", bool(j.get("is_new"))),
                    reverse=True)

    if a.out:
        with open(a.out, "w") as f:
            json.dump(ranked, f, indent=2, ensure_ascii=False)
        print(f"[prerank] wrote full sorted list ({len(ranked)}) to {a.out}", file=sys.stderr)

    top = ranked[: a.top_n]
    print(json.dumps(top, indent=2, ensure_ascii=False))
    print(f"[prerank] scored {len(ranked)} jobs; emitted top {len(top)} "
          f"(score range {top[-1]['prerank_score'] if top else 0}–{top[0]['prerank_score'] if top else 0})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
