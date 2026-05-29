#!/usr/bin/env python3
"""Validate an `answer-application-questions` output against the input contract.

Usage:
  python3 answer.py --validate <out.json>                       # shape-only checks
  python3 answer.py --validate-pair <in.json> <out.json>        # full contract: every
                                                                #   input id is answered
                                                                #   or flagged; types,
                                                                #   lengths, enum values
                                                                #   all correct.

Stdlib only. Exits 1 on any error; prints OK on success.
"""
import argparse, json, re, sys


def load(p):
    with open(p) as f:
        return json.load(f)


def _len_chars(v):
    return len(v) if isinstance(v, str) else len(str(v))


def _sentence_count(s):
    return len([x for x in re.split(r"(?<=[.!?])\s+", str(s).strip()) if x])


def validate_answer(q, a):
    errs = []
    if not a.get("source_field"):
        errs.append("missing source_field")
    val = a.get("value", "")
    if val == "" or val is None:
        errs.append("empty value")
        return errs
    t = q.get("type")
    if t == "numeric":
        try:
            float(str(val).replace(",", "").strip())
        except Exception:
            errs.append(f"numeric value '{val}' is not a number")
    elif t == "yes_no":
        if val not in ("Yes", "No"):
            errs.append(f"yes_no must be exactly 'Yes' or 'No', got '{val}'")
    elif t == "short":
        n = _len_chars(val)
        if n > 240:
            errs.append(f"short {n} chars > 240")
        if _sentence_count(val) > 2:
            errs.append("short > 2 sentences")
    elif t == "paragraph":
        mx = q.get("max_chars", 600)
        n = _len_chars(val)
        if n > mx:
            errs.append(f"paragraph {n} chars > max_chars {mx}")
    elif t == "enum":
        opts = q.get("options", [])
        if val not in opts:
            errs.append(f"enum '{val}' not in options {opts}")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", metavar="OUT", help="shape-only check on an output file")
    ap.add_argument("--validate-pair", nargs=2, metavar=("IN", "OUT"),
                    help="full contract check given input + output files")
    a = ap.parse_args()

    errs = []
    if a.validate_pair:
        ip, op = a.validate_pair
        inp, out = load(ip), load(op)
        qs = {q["id"]: q for q in inp.get("questions", [])}
        answered = {x["id"] for x in out.get("answers", [])}
        flagged = {x["id"] for x in out.get("flagged", [])}
        for qid in qs:
            if qid not in answered and qid not in flagged:
                errs.append(f"[{qid}] not in answers[] or flagged[]")
            if qid in answered and qid in flagged:
                errs.append(f"[{qid}] in BOTH answers and flagged")
        for ans in out.get("answers", []):
            q = qs.get(ans["id"])
            if not q:
                errs.append(f"[{ans['id']}] answer to unknown question id")
                continue
            for e in validate_answer(q, ans):
                errs.append(f"[{ans['id']}] {e}")
    elif a.validate:
        out = load(a.validate)
        for ans in out.get("answers", []):
            if not ans.get("source_field"):
                errs.append(f"[{ans.get('id','?')}] missing source_field")
            v = ans.get("value")
            if v is None or v == "":
                errs.append(f"[{ans.get('id','?')}] empty value")
    else:
        ap.error("pass --validate <out.json> or --validate-pair <in.json> <out.json>")

    if errs:
        print("VALIDATION FAILED:")
        for e in errs:
            print("  " + e)
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
