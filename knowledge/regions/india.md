
# India (IN)

## Meta
- code: IN · currency: INR · currency_format: CTC in **LPA** (lakhs per annum), e.g. `₹35 LPA` (fixed + variable + ESOPs) · date_format: DD/MM/YYYY · english_variant: British/Indian · timezone: IST

## Job sources (ranked)
1. **Naukri.com** `[user-session/manual]` — the dominant India board. No easy public API; reach via the user's session or pasted listings (future adapter). High coverage.
2. **LinkedIn India** `[user-session]` — conservative reads in the user's own session.
3. **Instahyre / Cutshort / Hirist** `[user-session/manual]` — tech-focused, recruiter-driven.
4. **Company ATS-direct** — many Indian startups use Greenhouse/Lever/Ashby (e.g., Razorpay, Meesho, CRED, Groww, Postman, Zomato) `[api]` — use `resolve_companies.py` → `ats_boards.py`. Enterprises/IT-services use Workday/SuccessFactors (the latter detect-only → Firecrawl/SerpApi fallback). SerpApi(`serpapi.py`) covers Naukri/LinkedIn-origin India listings too.
5. **Wellfound (India)** `[manual]`, **Foundit** (ex-Monster) `[manual]`, **IIMJobs** (senior/consulting) `[manual]`.
6. **Adzuna** `[api]` — `--country in`. Free baseline.

> POC reality: ATS-direct (Indian startups on Greenhouse/Lever) + Adzuna(`in`) are the automatable free sources today; Naukri/Instahyre are user-session/manual like LinkedIn.

## Work authorization & sponsorship
Enum + cross-region rule + effect verbs: [`../work-authorization.md`](../work-authorization.md)
(always resolve against the **job's** region — this pack — not the applicant's). This section holds
only the India-specific rows.

| Applicant | Job country = India | Effect verb |
|---|---|---|
| Indian citizen / OCI | ✅ already authorized | **NON-ISSUE — never raise it, never penalize** |
| Foreign national | needs employment visa (rare) | MINOR-NOTE/MAJOR-FILTER — flag only for non-Indian applicants |

**Key norm (the headline rule):** Indian employers assume local candidates are already authorized — visa sponsorship is **not** a factor for Indian applicants to Indian jobs, and listings rarely mention it. So for IN-applicant + IN-job, `score-fit` must **not** apply any sponsorship filter or gap. (The same Indian applicant targeting **US** jobs flips to the US pack, where sponsorship becomes the dominant filter.)

## Resume conventions
- **Length:** 1–2 pages acceptable.
- **Personal fields:** traditionally Indian resumes included photo, date of birth, marital status, father's/parent's name, gender, full address. **Modern best practice (and global/MNC/ATS): drop all of these.** Default to omitting; keep only if a specific traditional employer requires it. (Make this configurable, lean omit.)
- **Region-specific fields commonly expected:** **Current CTC**, **Expected CTC**, and **Notice period** (30/60/90 days) — often asked in the application and sometimes on the resume/summary. **Notice period is a major screening factor.**
- **Education detail:** 10th/12th board %s and grad CGPA/percentage are commonly listed, especially for freshers/early-career; "**fresher**" is the standard term for new grads.
- **Spelling:** British/Indian (organise, optimise, analyse). **Dates:** DD/MM/YYYY.
- **Format:** ATS-safe single column; `.pdf` and `.docx` both common.

## Compensation norms
- **INR, expressed as CTC in LPA** (fixed + variable + ESOPs). **Current CTC and Expected CTC are routinely asked up front** (unlike the US). Notice period negotiated alongside offer.

## Application norms
- Cover letters less emphasized than in the US. **Notice period** and **CTC expectations** are front-and-center. Referrals are very strong. A complete Naukri/LinkedIn profile matters for inbound recruiter reach.

## Decision rules (consumed by skills)
1. `find-jobs`: source from Indian ATS-direct startups + Adzuna(`in`); Naukri/Instahyre/LinkedIn-India via user-session/manual; do NOT lean on US-only boards/HN as primary.
2. `score-fit`: for IN applicant + IN job, **disable the sponsorship filter entirely**; weight notice-period fit and CTC alignment instead.
3. `build-profile`: capture `current_ctc`, `expected_ctc`, `notice_period`; do NOT collect photo/DOB/marital by default (note they're sometimes expected); capture CGPA/% if early-career.
4. `tailor-resume`: 1–2 pages, omit photo/DOB/marital by default, include notice period (and CTC if the user wants), British spelling, DD/MM/YYYY dates, "fresher" for new grads.
