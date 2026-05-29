# AI roles — taxonomy, title filter & archetypes

A shared lens for AI/ML roles, used across tracks (an "AI Engineer" is the `software` track with an
AI flavor; an "AI PM" is `product`; an "Applied Scientist" is `data`). AI is modeled as a **role lens**
layered on the existing tracks, not a separate track.

**Consumed by:** `find-jobs` (AI title filter + the AI/YC company subset), `score-fit` (archetype
detection → which proof points matter), and `tailor-resume` (which AI keywords to surface).

> The six archetypes below are adapted from the open-source **career-ops** project
> (github: santiagofdezg/career-ops — AI job-search agent), which classifies every AI role into an
> archetype to drive CV framing. Credited; reworked to fit JobClaw's skills.

## Title filter (for find-jobs AI searches)

**Positive (an AI role):** AI Engineer · ML Engineer · Machine Learning Engineer · Applied Scientist ·
Research Engineer · Research Scientist · Applied AI · AI/ML · MLOps · LLM Engineer · GenAI · Generative AI ·
NLP Engineer · Computer Vision · Deep Learning · Data Scientist (ML-heavy) · AI Product Manager ·
Forward Deployed Engineer · AI Solutions Architect · Prompt Engineer · Agent Engineer · RAG ·
AI Platform · Conversational AI · Speech/Voice AI · AI Safety · Alignment.

**Negative (filter out unless the user wants them):** Sales/Account roles "for AI companies" that aren't
technical · "AI" used only as a buzzword in non-AI roles · pure data-analyst/BI when the user targets ML ·
intern/trainee (unless seniority allows).

**Seniority boost:** Senior · Staff · Principal · Lead · Head of AI · Director · Member of Technical Staff (MTS).

## The six AI archetypes

Detect the archetype(s) from JD keywords (a role can be a hybrid of two). The archetype tells
`score-fit` which proof points to weight and `tailor-resume` which evidence to surface.

| Archetype | JD signals | Proof points to emphasize |
|---|---|---|
| **AI Platform / LLMOps** | observability, evals, pipelines, monitoring, inference, reliability, cost | production ML systems, eval harnesses, latency/cost wins, on-call |
| **Agentic / Automation** | agent, multi-agent, orchestration, tool-use, HITL, workflow | shipped agents, tool/function-calling, error-handling, human-in-the-loop |
| **Technical AI PM** | PRD, roadmap, discovery, stakeholders, 0→1, product | AI products shipped, metrics moved, model/UX tradeoffs, discovery |
| **AI Solutions Architect** | architecture, enterprise, integration, design, systems | system design, integrations, enterprise/security readiness |
| **AI Forward-Deployed Engineer** | client-facing, deploy, prototype, fast delivery, field, FDE | prototype→prod speed, customer deployments, ambiguity |
| **AI Transformation / Enablement Lead** | change management, adoption, enablement, transformation | org rollout, training, adoption metrics |

## Company sourcing for AI roles

`find-jobs` should bias the company set toward AI employers when the target is AI:
- **Catalog rows tagged `ai`** in `companies.csv` `tracks` (frontier labs + hot AI startups; see
  `knowledge/companies/` and the `source_index=ai`/`yc` rows).
- **YC AI-tagged companies** (ingested via `scripts/yc_companies.py --ai-only`).
- Frontier labs are first-class targets even when not on a classic ATS (route via the
  enterprise/JS fallback when needed).

## How skills apply this
- **find-jobs:** when `target.roles`/`target.tracks` indicate AI, apply the positive/negative title
  filter to every adapter's results, and prioritize `ai`/`yc`-tagged catalog companies + YC AI list.
- **score-fit:** detect the archetype, then weight `domain` + `must_haves` sub-scores toward that
  archetype's proof points; note archetype in the sidecar `gaps`/`strengths`.
- **tailor-resume:** surface the archetype's proof points and the matched positive keywords (no fabrication).
