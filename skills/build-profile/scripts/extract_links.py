#!/usr/bin/env python3
"""Extract every URL embedded in a PDF resume — visible *and* hidden.

Claude's native Read tool surfaces visible text only. A `\\href{url}{LinkedIn}` in
a PDF rendered by LaTeX/Word/Docs shows as the word "LinkedIn"; the URL is hidden
inside a `/URI` annotation in a FlateDecode-compressed object stream. This script
decompresses every stream and pulls every URI it can find, then classifies each
URL by domain into the canonical link-network keys the profile schema uses.

  python3 extract_links.py <resume.pdf>

Stdout = JSON:
  {
    "urls": ["https://...", ...],            # de-duplicated, in discovery order
    "classified": {                          # canonical-key map
      "linkedin": "https://linkedin.com/in/...",
      "github": "...",
      "other": { "<label>": "<url>", ... }   # everything that didn't match a known network
    },
    "status": "ok | encrypted | scanned_image | unreadable",   # never crashes
    "note": "<human-readable hint when status != ok>"
  }

Always exits 0 on a real path (even for a bad PDF) so build-profile can branch on `status`
instead of catching a crash. Stdlib only (zlib + re + json) — runs anywhere Python 3 runs.
"""
import json
import re
import sys
import zlib
from urllib.parse import urlparse


# Map of URL host pattern → canonical key in profile.links.
# Order matters: first match wins; put more-specific patterns above generics.
_NETWORK_PATTERNS = [
    (re.compile(r"(^|\.)linkedin\.com$", re.I),                  "linkedin"),
    (re.compile(r"(^|\.)github\.(com|io)$", re.I),               "github"),
    (re.compile(r"(^|\.)scholar\.google\.[a-z.]+$", re.I),       "scholar"),
    (re.compile(r"(^|\.)orcid\.org$", re.I),                     "orcid"),
    (re.compile(r"(^|\.)huggingface\.co$", re.I),                "huggingface"),
    (re.compile(r"(^|\.)kaggle\.com$", re.I),                    "kaggle"),
    (re.compile(r"(^|\.)(twitter|x)\.com$", re.I),               "twitter"),
    (re.compile(r"(^|\.)substack\.com$", re.I),                  "substack"),
    (re.compile(r"(^|\.)medium\.com$", re.I),                    "medium"),
    (re.compile(r"(^|\.)dev\.to$", re.I),                        "dev_to"),
    (re.compile(r"(^|\.)dribbble\.com$", re.I),                  "dribbble"),
    (re.compile(r"(^|\.)behance\.net$", re.I),                   "behance"),
    (re.compile(r"(^|\.)stackoverflow\.com$", re.I),             "stackoverflow"),
    (re.compile(r"(^|\.)stackexchange\.com$", re.I),             "stackoverflow"),
    (re.compile(r"(^|\.)mastodon\.[a-z.]+$", re.I),              "mastodon"),
    (re.compile(r"(^|\.)bsky\.app$", re.I),                      "bluesky"),
    (re.compile(r"(^|\.)youtube\.com$", re.I),                   "youtube"),
    (re.compile(r"(^|\.)youtu\.be$", re.I),                      "youtube"),
    (re.compile(r"(^|\.)cal\.com$", re.I),                       "calendar"),
    (re.compile(r"(^|\.)calendly\.com$", re.I),                  "calendar"),
    (re.compile(r"(^|\.)leetcode\.com$", re.I),                  "leetcode"),
    (re.compile(r"(^|\.)topmate\.io$", re.I),                    "topmate"),
    (re.compile(r"^mailto:", re.I),                              "email"),
    (re.compile(r"^tel:", re.I),                                 "phone"),
]

_BACKSTOP_URL = re.compile(rb"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")
_URI_LITERAL = re.compile(rb"/URI\s*\(([^)]*)\)")
_URI_HEX = re.compile(rb"/URI\s*<([0-9A-Fa-f\s]+)>")
_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)

# PDFs produced by LaTeX/Word/Docs embed font-license and metadata URLs that are
# never the candidate's links. Drop them so build-profile's gap prompt is clean.
_JUNK_HOSTS = (
    "ams.org",                   # AMS font metadata (Computer Modern)
    "scripts.sil.org",           # SIL Open Font License
    "scripts.sil.org/ofl",
    "tug.org",                   # TeX Users Group
    "ctan.org",                  # CTAN package metadata
    "gust.org.pl",               # GUST font foundry
    "www.gust.org.pl",
    "www.w3.org",                # XMP/RDF schema namespaces
    "ns.adobe.com",              # Adobe XMP namespaces
    "purl.org",                  # Dublin Core schema
    "fontawesome.com",           # FA icon set metadata
    "schemas.openxmlformats.org",  # docx XML namespaces
)


