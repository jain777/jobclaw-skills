"""Shared helpers for the rendercv-based render-resume skill.

`render.py` converts a JSON-Resume intermediate into a rendercv YAML input file
and shells out to `rendercv` (Typst engine). This module owns the cross-cutting,
template-agnostic concerns:

  * track-driven default ordering for the header links (carried over from the
    old LaTeX renderer — the orderings are unchanged),
  * the ATS-safety classification of rendercv's built-in themes.

LaTeX escaping / Unicode normalization are gone: rendercv consumes Markdown and
Typst handles Unicode natively, and we hand it JSON (a valid YAML subset) so
there is no hand-quoting to do. Stdlib only (`re`).
"""

# ---------------------------------------------------------------------------
# Header-link ordering (shared, carried over from the LaTeX renderer)
# ---------------------------------------------------------------------------

# SINGLE SOURCE OF TRUTH for per-track contact ordering. Docs (build-profile/
# reference/track-presets.md, render-resume/SKILL.md, profile-schema.md) point here
# instead of re-listing the orders. Precedence chain (see resolve_contact_order):
#   sidecar `contact_order` -> profile `contact_priority` -> track default (below)
#   -> FALLBACK_CONTACT_ORDER.
# Email + phone are separate rendercv `cv` fields and are excluded here; these keys
# order the `social_networks` + Links section.
DEFAULT_CONTACT_ORDER_BY_TRACK = {
    "software":        ["github", "linkedin", "portfolio", "website", "stackoverflow"],
    "product":         ["linkedin", "portfolio", "github", "medium", "twitter"],
    "quant":           ["github", "linkedin", "scholar", "kaggle", "orcid"],
    "finance":         ["linkedin", "website", "medium"],
    "marketing":       ["portfolio", "linkedin", "twitter", "medium", "substack", "youtube"],
    "founders-office": ["linkedin", "portfolio", "twitter", "substack", "calendar", "website"],
    "hr":              ["linkedin", "website", "medium"],
    "design":          ["portfolio", "linkedin", "dribbble", "behance", "website", "instagram"],
    "data":            ["github", "linkedin", "kaggle", "scholar", "portfolio"],
    "sales":           ["linkedin", "website", "twitter"],
    "operations":      ["linkedin", "website", "github", "medium"],
    "customer-success": ["linkedin", "website", "medium"],
    "content":         ["portfolio", "linkedin", "substack", "medium", "twitter"],
}
FALLBACK_CONTACT_ORDER = ["linkedin", "github", "portfolio", "website", "twitter"]


def resolve_contact_order(track, sidecar_order=None, profile_priority=None):
    """Pick the ordering list: sidecar wins -> profile -> track default -> fallback.

    Email/phone may appear in the incoming lists (they are legal profile keys);
    callers filter them out since rendercv renders email/phone separately.
    """
    if sidecar_order:
        return [k for k in sidecar_order if k not in ("email", "phone")]
    if profile_priority:
        return [k for k in profile_priority if k not in ("email", "phone")]
    return DEFAULT_CONTACT_ORDER_BY_TRACK.get(track, FALLBACK_CONTACT_ORDER)


def order_link_keys(available_keys, contact_order, contact_hidden=None):
    """Return `available_keys` sorted by `contact_order`, leftovers appended.

    `available_keys` is an iterable of link keys present in the profile (lowercased,
    excluding email/phone). `contact_hidden` keys are dropped entirely. No cap —
    rendercv wraps the header itself.
    """
    hidden = {k.lower() for k in (contact_hidden or [])}
    present = [k for k in available_keys if k.lower() not in hidden]
    ordered, used = [], set()
    for key in contact_order:
        if key in present and key not in used:
            ordered.append(key)
            used.add(key)
    for key in present:
        if key not in used:
            ordered.append(key)
            used.add(key)
    return ordered


# ---------------------------------------------------------------------------
# ATS-safety classification of rendercv's built-in themes
# ---------------------------------------------------------------------------

# rendercv ships 9 built-in themes. All are single-column and produce selectable
# text with real PDF hyperlink annotations, but some apply heavier styling (color
# blocks, denser typography) that can degrade older ATS pdf-to-text pipelines.
# We expose all 9; this list marks the conservative, "parses everywhere" subset.
ALL_THEMES = (
    "classic", "engineeringresumes", "engineeringclassic", "sb2nov",
    "moderncv", "harvard", "ink", "opal", "ember",
)
ATS_SAFE_THEMES = ("engineeringresumes", "classic", "engineeringclassic", "sb2nov")
DEFAULT_THEME = "engineeringresumes"  # the most ATS-aligned of the built-ins


def theme_is_ats_safe(theme):
    """True if `theme` is in the conservative ATS-safe subset."""
    return theme in ATS_SAFE_THEMES
