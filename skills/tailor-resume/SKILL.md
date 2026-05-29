---
name: tailor-resume
description: >
  Produce a job-specific, ATS-optimized resume from the user's master profile and a target
  job — reordering, reframing, and surfacing the most relevant real experience and keywords.
  Enforces a content rubric (bullet shape, length, parallel grammar, metric coverage).
  Writes both a markdown resume and a structured sidecar JSON for render-resume. Never
  fabricates.
when_to_use: >
  Use when the user wants a resume tailored to a specific job, usually after score-fit
  recommends applying. Needs profile/master-profile.md and a job description.
user-invocable: true
allowed-tools: Read, Write
---

# tailor-resume

Turn the master profile into a resume aimed at one job — maximizing relevance and ATS keyword match **without inventing anything**.

## Inputs
1. Profile: read `profile/master-profile.md` (frontmatter + body, plus any `[VERIFY]` flags — don't rely on unverified facts). If missing → `/build-profile`.
2. Job: pasted description, URL, or an entry from `jobs/found-<date>.json`.
3. (Optional) `score-fit` output for this job — reuse its "missing keywords" list.

## The one hard rule
**Never fabricate.** You may select, reorder, reframe, and re-emphasize the user's *real* experience and use the job's vocabulary for things they actually did. You may **not** invent roles, titles, dates, metrics, skills, or tools they don't have. If a must-have is genuinely absent, leave it out and flag it to the user — don't paper over it.

## Read but never quote: the context block
The profile has a `context:` block with `career_goal` and `additional_info`. **Read both for signal** — use them to bias which experience strand to lead with in the Summary and which skills to elevate. **Never quote, paraphrase, or echo their contents** into the Summary, bullets, or anywhere else the candidate would send out. Do not write phrases like "My career goal is…" — that signal stays internal.

## Method

0. **Load region conventions.** Read the target region's pack in [`../../knowledge/regions/`](../../knowledge/regions/) and follow its resume rules — length, what to include/omit (e.g., US: omit photo/DOB, no salary; IN: 1–2 pages, include notice period, drop photo/DOB by default), spelling variant, and date format. These govern the structure below.
1. **Read the job** for must-have keywords, responsibilities, seniority, and the language it uses.
2. **Select & order** the profile's most relevant experience, skills, and projects for *this* role; drop or shorten the irrelevant. Use `context.career_goal` as a tie-breaker on what to lead with.
3. **Rewrite bullets** under the rubric below.
4. **Surface keywords** naturally into summary/skills/bullets — enough to pass ATS screening, never keyword-stuffed.
5. **Honor constraints/voice** from the profile Notes (tone, hard limits).
6. **Self-check** the draft against the rubric and anti-patterns before writing.

## Bullet & section rubric (self-check before writing)

1. **One page if <10 yrs, two pages max** (defer to region pack). If the draft exceeds, trim oldest-irrelevant bullets first, then longest bullets — never delete a whole role.
2. **Bullet shape:** `Verb + What + Measurable impact (or scoped scale)`. Strong past-tense verb at start; metric at end. Choose the opening verb from [reference/action-verbs.md](reference/action-verbs.md) (Harvard list), matched to the *kind* of work (build / improve / lead / analyze / create).
3. **No first-person pronouns** (`I`, `my`, `we`). Implied subject only.
4. **Banned filler verbs:** *helped, assisted, worked on, was involved in, responsible for, participated in, contributed to.* Replace with the actual action or cut.
5. **Parallel grammar in a list:** same tense across all bullets in a role (past for past roles; pick past *or* present for current and stick).
6. **No buzzword-only bullets:** *synergized, leveraged, utilized, spearheaded* without a quantified outcome → rewrite or cut. *Leveraged* → *used*.
7. **Each role: 3–6 bullets** (up to 8 for the most recent/most-relevant role), most-relevant-to-target first.
8. **≥60% of bullets must contain a number** (count / percent / time / money / scale). If less, **prompt the user for missing metrics before writing** — never invent.
9. **Keyword surfacing is integrated, not appended:** a JD skill enters Summary + Skills + ≥1 truthful bullet. No bullet exists solely to namedrop.
10. **Default section order:** Name+Contact → Summary (≤3 lines) → Experience → Skills → Education → Projects (if relevant) → Achievements (only if load-bearing). Region pack may override.
11. **Summary is ≤3 lines, ≤55 words.** Pattern: *`[Role identity w/ target keywords]. [Two flagship achievements w/ metrics]. [What you bring to <target-role-type>]`*. Never name the target company.
12. **Skills grouped, not flat:** 3–5 named groups (per track preset); 4–8 items per group; ordered most-relevant first.
13. **Dates obey region pack** (US: `Mon YYYY` or `Mon YYYY – Present`; IN: `DD/MM/YYYY` or `Mon YYYY`). Consistent across all roles.
14. **Vary verbs across the whole page** — no two consecutive bullets start with the same verb, and avoid reusing any verb more than twice (scannability + perceived breadth). Pull from the full [action-verbs.md](reference/action-verbs.md) range rather than recycling *led/managed/built*.
15. **Honor `context.career_goal` and `Notes / voice`:** bias Summary toward stated goal direction; respect declared tone; never override hard constraints.

## Anti-patterns (do not ship)

- **The duties list** — job-description-as-resume.
- **"We did this"** plural where the candidate's individual contribution is unclear.
- **Smart quotes / em-dashes** in the markdown (rendercv/Typst render Unicode fine, but keep the source clean and consistent).
- **Skills-section keyword spam** (>10 per group, generic "Microsoft Office, Excel" for senior roles).
- **Tools-without-outcomes** ("Used Jira, Figma, Notion" as a bullet).
- **Naming the target company in Summary** ("Excited to join Stripe to…").

## Output

Write **both** files to `resumes/`:

1. **`resumes/<company>-<role-slug>.md`** — human-readable tailored markdown for review. Sections in the order from rule 10, in clean ATS-friendly markdown.

2. **`resumes/<company>-<role-slug>.tailor.json`** — structured sidecar for `render-resume`. Shape:

   ```jsonc
   {
     "source_profile_path": "profile/master-profile.md",
     "target_job": { "company": "...", "role": "...", "url": "..." },
     "theme_hint": "engineeringresumes | classic | sb2nov | moderncv | ...",  // optional rendercv theme
     "contact_order": ["email","phone","linkedin","github","portfolio"],
     "contact_hidden": ["twitter"],                      // optional, per-job
     "basics_overrides": {
       "label": "<role-targeted subtitle>",
       "summary": "<the tailored summary text>"
     },
     "content": {
       "work": [ ... ],          // JSON-Resume work array, tailored
       "skills": [ ... ],
       "projects": [ ... ],
       "education": [ ... ]
     }
   }
   ```

   `render-resume` reads this sidecar (preferred) and merges it with `profile/master-profile.md` for anything not overridden. **Every link in the master profile's `links:` block (including `links.other`) survives into the output** — known networks in the header, the rest in a "Links" section — never re-derive links by parsing the markdown.

Then show the user:
- A **2–4 line rationale**: what you emphasized, what you cut, which keywords you added.
- Any **honesty flags**: must-haves the user genuinely lacks (so they decide how to address them).
- Any **rubric warnings**: bullets that need metrics, sections that exceeded length caps.

Suggest `/render-resume` next (defaults to the `engineeringresumes` theme; user can pass `--theme classic|sb2nov|moderncv|auto|…`), then `/write-cover-letter` when available. No emoji.
