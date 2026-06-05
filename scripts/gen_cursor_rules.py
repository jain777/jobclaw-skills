#!/usr/bin/env python3
"""Generate Cursor rules (.cursor/rules/*.mdc) from the portable SKILL.md skills.

Cursor's native rule format is .mdc, not SKILL.md. This bridges the two: each skill becomes
an Agent-Requested rule (description-gated, alwaysApply:false) whose body is a THIN POINTER to
the real SKILL.md — so the skill stays the single source of truth and the .mdc never drifts.

Also emits 00-jobclaw.mdc (alwaysApply:true) carrying the always-on repo context.

Pure stdlib. Idempotent — rerun whenever skills change.

Usage:
    python3 scripts/gen_cursor_rules.py            # write .cursor/rules/*.mdc
    python3 scripts/gen_cursor_rules.py --check     # exit 1 if output is stale (no write)
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO, "skills")
RULES_DIR = os.path.join(REPO, ".cursor", "rules")


def parse_frontmatter(text):
    """Minimal YAML-frontmatter parser: handles `key: value` and folded `key: >` blocks.

    Good enough for our SKILL.md frontmatter (no nesting, no flow collections)."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip("\n").splitlines()
    data = {}
    i = 0
    key_re = re.compile(r"^(\S[^:]*):\s*(.*)$")
    while i < len(block):
        line = block[i]
        m = key_re.match(line)
        if not m:
            i += 1
            continue
        key, val = m.group(1).strip(), m.group(2).strip()
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            # Folded/literal block scalar: gather more-indented following lines.
            parts = []
            i += 1
            while i < len(block) and (block[i].strip() == "" or block[i][:1] in (" ", "\t")):
                parts.append(block[i].strip())
                i += 1
            data[key] = " ".join(p for p in parts if p).strip()
            continue
        data[key] = val
        i += 1
    return data


def collect_skills():
    skills = []
    for name in sorted(os.listdir(SKILLS_DIR)):
        if name.startswith("_"):
            continue  # _shared etc.
        skill_md = os.path.join(SKILLS_DIR, name, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        with open(skill_md, encoding="utf-8") as f:
            fm = parse_frontmatter(f.read())
        if not fm.get("name") or not fm.get("description"):
            sys.stderr.write(f"WARN: {name}/SKILL.md missing name/description — skipped\n")
            continue
        skills.append(fm)
    return skills


def skill_rule(fm):
    name = fm["name"]
    desc = fm["description"].rstrip(".")
    when = fm.get("when_to_use", "").strip()
    # Cursor reads `description` to decide whether to attach the rule (Agent-Requested mode).
    gate = desc + ("" if not when else f". {when.rstrip('.')}") + "."
    gate = " ".join(gate.split())
    body = (
        f"---\n"
        f"description: {gate}\n"
        f"alwaysApply: false\n"
        f"---\n\n"
        f"# {name}\n\n"
        f"This task maps to the **`{name}`** skill in this repo. Read "
        f"[`skills/{name}/SKILL.md`](../../skills/{name}/SKILL.md) and follow it exactly — "
        f"it is the single source of truth for this workflow.\n\n"
        f"Before producing any output, obey the shared rules in "
        f"[`skills/_shared/RULES.md`](../../skills/_shared/RULES.md) "
        f"(never fabricate, never echo the `context:` block, region-pack-first, no emoji, "
        f"known-info gate).\n"
    )
    return f"{name}.mdc", body


def always_rule():
    body = (
        "---\n"
        "description: JobClaw job-hunt skills — repo conventions and hard rules.\n"
        "alwaysApply: true\n"
        "---\n\n"
        "# jobclaw-skills\n\n"
        "This repo is a set of portable job-hunt Agent Skills. The runtime-neutral guide is "
        "[`AGENTS.md`](../../AGENTS.md); per-skill workflows live in "
        "[`skills/<name>/SKILL.md`](../../skills). When a task matches a skill's description, read "
        "that SKILL.md and follow it.\n\n"
        "Always obey [`skills/_shared/RULES.md`](../../skills/_shared/RULES.md): never fabricate; "
        "never echo the profile `context:` block; read `knowledge/regions/<code>.md` before "
        "geography-varying text; no emoji; never re-ask what the profile or a sidecar already holds. "
        "Skills compose via JSON sidecars (`jobs/current.json`, `scores/`, `resumes/`, `companies/`, "
        "`inbox/`), not direct calls — see [`knowledge/pipeline.md`](../../knowledge/pipeline.md).\n"
    )
    return "00-jobclaw.mdc", body


def main():
    check = "--check" in sys.argv
    skills = collect_skills()
    outputs = dict([always_rule()] + [skill_rule(fm) for fm in skills])

    if check:
        stale = []
        for fname, content in outputs.items():
            path = os.path.join(RULES_DIR, fname)
            if not os.path.isfile(path) or open(path, encoding="utf-8").read() != content:
                stale.append(fname)
        # Flag orphaned rule files too.
        existing = set(os.listdir(RULES_DIR)) if os.path.isdir(RULES_DIR) else set()
        orphans = [f for f in existing if f.endswith(".mdc") and f not in outputs]
        if stale or orphans:
            sys.stderr.write(f"STALE: {sorted(stale)}  ORPHANS: {sorted(orphans)}\n")
            return 1
        print(f"OK: {len(outputs)} Cursor rules up to date")
        return 0

    os.makedirs(RULES_DIR, exist_ok=True)
    # Remove orphaned rules so renamed/deleted skills don't linger.
    for f in (os.listdir(RULES_DIR) if os.path.isdir(RULES_DIR) else []):
        if f.endswith(".mdc") and f not in outputs:
            os.remove(os.path.join(RULES_DIR, f))
    for fname, content in outputs.items():
        with open(os.path.join(RULES_DIR, fname), "w", encoding="utf-8") as f:
            f.write(content)
    print(f"Wrote {len(outputs)} Cursor rules to {os.path.relpath(RULES_DIR, REPO)}/ "
          f"({len(skills)} skills + 1 always-apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
