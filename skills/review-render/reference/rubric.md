# review-render visual rubric

Score a rendered resume page image (the `.pN.png`) on the dimensions below. Each is
scored 0–100; the **overall = min(dimension scores)** is reported but the *decision*
is driven by issue severity (a single `critical` fails the page regardless of average).

When reading the screenshot, judge what a recruiter sees in the first 6 seconds AND
what an ATS extracts. Record each problem as `{dimension, severity, where, fix}` using
the fix vocabulary in SKILL.md.

## Dimensions

### 1. Line economy / no widows (severity up to *major*)
- No bullet should wrap so that only 1–2 words sit alone on the final line.
- No single-word last line in the summary or any paragraph.
- *Fix:* widen bullet area (`--date-col`), else tighten that bullet's wording.

### 2. Page fill (severity up to *major*)
- A one-page resume should fill **≥ ~90%** of the page height — no large blank band at the bottom.
- A two-page resume's **last page should be > 50%** full — no nearly-empty trailing page.
- *Fix:* restore content (underfill) or trim/densify (sparse last page). Prefer restoring over trimming.

### 3. Page count / overflow (severity up to *critical*)
- Matches the target (`--max-pages`). Content must not spill 1–3 lines onto an extra page.
- No section *heading* stranded at the very bottom of a page with its content on the next (orphan).
- *Fix:* densify / trim by a line, or accept `--max-pages 2` if content truly warrants it.

### 4. Alignment & consistency (severity up to *major*)
- Dates right-aligned and vertically consistent across all roles.
- One bullet glyph throughout; consistent indentation; consistent date format and verb tense.
- Section headings uniform; consistent spacing between sections.
- *Fix:* formatting edits in the JSON.

### 5. Hierarchy & balance (severity up to *minor*)
- Name/headline clearly dominant; section headings clearly delineate.
- Sections reasonably balanced — not one giant block and several stubs.
- Most-relevant content in the top third.
- *Fix:* reorder/rebalance sections in the JSON.

### 6. Readability / density floor (severity up to *major*)
- Body text must not be shrunk below readability to force a fit (≈ 9pt floor; `tight` preset is the limit).
- Adequate white space between sections; lines not cramped.
- If a page only fits by going below the floor → that's a **content** problem: trim, don't shrink further.

### 7. Links & contact (severity up to *minor*)
- Contact line present and complete; links visibly rendered (color/underline per theme).
- No raw unstyled URLs dumped in the body when they belong inline or in a Links section.

## Severity → action
- **critical** (overflow, illegible text, broken layout): must fix; fails the page.
- **major** (widows, underfill, misalignment, sub-floor density): fix if a pass remains.
- **minor** (slight imbalance, cosmetic): note; fix only if a cheap lever is at hand.

## Pass condition
Deterministic `flags` empty **and** no `critical`/`major` issue (score ≥ 90). Otherwise apply
the one highest-severity fix and re-render. Stop at 3 passes and report residuals.
