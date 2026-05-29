---
name: map-career-path
description: >
  Map a transition from a current role to a target role — surface real LinkedIn-style
  transition examples + a personalized gap roadmap (skills, experiences, signals) grounded
  in the user's profile. Optional Google CSE script (better recall) when keys are present;
  WebSearch fallback ships keyless.
when_to_use: >
  Use when the user is contemplating a role change ("PM → Director of Product",
  "SWE → AI Engineer", "Analyst → PM"). Lower priority than the apply / recruiter loops.
user-invocable: true
allowed-tools: Read, Write, Bash, WebSearch
---

# map-career-path

Show the user how others made the move, and where they'd need to grow. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md).

## Inputs
1. **current_role** (required).
2. **target_role** (required).
3. Profile — `profile/master-profile.md` (for the gap analysis).
4. **Optional region** — `--region US | IN` (else use profile's `target.regions`).

## Method

0. **Resolve the search backend.**
   - If `GOOGLE_API_KEY` + `CSE_ID` env vars are present →  
     `python3 scripts/career_paths.py --current "<X>" --target "<Y>" --region <code>` (CSE-driven; better recall + structured snippets).
   - Else → `WebSearch` with the same 4 query templates the script uses.
   
   Either path returns up to 10 transition examples.

1. **Query templates** (the script + the WebSearch fallback use identical queries):
   - `"<current>" "<target>" site:linkedin.com/in`
   - `from "<current>" to "<target>" site:linkedin.com`
   - `"<target>" "previously <current>" site:linkedin.com`
   - `career transition "<current>" "<target>"` (broader, no site restriction)

2. **Filter for relevance.** Keep entries where the snippet/title shows both the current and target role (or near-synonyms — "Product Manager" matches "Sr. PM"). Dedup by canonical URL. Drop entries with no transition signal.

3. **Synthesize patterns.** Across the kept profiles, surface **3–5 common patterns** (e.g., *"most PM → Director moves went through a 1–2 yr 'Group PM' stint"*; *"AI Engineer transitions usually start with shipping one production LLM project at the current role"*). Patterns must be observable in the snippets — don't generalize beyond evidence.

4. **Personalize the roadmap** against the user's profile:
   - **You already have:** items the profile evidences.
   - **Build next:** specific, *measurable* skills/experiences (e.g., "ship one LLM-eval doc in the current role"; not "get more AI experience").
   - **Soft signals (optional):** writing, speaking, OSS, certifications — only real, named ones.

## Output

### `paths/<current-slug>__to__<target-slug>.md`
```
# <Current> → <Target>
> as of <date> · source: cse | websearch · region: <code>

## Real transitions (up to 10)
- Name (or anonymized) — current company → target company — <link>
  - snippet quote (≤ 20 words)
- ...

## Common patterns
- ...
- ...

## Your roadmap

### You already have
- ...  (cites profile facts)

### Build next
- specific, measurable item
- ...

### Soft signals (if you want them)
- real, named resource
- ...
```

### Stdout
3-line summary — `# transitions found · 1 dominant pattern · 1 highest-leverage next step`. Suggest `/find-jobs` filtered to bridge roles, then `/score-fit`.

## Anti-patterns
- Treating a single snippet as authoritative ("most people do X" with N=1).
- Inventing roles, company names, or transitions not in the snippets.
- Generic "get an MBA / certification" suggestions without profile context.
- Quoting `context.career_goal` verbatim (paraphrased direction is fine, verbatim is not).
- Sourcing transition examples from anything other than LinkedIn-public snippets.
- Emoji.

## Rubric
- [ ] ≥ 3 transition examples (or honestly report the small N when search returned less).
- [ ] Every transition has a link.
- [ ] Roadmap items are specific (no "get more experience").
- [ ] "You already have" cites actual profile facts.
- [ ] Graceful degrade without CSE keys (skill still produces a roadmap; just smaller N).
