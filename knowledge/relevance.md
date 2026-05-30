# Relevance — the shared matching engine

One rubric, three users. `find-jobs` (rank found jobs), `score-fit` (deep per-job score),
and `build-profile` (proof-point gaps) all speak the vocabulary defined here so "which jobs
fit me?" and "am I a fit for this target?" stay consistent. This file sits *above*
[`ai-roles.md`](ai-roles.md) and [`work-authorization.md`](work-authorization.md) — it
**references** them, never re-defines them.

Mechanism is **Claude-as-ranker**: a stdlib pre-filter does the cheap deterministic part;
Claude does the semantic part. No embeddings, no API key.

## The six factors

Mapped 1:1 onto `score-fit`'s existing subscore weights, plus one directional factor.

| Factor | Weight (score-fit) | Deterministic signal (`prerank.py`) | Semantic credit (Claude) |
|---|---|---|---|
| **role_match** | folds into must_haves (45) | title/role token overlap vs `target.roles`; AI title-filter hit | adjacent/transferable titles under a different name |
| **seniority** | 20 | seniority keyword vs `target.seniority` | scope/impact inferred from the JD |
| **domain** | 15 | `target.industries` ∩ company sector/`tags` | adjacent-domain credit (e.g. fintech ↔ payments) |
| **keywords** | 15 | literal skill-token overlap | skills under synonyms (RAG ≈ retrieval-augmented; SMM ≈ social media) |
| **location_work_auth** | 5 | location/remote vs `target`; (work-auth verdict in score-fit §0) | n/a — deterministic |
| **goal_alignment** | directional (not scored) | **n/a — never read in a script** | how well the role serves `context.career_goal` |

## "Semantic-via-Claude" — the explicit upgrade

Credit **transferable / adjacent** evidence, not just literal keyword presence:
- a requirement is **met** if the profile demonstrates it under *any* name (a "Visual AI agent"
  shows "computer vision"; "ran paid campaigns" shows "performance marketing");
- never credit `[VERIFY]` facts — neither literally nor as transferable evidence;
- "X OR Y" is satisfied by either; don't penalize for lacking the other half.

This is what distinguishes the new matching from the old keyword sort.

## The 0–100 scale (shared, not identical)

Both `find-jobs.fit_rank` and `score-fit.score` use 0–100 and the six factors, so they must be
**directionally consistent** — a job pre-ranked 80 should not score-fit to 25 absent new JD
information. They are **not identical**:
- **`fit_rank`** (find-jobs) — a *fast estimate* over the top-N, from a single batched pass; for triage/sorting.
- **`score`** (score-fit) — the *authoritative* number: full requirement-by-requirement met/partial/missing grading with evidence + itemized hard-constraint penalties. Run `/score-fit` for the number you act on.

## `fit_reason` contract (find-jobs)

One line, ≤120 chars, describes **the job's match to the candidate**. No emoji. **Never** quotes,
paraphrases, or echoes `context.*` — it describes the JOB, not the goal. Good:
`"Beauty D2C SMM in Delhi; matches content-calendar + influencer + +43% community growth."`

## goal_alignment + the `context:` no-echo rule (RULES.md §2)

`goal_alignment` reads `context.career_goal` **only to DIRECT** the score and the
`recommendation`/ordering — it is **directional, never numeric, never echoed**. A reader of
`fit_reason` / `strengths` / `gaps` / any score-fit output must not be able to recover the
context text from it. Structural guarantee: **`prerank.py` never receives the `context:` block**,
so the script layer cannot leak it. `career-coach` remains the only skill allowed to *paraphrase*
context.

## Proof-point vocabulary (build-profile)

"What strong candidates for a target show" = the canonical coverage list build-profile checks:
- **AI tracks** → the archetype **proof points** in [`ai-roles.md`](ai-roles.md) (col 3).
- **All tracks** → the **emphasis** column in [`build-profile/reference/track-presets.md`](../skills/build-profile/reference/track-presets.md).

build-profile compares these against the profile's Experience/Projects/Achievements and surfaces
the **target-framed** gap ("strong `<target>` candidates show X/Y/Z; you have X, missing Y/Z").

## Edge cases
- **Empty / `[VERIFY]`-heavy profile:** missing `target.*` → that factor is **neutral**, never zero.
  `[VERIFY]` facts are never credited. The proof-point gap prompt is most valuable here.
- **Undated job:** recency is **neutral** (never bottom-ranked just for lacking a date — matches
  the `jobstore` "undated kept by default" convention).
- **Non-AI track:** `archetype` is null; fall back to the generic six-factor rubric + track emphasis.
