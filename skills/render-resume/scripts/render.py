#!/usr/bin/env python3
"""Render a JSON-Resume intermediate (see ../reference/json-resume-schema.md) to a
polished PDF via **rendercv** (https://github.com/rendercv/rendercv), which uses
a Typst engine and ships 9 single-column themes with real embedded hyperlinks.

  python3 render.py --data resumes/jane.json --out resumes/jane.pdf \\
                    [--theme engineeringresumes|classic|sb2nov|...|auto] \\
                    [--paper letter|a4]

Flow: load JSON-Resume -> convert to a rendercv document (to_rendercv.py) ->
write `resumes/<name>.rendercv.yaml` (JSON is valid YAML, so no hand-quoting) ->
run `rendercv render` into a scratch build dir -> move the produced PDF to --out.

rendercv lives in the skill's isolated venv (.venv/bin/rendercv) or on PATH. If it
is not installed the .rendercv.yaml is still written and install guidance printed
(exit 0, degrade gracefully). A genuine render/validation failure exits 1.

Stdlib only.
"""
import argparse
import copy
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
TEMPLATES_DIR = os.path.join(SKILL_DIR, "templates")
sys.path.insert(0, TEMPLATES_DIR)
sys.path.insert(0, HERE)
import _common as C  # noqa: E402
import to_rendercv  # noqa: E402

VALID_THEMES = C.ALL_THEMES + ("auto",)

# Legacy --template names from the old LaTeX renderer -> closest rendercv theme,
# so pre-existing tailor-resume sidecars (template_hint) keep working.
LEGACY_THEME_ALIASES = {"jake": "classic", "deedy-single": "classic", "awesome": "moderncv"}


def _find_rendercv():
    """Resolve the rendercv binary: PATH first, then the skill's venv."""
    on_path = shutil.which("rendercv")
    if on_path:
        return on_path
    venv_bin = os.path.join(SKILL_DIR, ".venv", "bin", "rendercv")
    if os.path.isfile(venv_bin):
        return venv_bin
    return None


def _pick_theme_auto(meta):
    """Route (track, seniority) -> a built-in theme. Mirrors the old --template auto."""
    track = (meta.get("track") or "").lower()
    seniority = (meta.get("seniority") or "").lower()
    # Creative tracks + execs get the styled theme — license to stand out.
    if track in ("marketing", "design") or seniority == "exec":
        return "moderncv"  # styled; not in the ATS-safe subset (warned below)
    # Conservative + people-facing tracks -> classic (ATS-safe, clean, room for warmth).
    if track in ("finance", "quant", "sales", "customer-success", "content", "hr", "founders-office"):
        return "classic"
    if seniority in ("senior", "staff", "lead") and track == "product":
        return "classic"
    # Tech/data/ops (and untyped) default to the most ATS-aligned theme.
    return C.DEFAULT_THEME  # engineeringresumes


def _resolve_paper(arg_paper, meta, region):
    """CLI --paper > meta.paper > region default (IN -> a4, else letter)."""
    paper = arg_paper or meta.get("paper") or ("a4" if region == "IN" else "letter")
    return "a4" if str(paper).lower() in ("a4", "a4paper") else "letter"


# Optional cv contact fields we can safely drop-and-retry if rendercv rejects them.
_STRIPPABLE = ("phone", "email", "website")

