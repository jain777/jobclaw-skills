---
name: coach-negotiation
description: >
  Coach a counter-offer — leverage analysis, floor / target / walk-away ranges per comp
  component, and a draft counter email the human sends (never auto-send). Reads
  companies/<slug>.json for market comp when present; otherwise asks for an inline range
  or runs a thin WebSearch. Region pack drives currency / structure (USD base+equity vs
  INR LPA CTC fixed+variable).
when_to_use: >
  Use after an offer arrives (or when preparing a counter). The reply-accept (offer)
  draft-reply template should have already bought time before this runs.
user-invocable: true
allowed-tools: Read, Write, WebFetch, WebSearch
---

# coach-negotiation

Negotiate honestly, ask for what's reasonable, never auto-send. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md). Leverage rubric: [`reference/leverage-rubric.md`](reference/leverage-rubric.md). Verb sourcing per `tailor-resume/reference/action-verbs.md` (Communication / Management).

## Inputs
1. **Offer** (required):
   ```jsonc
   {
     "company":  "...", "role": "...", "level": "...",
     "base":     195000, "equity": "...", "bonus": "...", "signing": "...",
     "location": "...", "deadline": "YYYY-MM-DD | null",
     "currency": "USD | INR | ..."
   }
   ```
2. **Profile** — `profile/master-profile.md`.
3. **Market comp** — one of: `companies/<slug>.json` (`compensation` block) · inline `--market "<range>"` · thin `WebSearch` sweep. **Never invent comp numbers.** If none of the three yields a sourced range, ask the user before proceeding.
4. **Competing offers** *(optional, strongest leverage)* — `[{company, base, equity, status}]`.

## Method

0. **Region pack.** Read `knowledge/regions/<code>.md` and `knowledge/work-authorization.md`:
   - **US:** comp = base + equity (4y vest, 1y cliff typical) + bonus + signing; pay-range laws in many states; any component negotiable.
   - **IN:** **CTC in LPA** (fixed + variable + ESOPs + retention bonus); **notice period** is part of negotiation; counter-offers more conservative — anchor on fixed CTC.

1. **Leverage analysis** per [`reference/leverage-rubric.md`](reference/leverage-rubric.md). Score each lever `strong / medium / weak / none`:
   - Competing offers (strongest).
   - Recruiter-initiated outreach (medium).
   - Niche / verified skill match (medium).
   - Tight timeline pressure (the recruiter's, not yours).
   - Deadline distance (more time → more room).
   - News-driven leverage (recent fundraise → cash; recent layoffs → equity over base).
   - Notice period (IN — short notice is bargaining value).
   
   Output `{ strong: [...], medium: [...], weak: [...], none: [...] }`.

2. **Ranges per component** — floor / target / walk-away:
   - `target` anchors on the high end of the market range; never below the offer.
   - `walk-away` = the number below which you'd decline; capture once even if the user has said "yes-pending-negotiation."
   - `floor` = a number you'd reluctantly accept.
   - For IN: explicitly split fixed CTC vs variable vs ESOPs.
   - If a component isn't negotiable for the company (e.g., rigid leveling at FAANG), say so and skip — don't ask anyway.

3. **Draft counter email** — 5–7 lines, polite, anchored to **one or two** leverage points (not all — looks needy). Asks for a **specific number** per negotiable component. Closes with a soft commitment ("happy to sign quickly once we land the package").
   - **No** multi-paragraph wall of text.
   - **No** "as you can see from my background" filler.
   - **No** `context:` echo.
   - **No** invented credentials, competing offers, or market numbers.
   - Sign with the profile's signature.

4. **Talking points for the verbal call** — 2–3 things to say if the recruiter wants to discuss live.

## Output
- `negotiation/<company-slug>-<role-slug>.strategy.md` — leverage analysis + per-component ranges + talking points + sources.
- `negotiation/<company-slug>-<role-slug>.counter-email.md` — the draft.
- Console: 3-line summary (top leverage · primary ask · expected pushback) + the **"REVIEW BEFORE SENDING"** warning + a suggestion to re-run `/coach-negotiation` with the recruiter's response when it arrives.

## Anti-patterns
- **Auto-sending.** Never — the skill writes drafts only.
- Inventing market comp without a source.
- Aggressive openers ("I demand…", "this is below market…").
- Echoing `context.additional_info` (medical / family / visa specifics) into the counter — those are internal signal.
- Asking for everything at once — pick the components with most leverage.
- Quoting competing-offer numbers as gospel; treat them as anchors, not facts.
- Mixing currency conventions (USD base+equity AND INR CTC) in one offer doc.
- Emoji.

## Rubric
- [ ] Every comp range cites a source (`companies/<slug>.json`, inline `--market`, or a `WebSearch` URL).
- [ ] Counter email is 5–7 lines; ≤ 1 leverage point per sentence; one specific number per negotiable component.
- [ ] Floor / target / walk-away set for each negotiable component.
- [ ] No `context:` echo.
- [ ] "REVIEW BEFORE SENDING" present in output footer.
- [ ] Region structure consistent (USD components or INR CTC structure, not mixed).
