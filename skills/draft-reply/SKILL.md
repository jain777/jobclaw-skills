---
name: draft-reply
description: >
  Draft a reply email matched to one of the taxonomy's reply intents — reply-schedule,
  reply-accept (with sub-templates for scheduling / assessment / offer), reply-decline,
  reply-ask, reply-info, follow-up. Mirrors inbound tone; interpolates dates / links;
  uses the profile's signature. Never auto-sends.
when_to_use: >
  Use after triage-inbox suggests an action OR when the user pastes a thread and names
  the intent. Pairs with infer-status to know which intent fits.
user-invocable: true
allowed-tools: Read, Write
---

# draft-reply

One reply, one intent, no auto-send. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md). Use **Communication / Leadership** verbs from [`../tailor-resume/reference/action-verbs.md`](../tailor-resume/reference/action-verbs.md). All reply-intent labels come from [`../../knowledge/status/taxonomy.md`](../../knowledge/status/taxonomy.md).

## Inputs
1. **Thread** — the inbound email plus any prior thread (paste or `--in inbox/<thread-id>.json`).
2. **Intent** — one of `reply-schedule | reply-accept | reply-decline | reply-ask | reply-info | follow-up`.
   - For `reply-accept`, also pass `accept_kind ∈ {schedule, assessment, offer}` (templates diverge).
3. **Triage extraction** *(optional)* — `{ dates[], links[], asks[], deadline, ... }` from `inbox/triage-<date>.json`. If absent, the skill runs a thin in-line classify to recover the minimum (don't write a triage record back — that's `triage-inbox`'s job).
4. **Profile** — `profile/master-profile.md` for signature, timezone, voice, and (if intent is `reply-info`) the `preferences.*` data the recruiter is asking for.
5. **Specifics**:
   - `reply-schedule` → 2–3 candidate windows the user offers (in the user's tz, with the recruiter's tz noted).
   - `reply-accept (offer)` → **do not write an acceptance email here.** Output a deliberately conservative acknowledgement that buys time and points the user to `/coach-negotiation`. Emit a warning in the rationale.
   - `reply-decline` → reason category (`accepted-elsewhere | not-aligned | timing | other`); the skill phrases gracefully.
   - `reply-ask` → exactly **one** question to ask.
   - `reply-info` → which `preferences.*` fields the recruiter asked for.
   - `follow-up` → days since last contact (drives tone — gentle at 7d, firm at 21d).

## Method

0. **Region note.** Read the target region pack — tone defaults (US: direct, IN: warmer with explicit thanks); spelling variant; date format used in the body.

1. **Mirror the inbound.** Match salutation style (`Hi <First>` vs `Dear <Last>`), formality, length expectations. Don't out-formal the recruiter; don't be sloppier either.

2. **Interpolate from extraction.** Dates → write in the format used by the inbound (or the region default if conflicting). Links → use the verbatim URL; if a calendar link is in `links[].kind == schedule`, *prefer* that to your own time proposals unless the recruiter explicitly asked for times.

3. **Apply the intent template.** Each intent has a clean shape:

   - **reply-schedule** — 3 short lines: thanks + acknowledgement / 2–3 candidate windows (timezone explicit) / sign-off.
   - **reply-accept (schedule)** — 2–3 lines: confirms a specific time / confirms the link or platform / sign-off.
   - **reply-accept (assessment)** — 2–3 lines: confirms commitment + a realistic submission ETA / one question if there's ambiguity (else cut) / sign-off.
   - **reply-accept (offer)** — **buys time**, does not accept. 3 lines: gratitude + that you're reviewing + a soft expected-response date (`I'll come back to you by <date>`). Suggest `/coach-negotiation` in the console rationale.
   - **reply-decline** — 3 short lines: gratitude / brief reason from the category (no detail beyond what the category gives) / door-open close ("would love to keep in touch").
   - **reply-ask** — 2 lines: one specific question / sign-off. Don't list multiple questions — pick the most consequential.
   - **reply-info** — 2–4 lines: provide the asked-for `preferences.*` data, exactly. CTC (IN) / work-auth (US) formatted per region conventions. No padding.
   - **follow-up** — 2–3 lines: polite reference to the last touch (date) / brief restating-of-interest / sign-off. Tone scales with elapsed days.

4. **Signature.** Use the profile's signature block (the user's name + one credibility line — current title only). Don't add address or social links beyond what the user's signature already has.

5. **Self-check.** Run the anti-patterns + rubric before output.

## Output
- Console: the reply (subject if email; otherwise `Re: <inbound subject>`).
- Write `inbox/replies/<thread-slug>.md` — body + subject as H1.
- **Two-line rationale**: *what I assumed* (the inbound facts the draft depends on) · *what to verify before sending* (times, link, name spelling).
- **Never auto-send.** "Human sends" is explicit in the output footer.
- If intent was `reply-accept (offer)`: add a single line "Suggested next: `/coach-negotiation` — do not send this draft as an acceptance."

## Anti-patterns
- Auto-CCing anyone (the agent doesn't know who).
- Multi-question replies for `reply-ask`.
- Inventing availability slots not provided by the user.
- Promising salary numbers in any `reply-accept` template.
- Echoing `context.career_goal` / `context.additional_info`.
- Long thank-you preambles for `reply-decline`.
- Mismatched salutation formality.
- Emoji.

## Rubric
- [ ] Subject line is `Re: <inbound>` (or the same explicit subject the inbound uses).
- [ ] Intent template matches the rules above; length ≤ template ceiling.
- [ ] Dates interpolated correctly; tz mentioned where it matters.
- [ ] Profile signature used; no extra contact info.
- [ ] No `context:` echo.
- [ ] For `reply-accept (offer)`: draft is an *acknowledgement*, not an acceptance; coach-negotiation recommended.
- [ ] "Human sends" footer present.

## Next steps
Draft ready — you send it. After sending, `/infer-status` to advance the status.
