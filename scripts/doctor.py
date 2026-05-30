#!/usr/bin/env python3
"""Dependency preflight for jobclaw-skills — run it BEFORE the skills need anything, so a
missing dependency is surfaced (and installed) up front instead of mid-flow.

  python3 scripts/doctor.py            # human-readable status + exact install commands
  python3 scripts/doctor.py --json     # machine-readable (for a skill to branch on)
  python3 scripts/doctor.py --require rendercv   # exit 1 if that hard dep is missing

What it checks:
  * Python 3 (the runtime for every script) — always present if this runs.
  * rendercv (+ Pillow)  — the ONLY install-required dependency, needed by render-resume /
    tailor-resume (PDF) and review-render (visual QA). Resolved on PATH or in
    skills/render-resume/.venv. If missing, the resume skills produce content/YAML but not a PDF.
  * Optional API keys (.env) — purely informational; every key is optional and the relevant
    adapter skips gracefully when it's absent.
  * Playwright MCP — optional; only used by build-profile link enrichment when the session
    exposes it. Not installable from here (it's a Claude Code / agent session feature).

Exit 0 unless --require names a missing dependency. Stdlib only.
"""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / "skills" / "render-resume" / ".venv"
VENV_PY = VENV / "bin" / "python"
VENV_RENDERCV = VENV / "bin" / "rendercv"

RENDERCV_INSTALL = (
    f"python3 -m venv {VENV.relative_to(ROOT)} && "
    f"{(VENV / 'bin' / 'pip').relative_to(ROOT)} install \"rendercv[full]\""
)
OPTIONAL_KEYS = [
    ("ADZUNA_APP_ID", "find-jobs — Adzuna aggregator"),
    ("ADZUNA_APP_KEY", "find-jobs — Adzuna aggregator"),
    ("SERPAPI_KEY", "find-jobs — SerpApi Google Jobs"),
    ("FIRECRAWL_API_KEY", "find-jobs — Firecrawl scrape fallback / link enrichment"),
    ("GOOGLE_API_KEY", "research-company / map-career-path — Google CSE"),
    ("CSE_ID", "research-company / map-career-path — Google CSE"),
]


def _rendercv_status():
    """Return (ok, how, detail). Checks the binary AND that the venv python has rendercv+PIL."""
    on_path = shutil.which("rendercv")
    if on_path:
        return True, "PATH", on_path
    if VENV_RENDERCV.exists():
        try:
            subprocess.run([str(VENV_PY), "-c", "import rendercv, PIL"],
                           check=True, capture_output=True, timeout=30)
            return True, "venv", str(VENV_RENDERCV)
        except Exception:
            return False, "venv-broken", "venv exists but rendercv/Pillow won't import — reinstall"
    return False, "missing", "not installed"


def _read_env_keys():
    env = dict(os.environ)
    envfile = ROOT / ".env"
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    return {k: bool(env.get(k)) for k, _ in OPTIONAL_KEYS}


def collect():
    ok, how, detail = _rendercv_status()
    keys = _read_env_keys()
    return {
        "python": {"ok": True, "version": sys.version.split()[0]},
        "rendercv": {"ok": ok, "how": how, "detail": detail, "install": None if ok else RENDERCV_INSTALL},
        "optional_keys": keys,
        "required_missing": [] if ok else ["rendercv"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--require", action="append", default=[], help="exit 1 if this dep is missing")
    a = ap.parse_args()
    rep = collect()

    if a.json:
        json.dump(rep, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print("jobclaw-skills — dependency check\n")
        print(f"  Python ............ OK ({rep['python']['version']})")
        rc = rep["rendercv"]
        if rc["ok"]:
            print(f"  rendercv (PDF) .... OK (via {rc['how']})")
        else:
            print(f"  rendercv (PDF) .... MISSING — {rc['detail']}")
            print(f"      Needed by: render-resume, tailor-resume (PDF), review-render (QA).")
            print(f"      Install once:\n        {rc['install']}")
            print(f"      Until installed, resume skills still produce markdown + the rendercv YAML,")
            print(f"      just not the PDF.")
        set_keys = [k for k, v in rep["optional_keys"].items() if v]
        unset = [k for k, v in rep["optional_keys"].items() if not v]
        print(f"\n  Optional API keys (all degrade gracefully if unset):")
        print(f"      set:   {', '.join(set_keys) or '(none)'}")
        print(f"      unset: {', '.join(unset) or '(none)'}  — add to .env to strengthen find-jobs / research.")
        print(f"\n  Playwright MCP (optional, build-profile link enrichment): used if your Claude Code")
        print(f"      session has it configured; skipped gracefully otherwise.")

    for dep in a.require:
        if dep in rep.get("required_missing", []) or (dep != "rendercv" and not rep.get(dep, {}).get("ok", True)):
            print(f"\n[doctor] required dependency missing: {dep}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
