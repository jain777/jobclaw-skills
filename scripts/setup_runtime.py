#!/usr/bin/env python3
"""Wire this skills repo into each agent runtime's discovery path.

`skills/` at the repo root is the single source of truth. Runtimes find skills in different
places, so this links/generates the right pointer per runtime:

    codex     .agents/skills        -> skills   (symlink; Codex walks up for .agents/skills)
    cursor    .cursor/rules/*.mdc    (generated from SKILL.md via gen_cursor_rules.py)
    claude    .claude/skills        -> skills   (symlink; parity with the plugin layout)
    hermes    ./skills              (read natively; --global also links ~/.hermes/skills)
    openclaw  ./skills              (read natively in the workspace; guidance printed)

Pure stdlib. Idempotent. Symlinks where possible; `--copy` (or auto-fallback on permission
errors, e.g. Windows without developer mode) duplicates the tree instead.

Usage:
    python3 scripts/setup_runtime.py [all|codex|cursor|claude|hermes|openclaw ...]
                                     [--global] [--copy] [--dry-run]
"""
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")
RUNTIMES = ["codex", "cursor", "claude", "hermes", "openclaw"]


def log(msg):
    print(msg)


def link_dir(target, link_path, copy, dry):
    """Create link_path -> target (symlink, or copy fallback). target/link_path are absolute."""
    rel = os.path.relpath(link_path, REPO)
    if os.path.islink(link_path):
        if os.path.realpath(link_path) == os.path.realpath(target):
            log(f"  ok    {rel} -> skills (already linked)")
            return
        if not dry:
            os.unlink(link_path)
    elif os.path.exists(link_path):
        log(f"  skip  {rel} exists and is not our symlink — leaving it alone")
        return
    if dry:
        log(f"  plan  {rel} -> {os.path.relpath(target, os.path.dirname(link_path))}")
        return
    os.makedirs(os.path.dirname(link_path), exist_ok=True)
    if copy:
        shutil.copytree(target, link_path)
        log(f"  copy  {rel}/ (copied skills tree)")
        return
    try:
        rel_target = os.path.relpath(target, os.path.dirname(link_path))
        os.symlink(rel_target, link_path, target_is_directory=True)
        log(f"  link  {rel} -> {rel_target}")
    except (OSError, NotImplementedError) as e:
        shutil.copytree(target, link_path)
        log(f"  copy  {rel}/ (symlink unavailable: {e.__class__.__name__}; copied instead)")


def setup_codex(opts):
    log("codex:")
    link_dir(os.path.join(REPO, "skills"), os.path.join(REPO, ".agents", "skills"),
             opts["copy"], opts["dry"])
    if opts["glob"]:
        link_dir(os.path.join(REPO, "skills"), os.path.join(HOME, ".agents", "skills"),
                 opts["copy"], opts["dry"])
    log("  -> Codex scans .agents/skills up the tree; invoke with /skills or $mention.")


def setup_cursor(opts):
    log("cursor:")
    if opts["dry"]:
        log("  plan  regenerate .cursor/rules/*.mdc from SKILL.md")
        return
    gen = os.path.join(REPO, "scripts", "gen_cursor_rules.py")
    rc = os.system(f'{sys.executable} "{gen}"')
    if rc != 0:
        log("  WARN  gen_cursor_rules.py failed")
    log("  -> Cursor auto-attaches rules by description, or invoke with @rule-name.")


def setup_claude(opts):
    log("claude:")
    link_dir(os.path.join(REPO, "skills"), os.path.join(REPO, ".claude", "skills"),
             opts["copy"], opts["dry"])
    log("  -> Or install as a plugin (see README). Invoke with /skill-name.")


def setup_hermes(opts):
    log("hermes:")
    log("  ok    Hermes reads ./skills in the project natively.")
    if opts["glob"]:
        link_dir(os.path.join(REPO, "skills"), os.path.join(HOME, ".hermes", "skills"),
                 opts["copy"], opts["dry"])
    log("  -> Auto-discovered by description; or run from this repo as the project root.")


def setup_openclaw(opts):
    log("openclaw:")
    log("  ok    OpenClaw reads the workspace skills/ dir natively (same SKILL.md standard).")
    log("  -> Run OpenClaw with this repo as the workspace, or `openclaw skills install` per-skill.")


HANDLERS = {
    "codex": setup_codex, "cursor": setup_cursor, "claude": setup_claude,
    "hermes": setup_hermes, "openclaw": setup_openclaw,
}


def main(argv):
    flags = {a for a in argv if a.startswith("--")}
    targets = [a for a in argv if not a.startswith("--")]
    if not targets or "all" in targets:
        targets = RUNTIMES
    bad = [t for t in targets if t not in HANDLERS]
    if bad:
        sys.stderr.write(f"Unknown runtime(s): {bad}. Choose from: all, {', '.join(RUNTIMES)}\n")
        return 2
    opts = {"copy": "--copy" in flags, "glob": "--global" in flags, "dry": "--dry-run" in flags}
    if opts["dry"]:
        log("(dry run — no changes written)\n")
    for t in targets:
        HANDLERS[t](opts)
    log("\nAll set. See docs/RUNTIMES.md for invocation details per runtime.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
