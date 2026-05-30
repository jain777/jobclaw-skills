# Shared rules — the JobClaw canon

> Every skill in this repo whose output reaches a human or downstream skill MUST follow these rules. They are **referenced — not duplicated — from each SKILL.md** (`See [../_shared/RULES.md](../_shared/RULES.md). Treat as non-negotiable.`). Skill authors may restate any rule in their own anti-patterns section for emphasis; they may not weaken it.

---

## 1. Never fabricate

You may **select, reorder, reframe, re-emphasize, and use the target's vocabulary** for things the user has actually done. You may **not** invent roles, titles, employers, dates, metrics, tools, certifications, projects, or skills the user does not have. If a must-have is genuinely absent, leave it out and flag it — don't paper over it.

This applies to every visible-artifact skill: tailored resumes, cover letters, outreach messages, application answers, draft replies, negotiation copy, prep talking points, mock-interview feedback, coaching advice, career-path roadmaps.

If you would have to invent a number, a date, a company name, or a story to satisfy a request, **flag the gap to the user instead** and tell them what evidence is missing.

## 2. Read but never echo the `context:` block

The master profile's frontmatter `context:` block (`career_goal`, `additional_info`) is **internal signal only**. Skills read it to *direct* their output; they do not quote, paraphrase, or otherwise surface it in anything a recruiter, hiring manager, or reader sees. A reader looking at the artifact must not be able to recover the `context:` text from it.

This means: no echo in summaries, no echo in cover-letter "why this role" paragraphs, no echo in application long-form answers, no echo in outreach hooks, no echo in negotiation emails, no echo in interview talking points, no echo in resume content (including `extra_sections`).

**One documented exception:** `career-coach` may *paraphrase* `context.career_goal` and `context.additional_info` in its coaching answers (never verbatim), because direct advice is the point of the skill. The exception applies **only** to `career-coach` and is called out explicitly in its SKILL.md.

## 3. Verb sourcing for written output

For every skill whose output contains bullet points or short verb-led sentences (cover letter, outreach, draft-reply, negotiation counter, prep talking points, application paragraph answers, mock-interview feedback), pull openers from [`../tailor-resume/reference/action-verbs.md`](../tailor-resume/reference/action-verbs.md):

- Use the **category** that matches the action (Communication, Leadership/Mentoring, Research, Creative, Management, Organizational, Financial, Technical).
- **Vary verbs** — don't use the same verb twice within one short artifact (≤1 page) or more than twice on a long one.
- **Obey the anti-patterns** in that file: no weak/passive openers ("Responsible for", "Worked on", "Helped with", "Tasked with", "Involved in", "Duties included"); no first-person + article filler at the start of a bullet.

## 4. Region pack first

Before producing any text whose form or content varies by geography — resume length, salary mentions, cover-letter prevalence, sponsorship phrasing, CTC / notice period, date format, spelling variant, tone — read the target's region pack in [`../../knowledge/regions/<code>.md`](../../knowledge/regions/). The pack's **Decision rules (consumed by skills)** section is the canonical answer; do not invent regional norms.

For work-authorization specifically, defer to the canonical resolution in [`../../knowledge/work-authorization.md`](../../knowledge/work-authorization.md) — judged against the **job's** region, not the applicant's.

## 5. No emoji

The repo's brand voice is encouraging-coach, sentence-case, verb-led, **no emoji** — anywhere in any generated artifact, log line, or summary. (Lucide icons cover UI affordances when there is a UI; text outputs stay clean.)

## 6. Known-info gate — never re-ask what's already captured

Before asking the user for **anything**, check what the system already holds:

1. The **master profile** (`profile/master-profile.md`) — identity, target, links, work-auth, region, CTC/notice, context.
2. The **working job** (`jobs/current.json`) — the company/role/JD under work (see composition convention).
3. The relevant **sidecars** for this skill (scores, tailor, company research, triage — see below).

Only ask for fields that are **genuinely missing or `[VERIFY]`**, and ask them in **one batched prompt**, not drip-fed. Never re-request a job description, target role, region, work-auth, salary, or any profile fact another skill already collected — read it. If a value exists but looks stale (`[VERIFY]` or contradicted), confirm it in the same batch rather than re-collecting from scratch. The goal is a flawless flow: the user states each thing once.

---

## Composition convention (for context)

Skills compose via JSON **sidecars** at known paths, not by calling each other:

- `jobs/current.json` — the **job under work**: `{company, role, url, job_id, jd_text, region, source, captured_at}`. Written by `find-jobs` (on pick), `score-fit`, or the `apply-to-job` orchestrator. Read by `score-fit`, `tailor-resume`, `write-cover-letter`, `answer-application-questions`, `research-company` when no job is passed inline — so the JD is supplied **once** per application.
- `scores/<job-id>.score.json` — written by `score-fit`, read by `tailor-resume`.
- `resumes/<slug>.tailor.json` — written by `tailor-resume`, optionally read by `write-cover-letter` (keyword consistency).
- `resumes/<slug>.cover-letter.json` — written by `write-cover-letter`, reserved for a future `/render-resume --kind cover-letter`.
- `companies/<slug>.json` — written by `research-company`, read by `prep-interview` and `coach-negotiation` (auto-read by slug before asking).
- `inbox/triage-<YYYY-MM-DD>.json` — written by `triage-inbox`, read by `infer-status`, `draft-reply`.
- `requests/<request_id>.json` — written by `request-human-input` in compose mode; read by the optional JobClaw agent's HITL MCP.

If a sidecar is absent, the consuming skill either degrades gracefully (thin in-line derivation) or asks the user — it never invents the missing data. The full stage map + each skill's next step lives in [`../../knowledge/pipeline.md`](../../knowledge/pipeline.md).
