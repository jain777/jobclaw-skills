# Resume style by track (industry-aware visual presets)

How a resume should *look* is industry-dependent. `render-resume` applies a
**track → {theme, accent color, font}** preset so the visual register matches the
field, instead of defaulting every resume to the same corporate blue. This file is
the rationale + the source of truth for the map implemented in
`skills/render-resume/scripts/render.py` (`_TRACK_STYLE`, `_pick_theme_auto`).

## Universal rules (all tracks)
- **Single column, selectable text, 9–11pt body.** Never sacrifice ATS-readability for looks.
- **One accent color, used only on rules / section titles / name / links — body stays black.**
- **Grayscale-safe accents only.** Mid-to-dark, saturated tones. Light/neon colors vanish when a resume is printed or faxed in B&W, so they're banned.
- **≤2 typefaces.** We use one family throughout (rendercv applies it to name/body/titles).
- Color/typography signal *register*; they never compensate for weak content.

## The map

| Track | Register | Theme (auto) | Accent | Font | Why |
|---|---|---|---|---|---|
| **marketing** | Expressive, warm | moderncv (styled) | burgundy `rgb(140,30,62)` | Lato | Creative roles get room to stand out; warm non-blue reads on-brand for brand/social/content. |
| **design** | Expressive, modern | moderncv (styled) | deep teal `rgb(13,110,120)` | Poppins | Geometric font + teal = contemporary/creative without going gimmicky. |
| **hr** | Approachable, professional | engineeringresumes / classic | teal `rgb(13,110,120)` | Lato | People-facing but not flashy. |
| **founders-office** | Modern, confident | classic | forest green `rgb(27,94,60)` | Lato | Distinctive, range-signaling, still clean. |
| **sales** | Confident, personable | classic | brick/terracotta `rgb(160,52,40)` | Lato | Results/relationship-driven; warm and bold but ATS-safe. |
| **customer-success** | Approachable | classic | teal-green `rgb(20,115,110)` | Lato | People-facing, friendly, professional. |
| **content** | Editorial, expressive | classic | plum `rgb(110,44,98)` | Lato | Writing/comms — creative-adjacent but highly readable. |
| **product** | Clean, minimal | engineeringresumes (ATS) | refined slate `rgb(36,62,99)` | Source Sans 3 | Tech-default minimalism; slate is calmer than the gimmicky bright blue. |
| **software** | Clean, minimal | engineeringresumes (ATS) | refined slate `rgb(36,62,99)` | Source Sans 3 | Same — ATS-first, one subtle accent. |
| **data** | Clean, minimal | engineeringresumes (ATS) | refined slate `rgb(36,62,99)` | Source Sans 3 | DS/ML/analytics — same clean tech register. |
| **operations** | Clean, structured | engineeringresumes (ATS) | steel blue-grey `rgb(55,71,79)` | Source Sans 3 | Ops/program/project — orderly and neutral. |
| **finance** | Conservative | classic | black `rgb(0,0,0)` | EB Garamond (serif) | Finance/consulting/law prefer minimal color + a serif face. |
| **quant** | Conservative | classic | near-black navy `rgb(20,33,61)` | XCharter (serif) | Conservative + a touch of structure for a technical-research field. |
| _default_ | — | engineeringresumes | theme default (blue) | theme default | No track → leave rendercv's defaults. |

## Overrides (precedence, highest first)
1. **CLI:** `render.py --accent "rgb(…)" --font "EB Garamond"`.
2. **Sidecar / intermediate `meta`:** `accent_color`, `font_family` (so `tailor-resume` can set a per-job look).
3. **Track default** (the table above).
4. **rendercv theme default.**

Themes also pass through `--theme <name>|auto`; `auto` routes per `_pick_theme_auto`.
Styled themes (moderncv/harvard/ink/opal/ember) print an ATS NOTE — prefer an
ATS-safe theme (engineeringresumes/classic/engineeringclassic/sb2nov) for portal
applications; the styled register is for direct/human sends.

## Available fonts (rendercv-bundled)
Sans: Lato, Source Sans 3, Open Sans, Noto Sans, Roboto, Ubuntu, Poppins, Raleway, Mukta, Open Sauce Sans.
Serif: EB Garamond, XCharter, Gentium Book Plus, Libertinus Serif, New Computer Modern.
Mono: DejaVu Sans Mono.

## Sources
Recruiter/industry guidance synthesized 2026-05-29 — creative roles tolerate
tasteful color (teal/burgundy/coral/forest), conservative roles want serif + minimal
color, tech wants clean ATS-first minimalism; always test in grayscale. See FINDINGS.
