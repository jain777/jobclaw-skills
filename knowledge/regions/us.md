# United States (US)

## Meta
- code: US · currency: USD · currency_format: `$180,000` annual · date_format: MM/DD/YYYY · english_variant: American · timezones: ET/CT/MT/PT

## Job sources (ranked)
1. **Company ATS-direct** — Greenhouse, Lever, Ashby, **SmartRecruiters**, Workday `[api]` (free, structured, ToS-clean). Best quality. Use `resolve_companies.py` → `ats_boards.py` / `smartrecruiters.py` / `workday.py`. Enterprise iCIMS/Taleo/Oracle/SuccessFactors are detect-only → Firecrawl/SerpApi fallback.
2. **SerpApi Google Jobs** `[api]` (freemium, built: `serpapi.py`) — aggregates Indeed/LinkedIn/ZipRecruiter/Workday. Best recall; budget-cap a few queries/run.
3. **Adzuna** `[api]` — `--country us`. Free baseline.
4. **Hacker News "Who is hiring"** `[api]` — startup-heavy.
5. **LinkedIn** `[user-session]` — conservative reads in the user's own session (JobClaw-side).
6. **Wellfound** (startups) `[manual]`.

## Work authorization & sponsorship
Enum + cross-region rule + effect verbs: [`../work-authorization.md`](../work-authorization.md)
(always resolve against the **job's** region — this pack — not the applicant's). This section holds
only the US-specific rows.

| Applicant authorization | Job country = US | Effect verb |
|---|---|---|
| US citizen / Green card | ✅ no issue | NON-ISSUE |
| H-1B (transferable) | usually fine | MINOR-NOTE (only if role says "no transfer") |
| OPT/CPT, or needs sponsorship | ⚠️ depends on employer | MAJOR-FILTER — penalize/flag if listing says "no sponsorship" / "must be authorized without sponsorship"; prefer known sponsors. DISQUALIFIER when the listing's requirement is explicitly incompatible. |

Norm: many US listings state "must be authorized to work in the US **without sponsorship**." If the applicant needs sponsorship, treat that phrase as a near-disqualifier and surface it.

## Resume conventions
- **Length:** 1 page (<10 yrs experience), 2 max.
- **Omit:** photo, date of birth, marital status, gender, nationality, full street address (city, ST is fine). These can trigger bias screens and look unprofessional in the US.
- **Sections:** Summary (optional), Experience (reverse-chron, action+metric bullets), Skills, Education. GPA only if new grad and strong.
- **Spelling:** American (organize, optimize, analyze).
- **Format:** ATS-safe single column, selectable text; `.pdf` for sending, `.docx` often required for ATS uploads.

## Compensation norms
- Annual **USD**: base + bonus + equity. Salary expectations often deferred to later stages; several states mandate pay ranges in postings. Do **not** put current/expected salary on the resume.

## Application norms
- Cover letters optional/role-dependent (stronger for senior, mission-driven, or career-change). Referrals are high-leverage. "Quick apply" common.

## Decision rules (consumed by skills)
1. `find-jobs`: source from ATS-direct + Adzuna(`us`) + HN (+ SerpApi when enabled); LinkedIn only via user-session.
2. `score-fit`: apply the sponsorship table above; only raise sponsorship as a gap when the applicant needs it.
3. `build-profile`: capture `work_auth`; do NOT collect photo/DOB/marital; no CTC/notice-period fields.
4. `tailor-resume`: 1 page, omit personal/photo fields, American spelling, no salary on resume, MM/DD or "Mon YYYY" dates.
