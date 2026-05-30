#!/usr/bin/env python3
"""Offline smoke tests for jobclaw-skills — no network, no API keys, stdlib only.

Run from the repo root:  python3 tests/smoke.py

Checks, in order:
  1. compile      — py_compile every script under skills/ and knowledge/
  2. jobposting   — _jobposting.py pure functions (JSON-LD parse, freshness, aggregator)
  3. extract_links— extract_links.py on a synthetic PDF (finds embedded URIs, status ok)
  4. jobstore     — jobstore.py merge + filter (first_seen/is_new, recency)
  4b. prerank     — prerank.py deterministic relevance sort (top-N, undated-neutral, no context leak)
  5. answer       — answer.py --validate-pair contract check
  6. to_rendercv  — build_cv_document on a minimal JSON-Resume (no rendercv needed)
  7. fixtures     — all email + offer fixtures parse and carry their _expected/offer blocks

Exit code 0 only if every check passes.
"""
import json, os, subprocess, sys, tempfile, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"
PY = sys.executable
results = []  # (name, ok, detail)


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def run(args, **kw):
    return subprocess.run([PY, *args], capture_output=True, text=True, cwd=ROOT, **kw)


# 1. compile gate -----------------------------------------------------------
def check_compile():
    print("1. compile")
    scripts = sorted(
        p for d in ("skills", "knowledge") for p in (ROOT / d).rglob("*.py")
        if ".venv" not in p.parts and "__pycache__" not in p.parts
    )
    bad = []
    for p in scripts:
        r = subprocess.run([PY, "-m", "py_compile", str(p)], capture_output=True, text=True)
        if r.returncode != 0:
            bad.append(f"{p.relative_to(ROOT)}: {r.stderr.strip().splitlines()[-1:] }")
    record(f"compile {len(scripts)} scripts", not bad, "; ".join(bad)[:200] if bad else f"{len(scripts)} ok")


# 2. _jobposting pure functions --------------------------------------------
def check_jobposting():
    print("2. jobposting")
    sys.path.insert(0, str(ROOT / "skills" / "find-jobs" / "scripts"))
    try:
        import _jobposting as J
    except Exception as e:
        record("import _jobposting", False, str(e)); return
    html = (FIX / "jobposting-sample.html").read_text()
    jp = J.first_jobposting(html)
    norm = J.normalize_jobposting(jp) if jp else {}
    record("parse JSON-LD JobPosting", bool(jp) and "Senior Product Manager" in (norm.get("title", "")),
           f"title={norm.get('title')!r} company={norm.get('company')!r}")
    # freshness: fresh / stale / expired
    fresh = J.status_for("2026-05-20", "2026-08-20", "2026-05-29", 45)
    stale = J.status_for("2023-04-17", None, "2026-05-29", 45)
    expired = J.status_for("2026-01-01", "2026-02-01", "2026-05-29", 365)
    record("status_for fresh→active", fresh == "active", f"got {fresh}")
    record("status_for old→stale", stale == "stale", f"got {stale}")
    record("status_for past validThrough→expired", expired == "expired", f"got {expired}")
    record("aggregator URL detected", J.looks_like_aggregator("https://www.glassdoor.com/Job/SRCH_KO0,5.htm") is True
           and J.looks_like_aggregator("https://jobs.lever.co/acme/123") is False)


# 3. extract_links on a synthetic PDF --------------------------------------
def check_extract_links():
    print("3. extract_links")
    r = run(["skills/build-profile/scripts/extract_links.py", str(FIX / "sample-resume.pdf")])
    try:
        out = json.loads(r.stdout)
    except Exception:
        record("extract_links runs", False, f"non-JSON stdout: {r.stdout[:120]}"); return
    urls = out.get("urls", [])
    record("extract_links status ok", out.get("status") == "ok", f"status={out.get('status')}")
    record("extract_links finds embedded URIs", any("linkedin" in u for u in urls) and any("github" in u for u in urls),
           f"{len(urls)} urls")
    record("extract_links classifies linkedin", out.get("classified", {}).get("linkedin", "").startswith("https://"))


