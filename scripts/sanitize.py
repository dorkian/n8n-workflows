#!/usr/bin/env python3
"""Make an exported n8n workflow safe to publish.

Usage: sanitize.py IN.json OUT.json

Strips instance-specific data (workflow/version ids, pinData, meta, active flag),
replaces credential ids with placeholders and personal emails with example.com.
"""
import json, re, sys

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
KEEP_EMAILS = re.compile(r"@example\.(com|org)$|^YOUR_")
DROP_TOP = ("id", "versionId", "meta", "active", "pinData", "instanceId", "staticData", "createdAt", "updatedAt", "shared", "tags", "triggerCount", "isArchived")


def placeholder(cred_type: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", cred_type).upper() + "_CREDENTIAL_ID"


def clean_text(s: str) -> str:
    s = GDOC.sub(r"\1YOUR_GOOGLE_SHEET_ID", s).replace("YOUR_STUDIO_HUB_SHEET_ID", "YOUR_GOOGLE_SHEET_ID")
    return EMAIL.sub(lambda m: m.group(0) if KEEP_EMAILS.search(m.group(0)) else "you@example.com", s)


LONG = re.compile(r"[A-Za-z0-9_-]{30,}")
GDOC = re.compile(r"(docs\.google\.com/[a-z]+/d/)[A-Za-z0-9_-]{20,}")


def fix_resource_locator(d: dict) -> dict:
    """Google Sheets/Drive pickers store the real document id and URL; replace them."""
    val = d.get("value")
    if isinstance(val, str) and LONG.fullmatch(val) and re.search(r"\d", val) and re.search(r"[A-Za-z]", val):
        return {"__rl": True, "value": "YOUR_GOOGLE_SHEET_ID", "mode": "id"}
    if d.get("mode") == "list" and d.get("cachedResultName"):
        return {"__rl": True, "value": d["cachedResultName"], "mode": "name"}
    d.pop("cachedResultUrl", None)
    return d


def walk(o):
    if isinstance(o, dict):
        if o.get("__rl"):
            return fix_resource_locator({k: walk(v) for k, v in o.items()})
        return {k: walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v) for v in o]
    if isinstance(o, str):
        return clean_text(o)
    return o


def sanitize(wf: dict) -> dict:
    wf = walk(wf)
    for k in DROP_TOP:
        wf.pop(k, None)
    for node in wf.get("nodes", []):
        for ctype, c in (node.get("credentials") or {}).items():
            cid = c.get("id")
            if not cid or not re.fullmatch(r"(YOUR_[A-Z0-9_]+|[A-Z0-9_]+_CREDENTIAL_ID)", cid):
                c["id"] = placeholder(ctype)
    return wf


if __name__ == "__main__":
    src, dst = sys.argv[1:3]
    wf = json.load(open(src, encoding="utf-8-sig"))
    if isinstance(wf, list):
        wf = wf[0]
    json.dump(sanitize(wf), open(dst, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(dst, "a").write("\n")
