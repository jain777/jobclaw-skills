# Work authorization & sponsorship — shared rules

The single entry point for how every skill reasons about visa/work-authorization. It defines
the canonical `work_auth` enum, the **cross-region resolution rule**, and the four effect verbs.
The country-specific *rows* live in each region pack (`knowledge/regions/<code>.md` →
"Work authorization & sponsorship"); this file is the algorithm + vocabulary they share.

**Consumed by:** `score-fit` (§0 + the location/work-auth sub-score), `build-profile` (which
auth field to collect), and `answer-application-questions` (future). Renderers and external-message
skills never surface raw auth status unless a form explicitly asks.

## Canonical `work_auth` enum

Use these exact values in `profile/master-profile.md` `work_auth:`:

```
US citizen | Green card | H-1B | OPT/CPT (F-1) | TN | Indian citizen/OCI | needs sponsorship | other
```

- `needs sponsorship` is the catch-all for any status that requires the employer to sponsor a visa
  in the **job's** country and isn't already covered above.
- `other` → record the specifics in the profile Notes; treat conservatively (see below).

## Effect verbs (used by every region pack)

| Verb | Meaning for score-fit |
|---|---|
| **NON-ISSUE** | Authorized locally. Never raise it, never penalize. Do not list it as a gap. |
| **MINOR-NOTE** | Usually fine; mention only if the listing flags a specific constraint (e.g. "no transfer"). No score penalty unless the listing conflicts. |
| **MAJOR-FILTER** | Real screening factor. Penalize and flag when the listing says "no sponsorship" / "must be authorized without sponsorship"; prefer known sponsors. |
| **DISQUALIFIER** | Hard block — the listing's stated requirement and the applicant's status are incompatible. Recommend Skip on this axis alone. |

## Cross-region resolution rule (the load-bearing part)

Authorization is judged against **the job's country, not the applicant's**.

1. Determine the **job's** country from the listing location → load that region pack.
2. Look up the applicant's `work_auth` in that pack's "Work authorization & sponsorship" table.
3. Apply the verb the table gives, using the definitions above.
4. If the applicant's region ≠ the job's region, **always use the job's pack.** (Example: an
   Indian citizen applying to an India job → NON-ISSUE; the *same* applicant applying to a US job
   flips to the US pack, where needing sponsorship is a MAJOR-FILTER.)
5. If the job's country has **no region pack yet**, fall back to: authorized in own country →
   NON-ISSUE; otherwise MAJOR-FILTER if the listing mentions sponsorship, else MINOR-NOTE. Note
   the missing pack as a `[VERIFY]`-style caveat in the output.

## Worked cases

- Indian citizen + India job → **NON-ISSUE** (never mention sponsorship).
- Indian citizen / OPT / "needs sponsorship" + US job that says "no sponsorship" → **MAJOR-FILTER**
  (near-disqualifier; surface it as the headline gap).
- H-1B holder + US job (no transfer restriction stated) → **MINOR-NOTE**.
- US citizen / Green card + US job → **NON-ISSUE**.
- Foreign national + India job → **MINOR-NOTE/MAJOR-FILTER** per the India pack (rare).
