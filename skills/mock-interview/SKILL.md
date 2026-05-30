---
name: mock-interview
description: >
  Run a text-based mock interview — one question at a time, capture the user's verbatim
  answer, end with a scored report per the shared report-schema. Defaults to 5 questions
  (matches Go original); configurable up to 10. Unanswered questions score 0. Forked.
when_to_use: >
  Use to practice for an upcoming round — ideally after /prep-interview produces a
  question bank. Long-running interactive skill.
user-invocable: true
allowed-tools: Read, Write
context: fork
---

# mock-interview

Practice live. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md). Report shape (canonical): [`reference/report-schema.md`](reference/report-schema.md).

## Inputs
1. **role** (required); **company** optional but improves question fidelity.
2. **Profile** — `profile/master-profile.md`.
3. **Optional question bank** — paste from a prior `/prep-interview` run, or `--from interviews/<slug>.prep.md`.
4. **Optional company brief** — `companies/<slug>.json`.
5. **Flags**:
   - `--questions N` — default **5**; up to 10.
   - `--difficulty easy | medium | hard` — default `medium`.
   - `--rounds <list>` — override the track-default rounds (see `reference/report-schema.md` for the per-track loop maps).

## Method

0. **Region pack** — read for region-specific behavioral framing (formality differs US ↔ IN).

1. **Greet by name** (from profile). One sentence. Confirm role + rounds + difficulty + length.

2. **The loop:**
   - Ask **one** question at a time. Tag with its round.
   - Wait for the user's answer. Acknowledge in **one** sentence (no live grading).
   - **Do not answer your own questions.** Do not hint. (Ports the Go `handlers.go:617` rule.)
   - If the user types `/skip`, log the question as unanswered (`userAnswer: ""`).
   - Stop after the configured count or when the user types `/done`.

3. **End-of-session** — generate the scored report per [`reference/report-schema.md`](reference/report-schema.md):
   - `overallScore` — float 1.0–10.0, one decimal.
   - `strengths` — 3–5 bullets, profile-grounded, citing specific Q ids.
   - `improvements` — 3–5 bullets, actionable (what to *do* next time).
   - `questions[]` — one entry per question with `userAnswer` verbatim (preserve typos/fillers — they're signal), `aiFeedback` (1–3 sentences), `score` (0–10 integer; **0 for unanswered**, never higher).
   - Optional `next_steps[]` — 0–3 things to drill next.

4. **Write transcript + report:**
   - `interviews/<company-or-role-slug>-<YYYY-MM-DD>.transcript.md`
   - `interviews/<company-or-role-slug>-<YYYY-MM-DD>.report.json`

## Output
- During the loop: questions + 1-sentence acknowledgements only. No feedback, no scores.
- At the end: 5-line summary on stdout — overallScore · top strength · top improvement · next-step suggestion · saved paths.

## Anti-patterns
- Long preambles before each question. One sentence max.
- Answering on the user's behalf.
- Asking out-of-track questions (SWE Qs in a marketing loop).
- Scoring an unanswered question higher than 0.
- **Live grading.** "Great answer!" leaks the rubric. Hold all assessment for the report.
- Hinting mid-question.
- Quoting `context.*`.
- Emoji.

## Rubric
- [ ] One question at a time; one-sentence acknowledgements; no live grades or hints.
- [ ] Unanswered Q → score 0 (not 1, not null).
- [ ] Report validates against `reference/report-schema.md` — integer per-Q scores; float `overallScore` (one decimal).
- [ ] Strengths + improvements cite specific Q ids.
- [ ] `userAnswer` is verbatim (typos preserved).
- [ ] No track-mismatched questions.

## Next steps
Scored. Next: re-run `/prep-interview` on the weak areas, or `/research-company` for more depth.
