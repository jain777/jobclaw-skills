# Import your memories from Claude / ChatGPT / Gemini

Your AI assistant already knows a lot about you. Pull that into JobClaw so you don't retype your whole career.

## Option A — paste this prompt into Claude / ChatGPT / Gemini

Copy the block below into a chat with the assistant **that knows you best**, then paste its reply back to `/build-profile`.

```
Based on everything you remember about me and our past conversations, write a thorough
professional dossier I can hand to a job-search assistant. Use clear markdown sections.
Be specific and factual — do NOT invent anything; omit what you don't know.

Include:
1. Identity: full name, current title, location, years of experience, work authorization.
2. Target: roles I want next, seniority, locations / remote preference, salary expectations,
   industries I like and ones I avoid, companies to exclude.
3. Experience: each role — company, title, dates, and 2–4 quantified achievements.
4. Education, certifications, languages.
5. Skills: technical and domain, grouped.
6. Projects / portfolio / open-source, with links if you know them.
7. Links: LinkedIn, GitHub, portfolio, personal site.
8. Constraints & preferences: relocation, sponsorship needs, travel, notice period,
   plus how I like my writing to sound (tone, things I avoid).

If you're unsure about a fact, mark it [VERIFY] rather than guessing.
```

## Option B — export your memory file

- **ChatGPT:** Settings → Personalization → Memory → review/save the entries, or Settings → Data Controls → Export data, and hand the relevant file to `/build-profile`.
- **Claude:** copy your profile/preferences or any saved project context.
- **Gemini:** Settings → Saved info / Activity, copy the relevant entries.

Drop the exported text/file into the chat and run `/build-profile`.

## Also helpful to provide
- Your **resume** (PDF, docx, or text).
- Your **LinkedIn PDF** (LinkedIn → your profile → *Resources* / *More* → *Save to PDF*).
- Links: **GitHub** (SWE/PM), **portfolio** (design/marketing/product), **personal site**, **LinkedIn URL**.

`build-profile` reads all of it, then asks you only what's still missing.