# 4. jobstore merge + filter ------------------------------------------------
def check_jobstore():
    print("4. jobstore")
    jobs = [
        {"id": "a1", "title": "PM", "company": "X", "posted_date": "2026-05-20"},
        {"id": "b2", "title": "SWE", "company": "Y", "posted_date": "2023-01-01"},
        {"id": "c3", "title": "Designer", "company": "Z", "posted_date": None},
    ]
    with tempfile.TemporaryDirectory() as d:
        jf = pathlib.Path(d) / "jobs.json"; store = pathlib.Path(d) / "seen.json"
        jf.write_text(json.dumps(jobs))
        r1 = run(["skills/find-jobs/scripts/jobstore.py", "merge", "--in", str(jf),
                  "--store", str(store), "--today", "2026-05-29"])
        merged = json.loads(r1.stdout)
        all_new = all(j.get("is_new") for j in merged) and all(j.get("first_seen") == "2026-05-29" for j in merged)
        record("jobstore merge stamps is_new/first_seen", all_new, f"{sum(j.get('is_new') for j in merged)}/3 new")
        # second merge → none new
        r2 = run(["skills/find-jobs/scripts/jobstore.py", "merge", "--in", str(jf),
                  "--store", str(store), "--today", "2026-05-30"])
        none_new = not any(j.get("is_new") for j in json.loads(r2.stdout))
        record("jobstore merge re-run → 0 new", none_new)
        # filter drops the 2023 posting, keeps undated by default
        r3 = run(["skills/find-jobs/scripts/jobstore.py", "filter", "--in", str(jf),
                  "--max-age-days", "30", "--today", "2026-05-29"])
        kept = {j["id"] for j in json.loads(r3.stdout)}
        record("jobstore filter drops stale, keeps undated", kept == {"a1", "c3"}, f"kept={sorted(kept)}")


# 4b. prerank deterministic relevance --------------------------------------
def check_prerank():
    print("4b. prerank")
    jobs_f = FIX / "jobs" / "prerank-input.json"
    tgt_f = FIX / "jobs" / "prerank-target.json"
    base = ["skills/find-jobs/scripts/prerank.py", "--in", str(jobs_f), "--target", str(tgt_f),
            "--today", "2026-05-29"]
    r1 = run(base + ["--top-n", "25"])
    ranked = json.loads(r1.stdout)
    order = [j["id"] for j in ranked]
    record("prerank: strong AI role ranks #1", order and order[0] == "strong", f"order={order}")
    record("prerank: off-role (accountant) ranks last", order and order[-1] == "offrole", f"order={order}")
    record("prerank: undated relevant job beats off-role (not bottomed for being undated)",
           "undated" in order and "offrole" in order and order.index("undated") < order.index("offrole"))
    record("prerank: output carries no `context` field", "context" not in r1.stdout)
    # deterministic across runs
    r2 = run(base + ["--top-n", "25"])
    record("prerank: deterministic across runs", r1.stdout == r2.stdout)
    # top-n trims
    rN = run(base + ["--top-n", "2"])
    record("prerank: --top-n 2 returns exactly 2", len(json.loads(rN.stdout)) == 2)
    # remote_only penalizes onsite — widen the strong(remote) vs pm(onsite) gap
    scores = {j["id"]: j["prerank_score"] for j in ranked}
    with tempfile.TemporaryDirectory() as d:
        ro = pathlib.Path(d) / "t.json"
        ro.write_text(json.dumps({**json.loads(tgt_f.read_text()), "remote_only": True}))
        rro = json.loads(run(["skills/find-jobs/scripts/prerank.py", "--in", str(jobs_f),
                              "--target", str(ro), "--today", "2026-05-29"]).stdout)
        ro_scores = {j["id"]: j["prerank_score"] for j in rro}
        gap0 = scores["strong"] - scores["pm"]
        gap1 = ro_scores["strong"] - ro_scores["pm"]
        record("prerank: remote_only deprioritizes onsite (gap widens)", gap1 > gap0, f"{gap0}→{gap1}")
    # graceful degrade on garbage
    g = subprocess.run([PY, "skills/find-jobs/scripts/prerank.py", "--today", "2026-05-29"],
                       input='{"not":"a list"}', capture_output=True, text=True, cwd=ROOT)
    record("prerank: garbage input → [] exit 0", g.returncode == 0 and json.loads(g.stdout) == [])


# 5. answer.py validator ----------------------------------------------------
def check_answer():
    print("5. answer validator")
    qin = {"questions": [
        {"id": "q1", "type": "yes_no", "text": "Authorized to work in the US?"},
        {"id": "q2", "type": "numeric", "text": "Years of experience?"},
    ]}
    aout = {"answers": [
        {"id": "q1", "type": "yes_no", "value": "Yes", "source_field": "work_auth"},
        {"id": "q2", "type": "numeric", "value": "5", "source_field": "years_exp"},
    ]}
    with tempfile.TemporaryDirectory() as d:
        i = pathlib.Path(d) / "in.json"; o = pathlib.Path(d) / "out.json"
        i.write_text(json.dumps(qin)); o.write_text(json.dumps(aout))
        r = run(["skills/answer-application-questions/scripts/answer.py", "--validate-pair", str(i), str(o)])
        record("answer.py --validate-pair accepts valid pair", r.returncode == 0,
               (r.stdout + r.stderr).strip().splitlines()[-1:][0] if (r.stdout or r.stderr) else "")


