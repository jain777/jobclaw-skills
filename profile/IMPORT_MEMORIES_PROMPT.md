# Import your career memories from Claude / ChatGPT / Gemini

The AI assistant you've used for your job search already knows a lot about you — recent interviews,
feedback, what you're aiming for. Pull **only the job-search-relevant parts** into JobClaw so you don't
retype your career.

## Option A — paste this prompt into Claude / ChatGPT / Gemini

Copy the block below into a chat with the assistant **that knows your career best**, then paste its
reply back to `/build-profile`. It deliberately asks for *only relevant* memories — not your whole chat
history.

```
From everything you remember about me across our past conversations, extract ONLY what is
relevant to my job search and career. Write it as clean markdown sections. Be specific and
factual — do NOT invent anything, and OMIT anything you're unsure of or that isn't career-related
(skip unrelated personal chatter, one-off questions, and trivia). If unsure about a fact, mark it
[VERIFY] instead of guessing.

Include, only where you actually have it:
1. Recent interviews & outcomes: companies, roles, rounds, what went well, feedback I got,
   and any rejections or offers — most recent first.
2. Career details not usually on a resume: scope, scale, key wins with numbers, leadership,
   domains, things I'm proud of, things I'd reframe.
3. What I'm targeting now: roles, seniority, locations / remote, comp expectations, industries
   I like and ones I avoid, companies to target or exclude.
4. Constraints & preferences: relocation, sponsorship/work-authorization, notice period,
   start timing, and how I like my writing to sound (tone, things I avoid).
5. Skills I've actually demonstrated (technical + domain), and any gaps I've mentioned.
6. Links if you know them: LinkedIn, GitHub, portfolio, personal site.

Keep it tight and relevant — quality over volume. Mark uncertain facts [VERIFY].
```

## Option B — export your saved memory

- **ChatGPT:** Settings → Personalization → Memory (review the entries), or Settings → Data Controls → Export data — hand over the career-relevant parts.
- **Claude:** copy your saved profile/preferences or relevant project context.
- **Gemini:** Settings → Saved info / Activity — copy the career-relevant entries.

Drop the exported text into the chat and run `/build-profile`.

## Also helpful to provide
- Your **resume** (PDF, docx, or text) and **LinkedIn PDF** (LinkedIn → your profile → *Resources* → *Save to PDF*).
- Links: **GitHub**, **portfolio**, **personal site**, **LinkedIn URL**.

`build-profile` reads all of it, folds in only what's new, and asks you only what's still missing.
