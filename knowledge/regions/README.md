# Region knowledge packs

Shared, data-driven geographic intelligence. Job hunting differs by country — **where jobs live, whether sponsorship is a factor, what a resume should contain, how pay is expressed.** Each pack (`<code>.md`) encodes those differences as explicit rules; skills read the relevant pack instead of hardcoding assumptions.

## Who reads these
| Skill | Uses the pack for |
|---|---|
| `build-profile` | which region-specific fields to capture (e.g., India: current/expected CTC, notice period; US: work authorization) |
| `find-jobs` | which **sources/adapters** apply for the target region |
| `score-fit` | **sponsorship / work-authorization** logic (job country × applicant authorization) |
| `tailor-resume` | resume **conventions** (length, what to include/omit, spelling, date format) |
| `render-resume` | inherits conventions via the tailored content (format only) |

## How the region is resolved
1. **Applicant region** — `region:` in the profile frontmatter (e.g., `IN`, `US`). Inferred from `location` during `build-profile`.
2. **Target region(s)** — `target.regions:` (where the user is hunting; may differ from where they live, e.g., an India-based user targeting remote-US roles).
3. A search/score runs against the **target job's country**; a resume is tailored to the **target role's region**. When applicant region ≠ job region, sponsorship rules engage (see each pack).

## Files
- `_schema.md` — the section structure every pack follows.
- `us.md`, `india.md` — the current packs. Add a country by copying `_schema.md` and filling it in; no skill code changes needed.

## The core idea (example)
> An **India-based applicant applying to India jobs** does **not** face visa sponsorship as a filter — it's a non-issue, so `score-fit` must not penalize it, and `find-jobs` should source from India boards (Naukri, Instahyre, Cutshort, company ATS) not just US ones. The **same applicant applying to US jobs** *does* hit sponsorship as the dominant filter.
