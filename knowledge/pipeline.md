# Pipeline map — how the skills compose

The canonical job-hunt pipeline: the stages, which skill owns each, the sidecar each reads/writes,
and the **single next step** every skill should suggest when it finishes. Skills read this to "know
where they sit"; the `apply-to-job` orchestrator drives the evaluate→apply chain from it.

Composition is **file-based** (sidecars at known paths — see `skills/_shared/RULES.md` §Composition).
Each skill reads what's already captured (the **known-info gate**, RULES §6) and only asks for gaps.

## Stages

| Stage | Skill(s) | Reads | Writes | Next step |
|---|---|---|---|---|
| **Onboard** | `build-profile` | resume/LinkedIn PDF, links, AI-memory paste | `profile/master-profile.md` | `/find-jobs` |
| **Discover** | `find-jobs` | profile `target.*`, region packs, company catalog | `jobs/found-<date>.json` (+ `jobs/current.json` on pick) | `/score-fit` (or `/apply-to-job`) |
| **Evaluate** | `score-fit` | profile, `jobs/current.json` or pasted JD, region/work-auth | `scores/<job-id>.score.json` (gated), `jobs/current.json` | Apply → `/tailor-resume` (or `/apply-to-job`); Skip → next job |
| **Apply** | `apply-to-job` (orchestrator) → `tailor-resume` → `render`+`review-render` → `write-cover-letter` → `answer-application-questions` | profile, `jobs/current.json`, `scores/<id>.score.json` | `resumes/<slug>.{md,tailor.json,json,pdf}`, `resumes/<slug>.cover-letter.{md,json}` | Submit (human/agent), then `/triage-inbox` as replies arrive |
| **Materials (à la carte)** | `tailor-resume`, `render-resume`, `review-render`, `write-cover-letter`, `write-outreach` | profile, `jobs/current.json`, tailor sidecar | resume PDF, cover letter, outreach text | `/apply-to-job` to assemble the full package |
| **Manage (recruiter loop)** | `triage-inbox` → `infer-status` → `draft-reply` | pasted email(s), `inbox/triage-<date>.json`, `status/taxonomy.md` | `inbox/triage-<date>.json`, tracker, `inbox/replies/<slug>.md` | triage→`/infer-status`; status→`/draft-reply`; reply→you send→`/infer-status` |
| **Research** | `research-company` | company+role, web | `companies/<slug>.{md,json}` | pre-interview → `/prep-interview`; pre-offer → `/coach-negotiation` |
| **Interview** | `prep-interview` → `mock-interview` | profile, `companies/<slug>.json` | `interviews/<slug>-<date>.{prep,report}.json` | prep→`/mock-interview`; after mock→`/prep-interview` for weak areas |
| **Offer** | `coach-negotiation` | offer, `companies/<slug>.json`, region pack | negotiation draft | you send the counter → re-run `/coach-negotiation` with their reply |
| **Cross-cutting** | `career-coach`, `map-career-path`, `request-human-input` | profile (+ context for career-coach) | coaching/paths/requests sidecars | route to the relevant apply/discover skill |

## Per-skill "next step" (use verbatim in the Next-steps block)

- **build-profile** → "Profile saved. Next: `/find-jobs` to pull matching roles (or `/apply-to-job <url>` to evaluate a specific one)."
- **find-jobs** → "Saved N jobs. Next: `/score-fit` on the top results, or `/apply-to-job <job_id>` to run the full apply chain."
- **score-fit** → Apply: "Strong fit. Next: `/tailor-resume` (or `/apply-to-job` for the whole package)." Skip: "Low fit — skip; try the next job."
- **tailor-resume** → "Resume PDF ready. Next: `/write-cover-letter`, then submit (or `/apply-to-job` to do both + the form answers)."
- **render-resume** → "PDF rendered. Next: `/review-render` if not already run, then `/write-cover-letter`."
- **review-render** → "Resume passed QA. Next: `/write-cover-letter`, then apply."
- **write-cover-letter** → "Cover letter ready. Next: `/answer-application-questions` for the form, then submit."
- **answer-application-questions** → "Answers ready. Submit the application, then `/infer-status` to log it."
- **write-outreach** → "Message ready. After you send it, `/infer-status` to track the touch."
- **triage-inbox** → "Triaged. Next: `/infer-status` to update the funnel, then `/draft-reply` for the suggested action."
- **infer-status** → "Status updated. Next: `/draft-reply` with the suggested intent (or `/coach-negotiation` if it's an offer)."
- **draft-reply** → "Draft ready — you send it. After sending, `/infer-status` to advance the status."
- **research-company** → "Brief saved. Next: `/prep-interview` (pre-interview) or `/coach-negotiation` (pre-offer)."
- **prep-interview** → "Prep brief ready. Next: `/mock-interview` to practice it."
- **mock-interview** → "Scored. Next: re-run `/prep-interview` on the weak areas, or `/research-company` for more depth."
- **coach-negotiation** → "Counter drafted — you send it. Re-run `/coach-negotiation` with their reply when it lands."
- **career-coach** → "If you want an artifact, jump to `/tailor-resume`, `/write-outreach`, or `/find-jobs`."
- **map-career-path** → "Roadmap ready. Next: `/find-jobs` filtered to bridge roles, then `/score-fit`."
- **request-human-input** → "Question composed/parsed. Resume the action that triggered it."
- **apply-to-job** → "Application package assembled. Review, then submit (or hand to the JobClaw agent for auto-apply)."
