---
name: request-human-input
description: >
  Decide whether a blocking situation needs human input; compose a mobile-first prompt
  with ≤ 3 quick-reply options + a stated timeout default; parse a free-text reply back
  into a structured decision. v0 reasoning-only — delivery (Telegram / WhatsApp) lives
  in JobClaw's HITL MCP, not here. Always persists requests/<id>.json in compose mode.
when_to_use: >
  Use when a flagged answer-application-questions item, an `escalate` triage row, or any
  ambiguous / irreversible action needs a human. Two modes: compose (no reply) → produce
  the question; parse (reply given) → interpret it.
user-invocable: true
allowed-tools: Read, Write
---

# request-human-input

Pause the loop, ask one clear thing, resume on reply. **Hard rules:** [`../_shared/RULES.md`](../_shared/RULES.md).

## Two modes

### Compose mode (default — no `--reply`)
Decide if the situation needs human input. If yes, produce a mobile-first prompt + ≤ 3 options + a timeout default. **Always** writes `requests/<id>.json` so the the optional JobClaw agent's HITL MCP can pick it up.

### Parse mode (`--reply "<text>"`)
Match the reply to an option (case-insensitive prefix + fuzzy). Return a structured decision; mark the request file `resolved`.

## Inputs (compose)
- `situation` — 1–3 sentences. The blocker.
- `policy` — freeform string. Escalation rules (e.g., *"Escalate any irreversible action; auto-proceed on captcha if MFA backup is configured"*).
- `context_attachments[]` *(optional)* — file paths (screenshot, log) the human can review.
- `request_id` *(optional)* — caller-provided; else generate a 12-char hex slug.

## Inputs (parse)
- `--request_id` — which request the reply is for.
- `--reply` — the user's verbatim reply string.

## Method (compose)

1. **Decide if a human is needed.** Apply the `policy` text to `situation`. Output `{needs_human: bool, reason}`. If `false`, exit cleanly — no question, no file.

2. **If needed, compose the prompt** (mobile-first):
   - **Stem** — ≤ 1 sentence, ≤ 120 chars. The question itself.
   - **Options** — 1–3 quick-reply labels, each ≤ 24 chars. Verb-led.
   - **Default on timeout** — what JobClaw does if the human doesn't reply: `skip | queue | retry | abort`. Default `abort` for irreversible actions.
   - **Context snippet** — 1 line (e.g. *"Captcha at Workday submit for Mercury, screenshot attached"*). No more.

3. **Persist.** Always write `requests/<request_id>.json`:
   ```jsonc
   {
     "request_id": "...",
     "created_at": "ISO-8601",
     "situation":  "...",
     "policy":     "...",
     "prompt":     "string ≤ 120 chars",
     "options":    [{ "label": "string ≤ 24 chars", "value": "string" }],
     "timeout_default": { "after_minutes": 30, "action": "skip|queue|retry|abort" },
     "context_refs":    ["path/or/url"],
     "status":     "open"
   }
   ```

## Method (parse)

1. Load `requests/<request_id>.json`.
2. Match `reply` to `options[*].label` (case-insensitive prefix, then fuzzy). If no match → treat as `free_text`.
3. Emit:
   ```jsonc
   {
     "request_id":      "...",
     "chosen_option":   "<value> | null",
     "free_text":       "<verbatim reply> | null",
     "parsed_decision": "string — one of options[].value OR a normalized free_text",
     "resolved_at":     "ISO-8601"
   }
   ```
4. Mark the request file `status: resolved` and append the `resolution` block. **Do not delete** the file — the optional JobClaw agent's HITL MCP owns cleanup.

## Output
- Compose: prompt block on stdout (stem · options · timeout default · context refs) + the file at `requests/<request_id>.json`.
- Parse: the decision JSON on stdout + the updated request file.

## Anti-patterns
- More than 3 options.
- Stems > 120 chars (mobile UX dies).
- Multi-question prompts ("Should I skip AND send the email?"). Decompose.
- Assuming a delivery channel (Telegram / WhatsApp specifics). Those belong in the HITL MCP.
- Long context dumps in the stem — link to a path instead.
- Emoji.

## Rubric
- [ ] Stem ≤ 120 chars; options ≤ 24 chars; ≤ 3 options.
- [ ] `timeout_default.action` is explicit and conservative for irreversible actions (default `abort` when in doubt).
- [ ] `requests/<id>.json` always written in compose mode; never deleted in parse mode.
- [ ] In parse mode, an unmatched reply falls through to `free_text`, not a guessed option.