# Density presets, applied to fit a page target. Each is a partial rendercv `design`
# overlay (keys verified against the ClassicTheme schema all built-in themes share).
# Auto-fit walks the ladder and stops at the FIRST (lightest) preset that meets the
# page target — so it picks the most generous spacing that still fits, which fills the
# page rather than over-compressing. Steps are deliberately fine to minimize the gap
# between "just over" and "comfortably under" (avoids large bottom whitespace).
_DENSITY = {
    "normal": {},
    "snug": {
        "page": {"top_margin": "0.65in", "bottom_margin": "0.65in",
                 "left_margin": "0.65in", "right_margin": "0.65in"},
        "typography": {"line_spacing": "0.6em", "font_size": {"body": "10pt"}},
        "sections": {"space_between_regular_entries": "1.0em",
                     "space_between_text_based_entries": "0.25em"},
    },
    "compact": {
        "page": {"top_margin": "0.55in", "bottom_margin": "0.55in",
                 "left_margin": "0.6in", "right_margin": "0.6in"},
        "typography": {"line_spacing": "0.55em", "font_size": {"body": "10pt"}},
        "sections": {"space_between_regular_entries": "0.85em",
                     "space_between_text_based_entries": "0.2em"},
        "header": {"space_below_name": "0.4cm", "space_below_headline": "0.4cm",
                   "space_below_connections": "0.4cm"},
    },
    "dense": {
        "page": {"top_margin": "0.5in", "bottom_margin": "0.5in",
                 "left_margin": "0.5in", "right_margin": "0.5in"},
        "typography": {"line_spacing": "0.5em", "font_size": {"body": "9.5pt"}},
        "sections": {"space_between_regular_entries": "0.7em",
                     "space_between_text_based_entries": "0.18em"},
        "header": {"space_below_name": "0.3cm", "space_below_headline": "0.3cm",
                   "space_below_connections": "0.3cm"},
    },
    "tight": {
        "page": {"top_margin": "0.4in", "bottom_margin": "0.4in",
                 "left_margin": "0.45in", "right_margin": "0.45in"},
        "typography": {"line_spacing": "0.45em", "font_size": {"body": "9pt"}},
        "sections": {"space_between_regular_entries": "0.6em",
                     "space_between_text_based_entries": "0.15em"},
        "header": {"space_below_name": "0.25cm", "space_below_headline": "0.25cm",
                   "space_below_connections": "0.25cm"},
    },
}
_PRESET_ORDER = ("normal", "snug", "compact", "dense", "tight")

# Applied to every render before the density preset:
#  - narrow the right-hand date/location column so bullet text gets more width
#    (fewer one/two-word overflow "widow" lines);
#  - force INTERNATIONAL phone display so the country code shows (rendercv defaults to
#    NATIONAL format, which drops e.g. "+91" and adds a leading 0 — see FINDINGS).
_BASE_DESIGN = {
    "entries": {"date_and_location_width": "3.6cm"},
    "header": {"connections": {"phone_number_format": "international"}},
}

# ---------------------------------------------------------------------------
# Industry-aware styling (accent color + font), keyed on the track.
# ---------------------------------------------------------------------------
# rendercv's default accent is rgb(0,79,144) — a corporate blue applied to the
# name, headline, connections, section titles, and links. That single blue reads
# wrong for creative tracks and is needlessly loud for conservative ones. This
# map gives each track a defensible accent + font, grounded in recruiter guidance
# (see knowledge/resume-style.md):
#   * creative (marketing/design/hr/founders): expressive but restrained — one
#     bolder NON-blue accent (burgundy/teal/forest), modern sans-serif.
#   * tech (software/product): clean, minimal — a refined slate (not the gimmicky
#     bright default blue), neutral sans-serif.
#   * conservative (finance/quant): minimal/no color (black or near-black navy) +
#     a serif face.
# All accents are mid-to-dark and saturated so they survive a grayscale print
# (light/neon accents disappear in B&W). `body` text stays black for ATS/legibility;
# only rules/titles/links/name/connections take the accent.
_ACCENT_ELEMENTS = ("name", "headline", "connections", "section_titles", "links")
_TRACK_STYLE = {
    "marketing":       {"accent": "rgb(140, 30, 62)",  "font": "Lato"},          # burgundy, modern sans
    "design":          {"accent": "rgb(13, 110, 120)",  "font": "Poppins"},      # deep teal, geometric/playful
    "hr":              {"accent": "rgb(13, 110, 120)",  "font": "Lato"},         # teal, approachable
    "founders-office": {"accent": "rgb(27, 94, 60)",    "font": "Lato"},         # forest green
    "content":         {"accent": "rgb(110, 44, 98)",   "font": "Lato"},         # plum, editorial/creative-adjacent
    "sales":           {"accent": "rgb(160, 52, 40)",   "font": "Lato"},         # brick/terracotta, confident
    "customer-success": {"accent": "rgb(20, 115, 110)", "font": "Lato"},         # teal-green, approachable
    "product":         {"accent": "rgb(36, 62, 99)",    "font": "Source Sans 3"},  # refined slate, clean
    "software":        {"accent": "rgb(36, 62, 99)",    "font": "Source Sans 3"},  # refined slate, clean
    "data":            {"accent": "rgb(36, 62, 99)",    "font": "Source Sans 3"},  # refined slate, clean (tech)
    "operations":      {"accent": "rgb(55, 71, 79)",    "font": "Source Sans 3"},  # steel blue-grey, industrial-clean
    "finance":         {"accent": "rgb(0, 0, 0)",       "font": "EB Garamond"},  # black, serif (conservative)
    "quant":           {"accent": "rgb(20, 33, 61)",    "font": "XCharter"},     # near-black navy, serif
}