def _is_junk(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    return any(host == j or host.endswith("." + j) for j in _JUNK_HOSTS)


def _classify(url: str) -> tuple[str, str]:
    """Return (canonical_key, url). If no known network, key = "other:<host>"."""
    if url.lower().startswith(("mailto:", "tel:")):
        scheme = url.split(":", 1)[0].lower()
        return ({"mailto": "email", "tel": "phone"}[scheme], url)
    host = (urlparse(url).hostname or "").lower()
    for pattern, key in _NETWORK_PATTERNS:
        if pattern.search(host):
            return (key, url)
    # Strip "www." for the freeform label so "www.example.com" → "example.com".
    label = host[4:] if host.startswith("www.") else host
    return (f"other:{label or 'unknown'}", url)


def _clean(url_bytes: bytes) -> str:
    """Decode a PDF string and trim trailing junk (closing parens, whitespace)."""
    s = url_bytes.decode("latin-1", "replace")
    # PDFs sometimes encode the URL with a trailing ")" or "."; strip common tails.
    return s.rstrip(").,;:'\" \t\r\n")


def _empty(status: str, note: str) -> dict:
    return {"urls": [], "classified": {"other": {}}, "status": status, "note": note}


def extract(pdf_path: str) -> dict:
    try:
        data = open(pdf_path, "rb").read()
    except OSError as e:
        return _empty("unreadable", f"could not open file: {e}")
    if not data:
        return _empty("unreadable", "file is empty")
    if not data.lstrip()[:5].startswith(b"%PDF"):
        return _empty("unreadable", "not a PDF (no %PDF header) — read it as text/markdown instead")

    encrypted = b"/Encrypt" in data
    has_text = False   # any text-showing operator across decompressed streams
    has_image = False  # any embedded raster image
    found: list[str] = []
    seen: set[str] = set()

    def add(url: str) -> None:
        if url and url not in seen and not _is_junk(url):
            seen.add(url)
            found.append(url)

    # 1. Walk every stream...endstream block; FlateDecode where possible.
    for raw in _STREAM.findall(data):
        try:
            dec = zlib.decompress(raw)
        except zlib.error:
            dec = raw
        if not has_text and (b"Tj" in dec or b"TJ" in dec or b" Td" in dec):
            has_text = True
        if not has_image and (b"/Image" in dec or b"/DCTDecode" in dec):
            has_image = True
        for u in _URI_LITERAL.findall(dec):
            add(_clean(u))
        for h in _URI_HEX.findall(dec):
            try:
                add(_clean(bytes.fromhex(h.decode().replace(" ", ""))))
            except ValueError:
                pass
        for u in _BACKSTOP_URL.findall(dec):
            add(_clean(u))
    if b"/Image" in data or b"/DCTDecode" in data:
        has_image = True

    # 2. Also scan the whole file uncompressed — some PDFs put /URI dicts in
    #    indirect-object headers outside any stream.
    for u in _URI_LITERAL.findall(data):
        add(_clean(u))
    for h in _URI_HEX.findall(data):
        try:
            add(_clean(bytes.fromhex(h.decode().replace(" ", ""))))
        except ValueError:
            pass
    for u in _BACKSTOP_URL.findall(data):
        add(_clean(u))

    # 3. Classify.
    classified: dict[str, object] = {"other": {}}
    for url in found:
        key, val = _classify(url)
        if key.startswith("other:"):
            label = key.split(":", 1)[1]
            # Don't overwrite an existing other-entry under the same domain — keep first.
            classified["other"].setdefault(label, val)
        else:
            # First match wins per canonical key (resumes occasionally have multiple GH
            # links — the first one is usually the personal profile).
            classified.setdefault(key, val)

    # Status: ok if we got URLs; otherwise diagnose why so build-profile can fall back.
    if found:
        status, note = "ok", ""
    elif encrypted:
        status, note = ("encrypted",
                        "PDF is encrypted/password-protected — links can't be read; "
                        "ask the user to re-export an unprotected copy or paste their URLs.")
    elif has_image and not has_text:
        status, note = ("scanned_image",
                        "PDF looks scanned/image-only (no selectable text) — Read won't see "
                        "the body either; ask the user to paste the text and their links.")
    else:
        status, note = ("ok", "no embedded URLs found (resume may simply have none)")

    return {"urls": found, "classified": classified, "status": status, "note": note}


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: extract_links.py <resume.pdf>", file=sys.stderr)
        sys.exit(2)
    result = extract(sys.argv[1])
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
