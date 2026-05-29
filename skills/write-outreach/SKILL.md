---
name: write-outreach
description: >
  Write a short, profile-grounded cold outreach message to a recruiter, hiring manager,
  or potential referrer — LinkedIn DM or email — with one clear CTA and no flattery.
when_to_use: >
  Use when the user wants to reach out cold for a referral, info chat, recruiter intro,
  or post-event/post-interview follow-up — targeted at a specific person at a specific
  company.
user-invocable: true
allowed-tools: Read, Write
---

# write-outreach

Compose a short outreach message that earns a reply. **Hard rules:** see [`../_shared/RULES.md`](../_shared/RULES.md) — non-negotiable. Use the **Communication** verbs in [`../tailor-resume/reference/action-verbs.md`](../tailor-resume/reference/action-verbs.md).

## Inputs
1. **Profile:** read `profile/master-profile.md` (esp. `Notes / voice`, `target.tracks`, and the `context:` block for *direction only* — never echo).
2. **Recipient:** `{ name, role, company }`. Optional: known mutual, a recent post/work they did, prior touch.
3. **Platform:** `linkedin` (≤ 120 words, no subject) or `email` (≤ 180 words, with subject).
4. **Goal:** `intro` (be known) · `referral` (ask for an internal referral) · `info` (informational chat) · `follow-up` (post-application / post-interview / post-event).

If recipient / platform / goal is missing, ask once, batched.

## Method

0. **Region note.** Read the target region pack — outreach norms differ slightly (US: direct; IN: referrals matter more, lead with mutuals/track when possible).

1. **Pick the hook.** One verifiable, **profile-grounded** fact connecting candidate → company / role / recipient. Examples that work: same OSS project, alum overlap, identifiable recent work overlap, shared track. Examples that don't: generic "I admire your mission", company-name flattery in the opener.

2. **One CTA only.** Schedule 15 min · share a referral · answer a specific question · introduce a third party. No multi-CTA messages — they get ignored.

3. **Draft.**
   - **LinkedIn** — ≤ 120 words. No "Dear", no "Hope this finds you well." Open with the hook in ≤ 1 sentence. One CTA. Sign with first name.
   - **Email** — ≤ 180 words. Subject = 4–8 specific words ("Quick question on Mercury API roadmap", not "Quick question"). Body = 2 short paragraphs (hook+credential → CTA). Sign with full name + 1-line current credential.

4. **Self-check** against the anti-patterns and rubric before output.

## Output
- Console: the message (and subject if email).
- Write `outreach/<company-slug>-<role-slug>-<platform>.md` (create `outreach/` if needed). Include the subject as the H1 for email.
- **2-line rationale:** *what hook you chose · what CTA you set*. Helps the user judge before sending.
- Region tip when relevant (e.g., IN: "open with the mutual / IIT-batch line — converts far harder than the cold version").

## Anti-patterns (do not ship)
- Generic flattery ("I admire X's mission", "your work is incredible"). Cut.
- Naming the recipient's company in the first 5 words of the body. Sounds canned.
- Multi-CTA ("would you be open to a chat, OR willing to refer me, OR share advice?"). Pick one.
- First-person filler at the start: "I am writing to you because…" / "I wanted to reach out…". Remove.
- Echoing `context.career_goal` / `context.additional_info`. Direction only.
- Emoji.

## Rubric (one-page self-check)
- [ ] Hook is profile-grounded and verifiable (not flattery).
- [ ] Exactly one CTA.
- [ ] LinkedIn ≤ 120 words · Email ≤ 180 words.
- [ ] No company name in the first 5 words.
- [ ] No `context:` echo.
- [ ] Verb openers vary across the body (Communication / Leadership categories).
- [ ] Tone matches profile `Notes / voice`.
