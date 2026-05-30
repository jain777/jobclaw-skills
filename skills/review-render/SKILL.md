---
name: review-render
description: >
  Visually QA a rendered resume PDF and auto-fix layout/content defects in a bounded
  loop: render → screenshot → deterministic gate → vision rubric → apply one fix →
  re-render, until it passes or hits a pass cap. Catches widows, under-fill, overflow,
  orphaned headers, and imbalance that text-only logic can't see.
when_to_use: >
  Use right after render-resume produces a PDF — especially in autonomous runs where no
  human eyes the page — to verify and tighten the visual result before it goes out.
user-invocable: true
context: fork
allowed-tools: Read, Write, Edit, Bash
---

# review-render

A rendered resume has defects that are **invisible in the JSON and only show up on the page** — a bullet wrapping with two dangling words, a half-empty page, content spilling one line onto page 2, an orphaned section header. This skill closes the loop the way a human does: **make it, look at it, fix it, repeat** — bounded so it always terminates.

Architecture split (see [`../../_shared/RULES.md`](../../_shared/RULES.md)): **rendercv renders; this skill (the brain) judges and decides the fix.** Rendering levers live in `render-resume`; the visual judgment and content edits live here.

`render-resume` **hands off to this skill as its mandatory final step** (its §6 Self-QA) — so every resume is visually QA'd, not just ones where someone remembers to ask. You can also invoke it standalone on any existing rendered resume.

## Inputs
- The JSON-Resume intermediate: `resumes/<name>.json` (the editable source of content fixes).
- The output PDF path: `resumes/<name>.pdf`.
- Optional: target `--max-pages`, `--theme` (else from `meta.theme`).

## The loop (max **3** passes — never loop forever)

**1. Render with page PNGs**
```
python3 skills/render-resume/scripts/render.py \
    --data resumes/<name>.json --out resumes/<name>.pdf --emit-png \
    [--max-pages 1|2] [--theme T] [--date-col 3.3cm] [--density snug|compact|dense|tight]
```
This writes the PDF plus `resumes/<name>.p1.png, .p2.png, …`.

**2. Deterministic gate (cheap — no vision tokens)**
```
skills/render-resume/.venv/bin/python skills/render-resume/scripts/qa_report.py resumes/<name>.p*.png
```
Returns `{pages, page_fills, last_page_fill, flags}`. Flags: `underfilled`, `sparse_last_page`, `overflow_risk`.

**3. Vision rubric** — **Read** each `.pN.png` and score it against [`reference/rubric.md`](reference/rubric.md). Record each issue as `{dimension, severity (critical/major/minor), where, suggested fix}`.

**4. Decide**
- **PASS** when the deterministic `flags` are empty **and** the rubric has no critical/major issue (score ≥ 90). Report and stop.
- Otherwise pick the **single highest-severity issue**, apply **exactly one** fix from the vocabulary below, and go back to step 1.
- After **3 passes**, stop regardless; report the best version + any residual issues and a recommendation.

**5. Clean up** the `.pN.png` files (and any `.rendercv.yaml`) unless the caller asked to keep them.

## Fix vocabulary (issue → lever)

Apply ONE per pass, then re-render and re-judge — never stack blind changes.

| Issue | Fix (try in this order) |
|---|---|
| **Widow / overflow line** (bullet wraps, 1–2 words dangle) | `--date-col 3.3cm` (more bullet width). If it persists, **tighten that specific bullet** in the JSON by 3–6 words — preserve meaning and keep the metric. |
| **Underfilled single page** (`underfilled`, bottom whitespace) | **Restore** a previously-cut bullet/section to the JSON (preferred — recovers lost context), or force a lighter density (`--density snug`/`compact`). |
| **Spills to 2 pages, sparse last page** (`sparse_last_page` / `overflow_risk`) | If content is ~1 page: trim the lowest-value bullet(s) per `tailor-resume`'s rubric, or `--max-pages 1` to densify. If genuinely 1.5+ pages: `--max-pages 2` and rebalance so the last page is >50% full. |
| **Orphaned section header** at page bottom | Step density one notch, or trim/restore one line to shift the break. |
| **Inconsistent dates / bullet glyphs / tense** | Fix in the JSON (formatting) — not a renderer concern. |
| **Section imbalance or wrong order** | Reorder/rebalance sections in the JSON. |

## Rules
- **One fix per pass.** Re-render and re-evaluate before the next change.
- **No fabrication.** "Tighten" = cut words, never invent. Content edits obey `tailor-resume`'s rubric and `_shared/RULES.md` (incl. never quoting `context.*`).
- **Always terminates.** Hard cap of 3 passes; if still failing, stop and recommend (e.g., "content is genuinely two pages — use `--max-pages 2`").
- **Layout first, content second.** Prefer a rendering lever (date-col, density) before editing real content, so context isn't lost to cosmetics.

## Output
A concise QA report: **PASS/FAIL**, final score, the **iteration log** (per pass: what the gate + rubric flagged → the one fix applied → the new result), and the final PDF path.

## Next steps
Resume passed QA. Next: `/write-cover-letter`, then apply — or `/apply-to-job` to finish the package.