# 6. to_rendercv build_cv_document -----------------------------------------
def check_to_rendercv():
    print("6. to_rendercv")
    sys.path.insert(0, str(ROOT / "skills" / "render-resume" / "scripts"))
    try:
        import to_rendercv as T
    except Exception as e:
        record("import to_rendercv", False, str(e)); return
    data = {
        "meta": {"track": "software", "region": "US"},
        "basics": {"name": "Jane Doe", "label": "Software Engineer",
                   "email": "jane@example.com", "phone": "+1 415 555 0100",
                   "profiles": [{"network": "GitHub", "url": "https://github.com/janedoe"}]},
        "work": [{"company": "Acme", "position": "Engineer", "startDate": "2022-01", "endDate": "present",
                  "highlights": ["Shipped X improving Y by 30%."]}],
        "education": [{"institution": "MIT", "area": "CS", "studyType": "BS",
                       "startDate": "2018", "endDate": "2022"}],
        "skills": [{"name": "Languages", "keywords": ["Python", "Go"]}],
    }
    try:
        doc = T.build_cv_document(data, theme="engineeringresumes", paper="letter", region="US")
        ok = isinstance(doc, dict) and "cv" in doc and doc["cv"].get("name") == "Jane Doe"
        record("to_rendercv builds a valid document", ok, f"keys={sorted(doc)[:4]}")
    except Exception as e:
        record("to_rendercv builds a valid document", False, str(e))


# 7. pipeline + orchestration wiring ---------------------------------------
def check_pipeline():
    print("7. pipeline/orchestration")
    record("knowledge/pipeline.md exists", (ROOT / "knowledge" / "pipeline.md").exists())
    aj = ROOT / "skills" / "apply-to-job" / "SKILL.md"
    record("apply-to-job skill exists", aj.exists() and "name: apply-to-job" in (aj.read_text() if aj.exists() else ""))
    rules = (ROOT / "skills" / "_shared" / "RULES.md").read_text()
    record("RULES.md has known-info gate + current.json", "Known-info gate" in rules and "jobs/current.json" in rules)
    # every skill ends with a Next steps block
    skills = sorted(p for p in (ROOT / "skills").glob("*/SKILL.md"))
    missing = [p.parent.name for p in skills if "## Next steps" not in p.read_text()]
    record(f"all {len(skills)} skills have a Next-steps block", not missing, "missing: " + ",".join(missing))
    # the JD-reuse convention reaches the consumers
    consumers = ["score-fit", "tailor-resume", "write-cover-letter", "answer-application-questions", "research-company"]
    no_ref = [c for c in consumers if "jobs/current.json" not in (ROOT / "skills" / c / "SKILL.md").read_text()]
    record("consumers read jobs/current.json", not no_ref, "missing: " + ",".join(no_ref))


# 8. fixture integrity ------------------------------------------------------
def check_fixtures():
    print("8. fixtures")
    emails = sorted((FIX / "emails").glob("*.json"))
    bad = []
    for e in emails:
        try:
            d = json.loads(e.read_text())
            if "_expected" not in d:
                bad.append(f"{e.name}: no _expected")
        except Exception as ex:
            bad.append(f"{e.name}: {ex}")
    record(f"{len(emails)} email fixtures parse + have _expected", not bad and len(emails) == 12, "; ".join(bad)[:160])
    offers = sorted((FIX / "offers").glob("*.json"))
    obad = []
    for o in offers:
        try:
            json.loads(o.read_text())
        except Exception as ex:
            obad.append(f"{o.name}: {ex}")
    record(f"{len(offers)} offer fixtures parse", not obad and len(offers) == 2, "; ".join(obad)[:160])


def main():
    print(f"jobclaw-skills smoke tests (root: {ROOT})\n")
    for fn in (check_compile, check_jobposting, check_extract_links, check_jobstore,
               check_prerank, check_answer, check_to_rendercv, check_pipeline, check_fixtures):
        try:
            fn()
        except Exception as e:
            record(fn.__name__, False, f"crashed: {e}")
        print()
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"{'='*48}\nSMOKE: {passed}/{total} checks passed")
    if passed != total:
        print("FAILURES:")
        for n, ok, d in results:
            if not ok:
                print(f"  - {n}: {d}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
