---
name: render-resume
description: >
  Render a resume to a polished PDF via rendercv (Typst engine). Exposes all 9
  built-in themes (engineeringresumes is the ATS-safe default) and embeds every
  link as a real, clickable PDF annotation. Reads the tailor-resume sidecar so
  the tailored content and links survive intact.
when_to_use: >
  Use after tailor-resume to produce a sendable PDF, or any time the user wants
  a typeset resume file from their profile or a tailored markdown resume.
user-invocable: true
allowed-tools: Read, Write, Bash
---

# render-resume

Typeset a resume into a clean PDF with [rendercv](https://github.com/rendercv/rendercv) (a Typst-based renderer). This skill is format-only — content/region decisions are made upstream by `tailor-resume` (which applies region conventions); here we just produce the file. rendercv embeds links as real PDF hyperlink annotations, so contact links are clickable and ATS-extractable with no LaTeX workarounds.

## 1. Get the content

In priority order:
1. **`resumes/<slug>.tailor.json` sidecar** (preferred) — written by `tailor-resume`. Contains `basics_overrides`, the tailored `content`, optional `contact_order` / `contact_hidden`, and an optional `theme_hint`. Merge with `profile/master-profile.md` for anything not overridden.
2. **`resumes/<slug>.json`** — a hand-authored JSON Resume intermediate.
3. **`profile/master-profile.md` directly** — for a generic, non-job-tailored resume.

Identify the target region (profile `region` or job region) so paper size matches — see [`../../knowledge/regions/`](../../knowledge/regions/).

**Never re-derive links by parsing the tailored markdown.** The master profile's `links:` map is the source of truth; the sidecar's `contact_order`/`contact_hidden` are the only per-job overrides. Every link in `links:` (including everything under `links.other`) survives into the output — see the link mapping in §4.

## 2. Build the JSON Resume intermediate

Convert the content into the structured JSON in [reference/json-resume-schema.md](reference/json-resume-schema.md) (a subset of the [JSON Resume](https://jsonresume.org) standard, plus optional region fields). Write it to `resumes/<name>.json`. **No fabrication** — only what's in the source.

Read `context.career_goal` and `context.additional_info` from the profile **only to skip them** — they are CONTEXT-ONLY and must never appear in any rendered output.

## 3. Render

```
python3 scripts/render.py --data resumes/<name>.json --out resumes/<name>.pdf \
                          [--theme <theme>|auto] \
                          [--paper letter|a4] \
                          [--max-pages 1|2] \
                          [--accent "rgb(140,30,62)"] [--font "Lato"]
```

`render.py` converts the JSON Resume into a rendercv input file (`<out>.rendercv.yaml`, next to `--out`), runs `rendercv render`, and moves the produced PDF to `--out`. The `.yaml` is left in place so the user can tweak and re-render manually.

### Page length (`--max-pages`, default 1)

`render.py` **auto-fits density** to the page target: it walks `normal → snug → compact → dense → tight` spacing presets and stops at the **first (lightest)** that fits within `--max-pages` (default **1**). Picking the lightest fitting preset means the page is *filled*, not over-compressed — the fine ladder avoids the "trimmed AND half-empty" outcome.

If content genuinely can't fit even at `tight`, it prints a `WARNING` and renders the densest layout (it will NOT shrink text to illegibility). **Fitting one page is then a content decision — the brain's job:** trim with `tailor-resume`. But **don't over-trim** — preserve real context and aim to fill the page; a denser layout beats dropping genuine achievements. Pass `--max-pages 2` for a comfortable two-page layout when the content warrants it.

### Themes (all 9 exposed)

`--theme` defaults to **`engineeringresumes`**. ATS-safety annotations — all themes are single-column with selectable text and embedded links, but the styled ones apply color/denser typography that can degrade older ATS pdf-to-text pipelines:

- **ATS-safe (prefer for portal applications):** `engineeringresumes` *(default)*, `classic`, `engineeringclassic`, `sb2nov`.
- **Styled (fine for direct/human sends; render.py prints a NOTE):** `moderncv`, `harvard`, `ink`, `opal`, `ember`.
- **`--theme auto`** — routes by `meta.track` / `meta.seniority`: marketing/design/exec → `moderncv`; finance/quant/sales/customer-success/content/hr/founders-office (+ senior product) → `classic`; software/data/operations/product → `engineeringresumes`.

Legacy `--theme jake|deedy-single|awesome` (old LaTeX template names, e.g. from an older `template_hint`) still resolve — `jake`/`deedy-single` → `classic`, `awesome` → `moderncv` — with a deprecation note.

### Industry-aware styling (accent color + font)

rendercv's default accent is one corporate **blue** on every resume — wrong for creative tracks, needlessly loud for conservative ones. `render.py` applies a **track → {accent, font}** preset on top of the theme (see [`../../knowledge/resume-style.md`](../../knowledge/resume-style.md) for the full map + rationale):

- **marketing** → burgundy + Lato · **design** → deep teal + Poppins · **hr** → teal + Lato · **founders-office** → forest green + Lato · **sales** → brick + Lato · **customer-success** → teal-green + Lato · **content** → plum + Lato (expressive/personable, non-blue, warm).
- **product / software / data** → refined slate + Source Sans 3 · **operations** → steel blue-grey + Source Sans 3 (clean, minimal, ATS-first).
- **finance** → black + EB Garamond · **quant** → near-black navy + XCharter (conservative + serif).

Accents apply only to name/headline/section-titles/links/connections; **body text stays black** and the layout stays single-column, so ATS-readability is unchanged. All accents are mid-to-dark and grayscale-safe (light/neon vanish in B&W).

**Override precedence:** `--accent` / `--font` (CLI) → `meta.accent_color` / `meta.font_family` (sidecar/intermediate) → track default → theme default. So `tailor-resume` can pin a per-job look via `meta`, and the user can override either at the CLI.

### Paper

`--paper` overrides; otherwise derived from `meta.paper`, then region (`IN` → `a4`, else `letter`).

## 4. How links are mapped (every link survives)

rendercv's header `social_networks` is a **fixed set** (LinkedIn, GitHub, GitLab, Instagram, ORCID, Mastodon, StackOverflow, ResearchGate, YouTube, Google Scholar, Telegram, WhatsApp, Leetcode, X, Bluesky, Reddit, IMDB), stored as `username` not URL. The converter (`scripts/to_rendercv.py`):

- **Known networks** → header `social_networks` (username extracted from the URL; only emitted if it passes rendercv's own username validation, so the render never hard-fails).
- **Portfolio / personal site** → `cv.website`.
- **Everything else** (Medium, Substack, Speakerdeck, personal domains, any network whose username can't be cleanly extracted) → a body **"Links"** section as a Markdown link, so nothing is dropped.
- `email` / `phone` are rendered by rendercv as their own header connections.

**Ordering** of the `social_networks` list follows one precedence chain, defined once in
`templates/_common.py` (`DEFAULT_CONTACT_ORDER_BY_TRACK` / `resolve_contact_order`):

> sidecar `contact_order` → profile `contact_priority` → track default → `FALLBACK_CONTACT_ORDER`

`contact_hidden` drops entries. Email/phone/website *placement* is theme-controlled, not orderable.
(Reduced control vs. the old LaTeX renderer — but the ordering source of truth is no longer duplicated
in docs.)

## 5. Report
- If rendercv ran: report the `.pdf` path and the theme used. **Read `render.py`'s stdout** — it ends
  with a `Rendered … (… ATS-safe: yes/no)` line. **If `ATS-safe: no`, you MUST relay the `ATS WARNING`
  to the user in chat** (it means a styled theme was used — fine for direct/human sends, but recommend
  switching to an ATS-safe theme for portal/ATS applications). Don't rely on the stderr NOTE alone.
- If **rendercv isn't installed**: the `.rendercv.yaml` is still written (exit 0) — tell the user to install rendercv (see below) or run `rendercv render <yaml>` themselves.
- **Invalid contact field:** rendercv validates strictly (email/phone/website). If one is rejected (e.g. a placeholder phone like `+1 555 0100`), `render.py` prints a `WARNING`, drops just that field, and retries so the resume still renders. If you see the warning, fix the value in the source JSON to keep the field.

## 6. Self-QA (always — rendering isn't done until it passes)

Every render is self-checked, in two layers:

1. **Deterministic gate (automatic, in `render.py`).** Unless `--no-qa`, `render.py` prints a `QA:` line on stdout — `pages`, `last_fill`, `flags` (`underfilled`/`sparse_last_page`/`overflow_risk`). **Read it.** Combined with the `pages` vs your `--max-pages` target and the stderr `WARNING`, this is the cheap first signal.

2. **Visual rubric + auto-fix (the [`review-render`](../review-render/SKILL.md) skill).** After producing the PDF you **must** run the `review-render` loop before declaring the resume done: it re-renders with `--emit-png`, scores the page image against its rubric (widows, fill, overflow, alignment, readability — things this script can't see), and applies one fix per pass (layout lever first via `--date-col`/`--density`/`--max-pages`, content second via the source JSON, obeying `tailor-resume`'s rubric), capped at 3 passes.

Skip the vision pass only if the caller explicitly asks for a raw render. For autonomous runs (JobClaw), the `review-render` pass is **mandatory** — no human is watching the page.

## Install (one-time, Python 3.12+)

rendercv lives in an isolated venv the skill resolves automatically (`skills/render-resume/.venv/bin/rendercv`), or on PATH. To create it:

```
python3 -m venv skills/render-resume/.venv
skills/render-resume/.venv/bin/pip install "rendercv[full]"
```

(`uv tool install rendercv` or `pipx install "rendercv[full]"` also work.) The Typst engine ships with the pip package — no separate LaTeX/Tectonic install is needed.

## ATS guarantees

All rendercv themes are single-column and produce selectable text with embedded hyperlink annotations. When a non-ATS-safe theme is selected, `render.py` prints `ATS-safe: no` plus an `ATS WARNING` **on stdout** (and a NOTE on stderr); the skill must relay that warning to the user (see §5). For portal applications, prefer the ATS-safe subset above.
