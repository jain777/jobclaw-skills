---
name: write-cover-letter
description: >
  Produce a job-specific, profile-grounded cover letter in markdown — ≤ 350 words,
  ≤ 1 page, three paragraphs (hook → two quantified proofs → fit close). Reuses keywords
  from a prior tailor-resume sidecar when present. Writes a JSON sidecar reserved for a
  future /render-resume --kind cover-letter (rendercv).
when_to_use: >
  Use when the user wants a cover letter for a specific job — typically after score-fit
  recommends applying and tailor-resume has produced a tailored resume.
user-invocable: true
allowed-tools: Read, Write, WebFetch
---

# write-cover-letter

Earn the reader the next 30 seconds. Open with one concrete reason this candidate fits *this* role at *this* company. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md). Use **Communication / Management / Creative** verbs from [`../tailor-resume/reference/action-verbs.md`](../tailor-resume/reference/action-verbs.md).

## Inputs
1. **Profile:** `profile/master-profile.md`. Read `context:` for *direction only* — never quote.
2. **Job:** pasted JD text, a URL (use `WebFetch`), or an entry from `jobs/found-<date>.json`.
3. **Tone:** `enthusiastic | confident | concise | warm` (default: `confident`).
4. **Optional sidecar:** `resumes/<slug>.tailor.json` from a prior `tailor-resume` run — reuse its keyword list and `basics_overrides.summary` so the letter and the resume sing the same notes.
5. **Optional score-fit sidecar:** `scores/<job-id>.score.json` — reuse `missing_keywords` to know what the resume already incorporated.

If the job is missing, ask for it; the tone has a safe default.

## Method

0. **Region note.** Read the target region pack:
   - **US:** cover letters role-dependent — stronger for senior, mission-driven, career-change roles. Surface this in the rationale so the user decides whether to send.
   - **IN:** cover letters less emphasized; usually a 2–3 sentence email body suffices. Offer a "short form" alternative if the user wants.

1. **Read the JD** for 3–5 must-have themes, the JD's tone of voice (formal / casual / mission-led), and any explicit asks ("tell us why you want to work here").

2. **Pick two flagship achievements** from the profile that map to those themes — each quantified. No invention; if the profile lacks a quantified match, pick the closest qualitative win and flag the gap rather than fabricating a number.

3. **Draft three paragraphs** (≤ 350 words total):
   - **Opening hook** (~60 words) — concrete reason you/this role fit, anchored to a specific JD theme. **Not** "I am writing to apply for…". **Not** "I admire your mission…".
   - **Two proof points** (~180 words) — each a 2–3 sentence story tying one flagship achievement to one JD must-have. Verb-led, metric-led, no resume restating.
   - **Fit close** (~110 words) — what specifically excites you about *this* role (not the company in general). One CTA-style close.

4. **Apply tone modifier** + region spelling (US American · IN British) + region date format (if you reference dates).

5. **No salary.** No street address. No "References available on request." No `context:` echo.

## Output
- `resumes/<company-slug>-<role-slug>.cover-letter.md` — body only (signed with the candidate's name; no address blocks).
- `resumes/<company-slug>-<role-slug>.cover-letter.json` — sidecar:
  ```jsonc
  {
    "company": "...", "role": "...", "tone": "confident",
    "body_md": "...",
    "themes_used": ["..."],
    "source_profile_path": "profile/master-profile.md",
    "source_sidecar_path": "resumes/<slug>.tailor.json" /* or null */
  }
  ```
  Reserved for `/render-resume --kind cover-letter` once rendercv cover-letter support lands.
- Console: 2-line rationale (themes hit · what you cut) + region prevalence note.
- Final line: *"Future: pass to /render-resume --kind cover-letter when rendercv cover-letter support lands."*

## Anti-patterns
- "I am writing to apply for the X position at Y." Cut the opener cliché.
- First-paragraph flattery about the company.
- Restating the resume in narrative form.
- Salary / current-CTC / expected-CTC in the body (US: never; IN: only if the JD explicitly asks).
- Quoting `context.career_goal` / `context.additional_info`.
- Filler ("I believe", "I feel", "I think", "I am passionate about").
- Emoji.

## Rubric (one-page self-check)
- [ ] ≤ 350 words; exactly 3 paragraphs.
- [ ] ≥ 2 quantified proof points.
- [ ] Each proof point ties to a specific JD theme.
- [ ] 1 explicit "why this role" sentence (specific, not generic).
- [ ] No salary, no address, no clichés.
- [ ] Spelling matches region.
- [ ] Verb openers vary across the 6–10 sentences that have them.
