---
name: apply-to-job
description: >
  Orchestrate the full apply chain for one job — capture the job once, score fit, tailor the
  resume (PDF), write the cover letter, and answer the application questions — in auto-pilot
  (run end-to-end, pause only at decision/send gates) or review (confirm each step) mode.
  Stops before anything that sends or submits. The single entry point for "apply to this job".
when_to_use: >
  Use when the user has a specific job (a URL, a pasted JD, or a job_id from find-jobs) and
  wants the complete application package assembled without running each skill by hand.
user-invocable: true
allowed-tools: Read, Write, Bash
---

# apply-to-job

One command to turn a job into a ready-to-submit application package. This skill **orchestrates** the
other skills (it invokes them in order) — it does not re-implement them. Stage map + each skill's role:
[`../../knowledge/pipeline.md`](../../knowledge/pipeline.md). Hard rules: [`../_shared/RULES.md`](../_shared/RULES.md).

## Input
A job, supplied any way: a **URL**, **pasted JD text**, or a **`job_id`** from `jobs/found-<date>.json`.
If none is given, read `jobs/current.json`; if that's absent too, ask for the job.

## Mode
Ask once at the start (or accept `--mode auto|review`):

> *"Run this in **auto-pilot** (I run the whole chain and only stop at the apply/skip call and before anything is sent) or **review** (I check with you before each step)?"*

Default to **review** if the user doesn't choose. Both modes obey the same guardrails below.

## Chain

0. **Profile check.** If `profile/master-profile.md` is missing → run `/build-profile` first (or stop and say so).
1. **Capture the job once.** Resolve the JD (fetch the URL / use the pasted text / look up the `job_id`) and write `jobs/current.json` = `{company, role, url, job_id, jd_text, region, source, captured_at}`. Every downstream skill reads this — the JD is supplied **once** (RULES §6).
2. **`score-fit`.** Run it against `jobs/current.json`.
   - **Skip / low fit:** in **auto** mode, stop and report the one-line reason (offer: "apply anyway?"); in **review** mode, ask whether to proceed.
   - **Apply / Apply-if-tailored:** continue.
3. **`tailor-resume`.** Produces the tailored resume **PDF** (+ md + sidecars) and runs the `review-render` QA loop. Relay any ATS warning.
4. **`write-cover-letter`.** Region-aware (US: role-dependent; IN: short-form often enough — follow the region pack). Skip only if the user opts out.
5. **`answer-application-questions`.** Only if the user provides the form's questions (paste or a JSON schema). If no form is available yet, note it and move on — the answers come at submit time.
6. **Assemble + STOP.** Present the package: resume PDF path, cover letter, any answers, and the apply URL. **Do not submit, send, or auto-fill any portal** — that's the human's action (or the JobClaw agent's, behind its own guardrails).

In **review** mode, pause after each numbered step for a go/no-go. In **auto** mode, run 1→6 without pausing **except** at the score-fit decision (step 2) and the final stop (step 6); surface every artifact + warning in the end summary.

## Guardrails
- **Never submit, send, or auto-fill** an application, email, or portal. This skill stops at a ready package.
- **Never fabricate** (RULES §1); **never re-ask** for data already captured (RULES §6 — the profile + `jobs/current.json` + sidecars hold it).
- Honor the region pack and work-authorization rules; relay honesty flags from score-fit/tailor-resume rather than hiding them.
- If any step fails (e.g. rendercv not installed), continue the rest, mark that step pending, and tell the user exactly what to fix.

## Output
A package summary: `company · role · fit score · resume.pdf · cover-letter · answers (or "form pending") · apply URL`, plus any honesty/ATS warnings.

## Next steps
Application package assembled. Review it, then submit yourself (or hand it to the JobClaw agent for auto-apply). After you apply, run `/triage-inbox` on recruiter replies and `/infer-status` to track it. No emoji.
