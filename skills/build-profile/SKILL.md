---
name: build-profile
description: >
  Build or update the JobClaw master profile — the single file every other job-hunt
  skill reads. Ingests a resume (extracting every embedded URL), LinkedIn PDF, exported
  AI-memory, and links, then asks only for what's missing in one batched, optional gap
  prompt. Captures career-goal context for downstream skills.
when_to_use: >
  Use at the start of a job hunt, when onboarding a new user, when the user shares a
  resume/CV/LinkedIn export, or whenever profile/master-profile.md is missing or stale.
user-invocable: true
allowed-tools: Read, WebFetch, WebSearch, Write, Edit, Bash
---

# build-profile

Produce `profile/master-profile.md` from whatever the user already has, then fill gaps with a short, track-aware interview. **Ingest first, ask last.**

## 1. Gather what exists (don't ask the user to retype anything)

Collect any of these the user provides; actively offer the options:
- **Resume / CV** — see step 1a for PDFs (mandatory link-extractor first), then read the body with the Read tool.
- **LinkedIn PDF** — read it. (Point them to LinkedIn → profile → *Resources* → *Save to PDF* if they don't have it.)
- **AI-memory export** — if they haven't, point them to `profile/IMPORT_MEMORIES_PROMPT.md` and have them paste the result.
- **Links** — fetch and mine:
  - **GitHub**: `WebFetch https://api.github.com/users/<user>` and `/repos?sort=stars` for top repos, languages, bio. (Public, no key.)
  - **Portfolio / personal site**: `WebFetch` the URL.
  - **LinkedIn URL**: do **not** scrape — LinkedIn blocks it and it breaks ToS. Use the LinkedIn PDF instead; only record the URL.

Read everything before asking anything.

### 1a. For every PDF input — run the link extractor FIRST

Claude's native Read tool surfaces visible anchor text only (it shows the word "LinkedIn" but not the URL it's hyperlinked to). LaTeX/Word/Docs resumes routinely embed `\href{url}{anchor}` annotations whose URLs are invisible to Read. **You will silently lose the user's LinkedIn / GitHub / portfolio URLs** if you skip this step.

```
python3 skills/build-profile/scripts/extract_links.py <path-to-resume.pdf>
```

The script decompresses every FlateDecode stream and pulls every `/URI` annotation it can find. Stdout is JSON:

```jsonc
{
  "urls": ["https://...", ...],           // every URL found, in order
  "classified": {
    "linkedin": "https://linkedin.com/in/...",
    "github": "https://github.com/...",
    "other": { "<host-or-label>": "<url>", ... }
  }
}
```

The script also returns a **`status`** field — branch on it:
- `ok` → use the `classified` map directly to populate `links:` (canonical keys land in their named
  fields; unknowns land in `links.other`). Surface any `links.other` entries with one short question —
  *"I found these other URLs in your resume: <list>. Keep any as portfolio links?"* — so project pages
  (e.g. *lambdatest.com/visual-ai-testing*) can be promoted to `portfolio` if relevant.
- `encrypted` / `scanned_image` / `unreadable` → the script never crashes (exit 0). When status is one
  of these **and** the Read tool also returns little/no body text, the PDF is unusable: tell the user
  what's wrong (use the script's `note`) and offer the fallback ladder — (a) paste the resume text,
  (b) supply a `.txt`/`.md`/`.docx` version, or (c) re-export from LinkedIn (*profile → Resources →
  Save to PDF*). **Explicitly warn that embedded links are lost on scanned/encrypted PDFs** and ask
  them to paste their LinkedIn / GitHub / portfolio URLs manually.

After the extractor, use the Read tool for body text. For non-PDF inputs (markdown, pasted text,
LinkedIn URLs), scan the text directly with regex for any `https?://…` matches.

## 2. Know the track and region

- **Track** (ask if unclear): `product · software · finance · quant · marketing · founders-office · hr · design · data · sales · operations · customer-success · content`. Decides which fields matter and which links to push for — see [reference/track-presets.md](reference/track-presets.md).
- **Region**: infer the applicant's `region` using this ladder, stopping at the first that resolves:
  1. **Location string** → region code (`New York`→`US`, `Bengaluru`→`IN`).
  2. **Contact clues** if location is missing/ambiguous (e.g. "Remote") → a `+91` phone or `₹`/CTC/LPA
     mentions → `IN`; a `+1` phone or `$`/state abbreviations → `US`.
  3. **`target.regions`** if already known from the conversation.
  4. **Otherwise ask one short question:** *"Which country are you based in, and where are you hunting?"*
  Codes must match a pack in [`../../knowledge/regions/`](../../knowledge/regions/). **Never silently
  default to US.** When region was inferred from weak signals (clues, not an explicit location), write
  it as `[VERIFY]` so downstream skills treat it as soft. Then confirm where they're hunting
  (`target.regions`). The chosen pack dictates which region-specific fields to collect (IN →
  current/expected CTC + notice period; US → work authorization per
  [`../../knowledge/work-authorization.md`](../../knowledge/work-authorization.md)) and what to omit
  (e.g., don't collect photo/DOB).

## 3. Ask only for gaps

Compare what you extracted against [reference/profile-schema.md](reference/profile-schema.md). Then ask a **short, batched** set of questions for only the missing or `[VERIFY]` fields, prioritizing the track's must-haves, the **region's** required fields (per the region pack), and anything `find-jobs`/`score-fit` need (target roles, locations, remote preference, salary floor; work authorization for US; current/expected CTC + notice period for IN). Don't interrogate — 5–8 crisp questions max, grouped, with sensible defaults offered.

### 3a. The single optional links-gap prompt

After populating `links:` from extraction, run **one** track-aware optional prompt to surface what the resume didn't include. Use the link gap matrix in [reference/track-presets.md](reference/track-presets.md) to decide what to suggest.

Shape:

> *"I found these links: \<list of canonical keys filled\>. For \<track\> roles, candidates also commonly include: \<strongly + optional gaps from the matrix\>. Want to add any? (Paste or skip.)"*

**One prompt. Dismissible. No follow-ups.** The user can paste any handle/URL or skip entirely.

### 3b. Two closing context prompts

The `context:` block is read by `find-jobs`, `score-fit`, and `tailor-resume` to bias direction — never rendered into a PDF or external message. Ask once:

1. *"In 2–3 sentences, what are you actually optimizing for over the next 12–24 months?"* → `context.career_goal` (≤ 600 chars).
2. *"Anything else I should know that won't go on the resume — geo constraints, life situation, things to avoid?"* → `context.additional_info` (≤ 400 chars). Skip if the conversation already covered it; record what surfaced.

Both fields are optional but high-value.

## 4. Write the profile

Write `profile/master-profile.md` following [reference/profile-schema.md](reference/profile-schema.md) exactly (YAML frontmatter + markdown sections). Rules:
- **Never fabricate.** If a fact is unknown, leave the field empty / omit it; mark anything uncertain inline as `[VERIFY]`.
- Quantify achievements where the source gives numbers; don't invent metrics.
- Capture the user's **voice/constraints** in the Notes section (tone, hard limits like no-relocation, sponsorship needs) — downstream skills rely on it.
- Populate **every** link the extractor found (canonical keys to their named fields; everything else under `links.other`). Keep unfamiliar URLs even if you can't classify them.
- If the file already exists, **update in place** (preserve user edits; only fill/correct).

## 5. Confirm

Show a tight summary (identity, target, # roles captured, # links captured, gaps still `[VERIFY]`) and tell the user they can now run `/find-jobs`. Keep tone encouraging and concise — no emoji.