def _style_overlay(meta, cli_accent=None, cli_font=None):
    """Build a `design` overlay (colors + font) from the track, with overrides.

    Precedence: CLI flag > meta.accent_color / meta.font_family > track default.
    Returns {} when nothing applies (keeps the theme's own defaults).
    """
    track = (meta.get("track") or "").lower()
    preset = _TRACK_STYLE.get(track, {})
    accent = cli_accent or meta.get("accent_color") or preset.get("accent")
    font = cli_font or meta.get("font_family") or preset.get("font")
    overlay = {}
    if accent:
        overlay["colors"] = {el: accent for el in _ACCENT_ELEMENTS}
    if font:
        overlay.setdefault("typography", {})["font_family"] = font
    return overlay


def _deep_merge(base, overlay):
    """Recursively merge dict `overlay` into dict `base` (in place); returns base."""
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def _write_yaml(document, yaml_path):
    """Write the rendercv document as JSON (a valid YAML subset — no hand-quoting)."""
    with open(yaml_path, "w") as f:
        f.write("# rendercv input — generated by render.py from a JSON-Resume intermediate.\n")
        json.dump(document, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _run_rendercv(rendercv, yaml_path, build_dir):
    """Run `rendercv render` (PDF + PNG-per-page; skip md/html). Returns (ok, error_text)."""
    shutil.rmtree(build_dir, ignore_errors=True)
    cmd = [rendercv, "render", yaml_path, "-o", build_dir, "-nomd"]  # md off also disables html
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, (e.stderr or e.stdout or str(e))
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def _count_pages(build_dir):
    """Page count = number of per-page PNGs rendercv emitted (reliable for typst PDFs)."""
    return len(glob.glob(os.path.join(build_dir, "*.png"))) or 1


def _offending_field(err):
    """Return the strippable cv field rendercv flagged (phone/email/website), else None."""
    for field in _STRIPPABLE:
        if f"cv.{field}" in err:
            return field
    return None


def _run_qa(rendercv_bin, build_dir):
    """Deterministic layout gate: run qa_report.py (needs Pillow) under the venv python
    on the build PNGs. Returns the parsed dict, or None if unavailable. Best-effort —
    never fails the render."""
    venv_py = os.path.join(SKILL_DIR, ".venv", "bin", "python")
    if not os.path.isfile(venv_py):
        venv_py = os.path.join(os.path.dirname(rendercv_bin), "python")
    qa_script = os.path.join(HERE, "qa_report.py")
    pngs = sorted(glob.glob(os.path.join(build_dir, "*.png")))
    if not (os.path.isfile(venv_py) and os.path.isfile(qa_script) and pngs):
        return None
    try:
        out = subprocess.run([venv_py, qa_script, *pngs],
                             capture_output=True, text=True, timeout=60)
        d = json.loads(out.stdout)
        return d if "pages" in d else None
    except Exception:  # noqa: BLE001
        return None


def _render_once(rendercv, document, yaml_path, build_dir):
    """Render `document`, stripping invalid optional contact fields and retrying.
    Returns (ok, error_text, page_count). Mutates `document` if a field is dropped."""
    for _ in range(len(_STRIPPABLE) + 1):
        _write_yaml(document, yaml_path)
        ok, err = _run_rendercv(rendercv, yaml_path, build_dir)
        if ok:
            return True, "", _count_pages(build_dir)
        field = _offending_field(err)
        if field and field in document.get("cv", {}):
            document["cv"].pop(field, None)
            print(f"[render] WARNING: rendercv rejected cv.{field} as invalid — "
                  f"dropping it and retrying. Fix it in the source JSON to keep it.", file=sys.stderr)
            continue
        return False, err, 0
    return False, "too many invalid fields", 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Path to JSON-Resume input.")
    ap.add_argument("--out", required=True, help="Path to output PDF.")
    ap.add_argument("--theme", default=None,
                    help=f"rendercv theme. CLI > meta.theme > default ({C.DEFAULT_THEME}). "
                         f"'auto' routes by meta. Choices: {', '.join(VALID_THEMES)}.")
    ap.add_argument("--paper", default=None, choices=("letter", "a4"),
                    help="Override page size (else derived from meta.paper / region).")
    ap.add_argument("--max-pages", type=int, default=1, choices=(1, 2),
                    help="Target page count (default 1). Auto-tightens density to fit; "
                         "pass 2 to allow a comfortable two-page layout.")
    ap.add_argument("--emit-png", action="store_true",
                    help="Also write per-page PNGs next to --out (<stem>.p1.png, ...) for review-render QA.")
    ap.add_argument("--date-col", default=None,
                    help="Override date/location column width, e.g. '3.3cm' (widow control).")
    ap.add_argument("--density", default=None, choices=_PRESET_ORDER,
                    help="Force a density preset (skip auto-fit). For QA-loop targeted fixes.")
    ap.add_argument("--no-qa", action="store_true",
                    help="Skip the automatic deterministic layout gate (qa_report.py).")
    ap.add_argument("--accent", default=None,
                    help="Override the accent color (name/titles/links), e.g. 'rgb(140,30,62)' "
                         "or a hex/CSS name. Else from meta.accent_color / the track default.")
    ap.add_argument("--font", default=None,
                    help="Override the font family (e.g. 'Lato', 'EB Garamond'). "
                         "Else from meta.font_family / the track default.")
    args = ap.parse_args()

    with open(args.data) as f:
        data = json.load(f)
    meta = data.get("meta", {}) or {}
    region = meta.get("region", "US")

    theme = args.theme or meta.get("theme") or C.DEFAULT_THEME
    if theme in LEGACY_THEME_ALIASES:
        mapped = LEGACY_THEME_ALIASES[theme]
        print(f"[render] legacy template '{theme}' -> rendercv theme '{mapped}'", file=sys.stderr)
        theme = mapped
    if theme == "auto":
        theme = _pick_theme_auto(meta)
        print(f"[render] auto-selected theme: {theme}", file=sys.stderr)
    if theme not in C.ALL_THEMES:
        print(f"[render] unknown theme '{theme}'. Choices: {', '.join(VALID_THEMES)}", file=sys.stderr)
        return 2
    if not C.theme_is_ats_safe(theme):
        print(f"[render] NOTE: '{theme}' is not in the ATS-safe subset "
              f"({', '.join(C.ATS_SAFE_THEMES)}). Fine for direct/human sends; "
              f"prefer an ATS-safe theme for portal applications.", file=sys.stderr)

    paper = _resolve_paper(args.paper, meta, region)
    document = to_rendercv.build_cv_document(data, theme=theme, paper=paper, region=region)

    out_abs = os.path.abspath(args.out)
    outdir = os.path.dirname(out_abs) or "."
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.out))[0]
    yaml_path = os.path.join(outdir, base + ".rendercv.yaml")

    rendercv = _find_rendercv()
    if not rendercv:
        _write_yaml(document, yaml_path)
        print(
            f"[render] rendercv is not installed. The input is ready at {yaml_path}.\n"
            f"         Install it (Python 3.12+):\n"
            f"           python3 -m venv {os.path.join(SKILL_DIR, '.venv')} && \\\n"
            f"           {os.path.join(SKILL_DIR, '.venv/bin/pip')} install 'rendercv[full]'\n"
            f"         (or `uv tool install rendercv` / `pipx install 'rendercv[full]'`),\n"
            f"         then re-run, or render manually: rendercv render {yaml_path}",
            file=sys.stderr,
        )
        return 0  # degrade gracefully — the YAML is usable

    # Base design overlay (date-column width; --date-col overrides the default).
    base_design = copy.deepcopy(_BASE_DESIGN)
    if args.date_col:
        _deep_merge(base_design, {"entries": {"date_and_location_width": args.date_col}})

    # Industry-aware styling (accent color + font) layered on top of the theme
    # defaults. Density presets (below) only touch spacing/size, so no conflict.
    style = _style_overlay(meta, cli_accent=args.accent, cli_font=args.font)
    if style:
        _deep_merge(base_design, style)
        _accent = style.get("colors", {}).get("name", "theme default")
        _font = style.get("typography", {}).get("font_family", "theme default")
        print(f"[render] style: track='{(meta.get('track') or '').lower() or 'none'}' "
              f"accent={_accent} font={_font}", file=sys.stderr)

    # Auto-fit: walk the density ladder, stop at the first (lightest) layout that meets
    # --max-pages. --density forces a single preset (QA-loop targeted control). Each
    # attempt strips invalid optional contact fields and retries.
    build_dir = os.path.join(outdir, ".rendercv_build")
    target = args.max_pages
    presets = (args.density,) if args.density else _PRESET_ORDER
    chosen_preset, chosen_pages = None, None
    for preset in presets:
        attempt = copy.deepcopy(document)
        _deep_merge(attempt.setdefault("design", {}), base_design)
        _deep_merge(attempt["design"], _DENSITY[preset])
        ok, err, pages = _render_once(rendercv, attempt, yaml_path, build_dir)
        if not ok:
            print(f"[render] rendercv failed:\n{err[-1500:]}\n[render] input kept at {yaml_path}", file=sys.stderr)
            return 1
        chosen_preset, chosen_pages = preset, pages
        if pages <= target:
            break
    else:
        if not args.density:
            print(f"[render] WARNING: couldn't fit within {target} page(s); densest layout is "
                  f"{chosen_pages} pages. Trim content (the brain's job) or pass --max-pages 2.",
                  file=sys.stderr)

    pdfs = glob.glob(os.path.join(build_dir, "*.pdf"))
    if not pdfs:
        print(f"[render] rendercv produced no PDF in {build_dir}", file=sys.stderr)
        return 1
    shutil.move(pdfs[0], out_abs)

    if args.emit_png:  # copy per-page PNGs out for review-render before cleanup
        for stale in glob.glob(os.path.join(outdir, f"{base}.p*.png")):
            os.remove(stale)  # clear prior pages so a now-shorter render leaves none behind
        pngs = sorted(glob.glob(os.path.join(build_dir, "*.png")))
        for i, p in enumerate(pngs, 1):
            shutil.copy(p, os.path.join(outdir, f"{base}.p{i}.png"))
        if pngs:
            print(f"[render] emitted {len(pngs)} page PNG(s): {os.path.join(outdir, base)}.p1.png ...", file=sys.stderr)

    # Deterministic self-QA gate (cheap, automatic) — runs on every render unless --no-qa.
    qa = None if args.no_qa else _run_qa(rendercv, build_dir)

    shutil.rmtree(build_dir, ignore_errors=True)
    ats_safe = C.theme_is_ats_safe(theme)
    # Success summary on STDOUT so the skill always sees the theme + ATS classification
    # (the NOTE on stderr is easy to miss). The skill relays the warning to the user.
    print(f"Rendered {args.out} (theme: {theme}, paper: {paper}, "
          f"pages: {chosen_pages}, density: {chosen_preset}, "
          f"ATS-safe: {'yes' if ats_safe else 'no'})")
    if qa:
        print(f"QA: pages={qa['pages']} last_fill={qa['last_page_fill']} "
              f"flags={','.join(qa['flags']) if qa['flags'] else 'none'}")
        if qa["flags"]:
            print(f"QA HINT: {qa['notes']} "
                  f"Run review-render for the full visual rubric + auto-fix loop.")
    if not ats_safe:
        print(f"ATS WARNING: theme '{theme}' is not ATS-safe "
              f"({', '.join(C.ATS_SAFE_THEMES)} are). Relay this to the user — prefer an "
              f"ATS-safe theme for portal/ATS applications; this is fine for direct/human sends.")
    print(f"[render] compiled {args.out} via rendercv "
          f"(theme: {theme}, paper: {paper}, density: {chosen_preset}, pages: {chosen_pages})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
