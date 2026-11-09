#!/usr/bin/env python3
"""CI gate: fail if any published workflow leaks instance data.

Checks every templates/**/workflow*.json for: invalid JSON, pinData, non-placeholder
credential ids, real-looking emails, secret/token patterns, and long id-like strings
(Google Sheet/Drive ids and similar). Exit code 1 on any finding.
"""
import glob, json, re, sys

SECRET = re.compile(r"(sk-[A-Za-z0-9]{20,}|sk-ant-[\w-]{20,}|xox[bap]-[\w-]+|ghp_\w{20,}|AKIA[0-9A-Z]{16}|AIza[\w-]{30,}|Bearer\s+[A-Za-z0-9._-]{20,}|eyJ[A-Za-z0-9_-]{20,}\.[\w-]{10,})")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
OK_EMAIL = re.compile(r"@example\.(com|org)$|^YOUR_")
LONG = re.compile(r"[A-Za-z0-9_-]{30,}")
UUID = re.compile(r"[0-9A-Za-z]{8}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]{12}")
CRED_OK = re.compile(r"YOUR_[A-Z0-9_]+|[A-Z0-9_]+_CREDENTIAL_ID")


def strings(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)
    elif isinstance(o, str):
        yield o


def check(path):
    errs = []
    try:
        wf = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [f"invalid JSON: {e}"]
    if wf.get("pinData"):
        errs.append("pinData present")
    for k in ("id", "versionId", "instanceId"):
        if k in wf:
            errs.append(f"top-level '{k}' present")
    for n in wf.get("nodes", []):
        for ctype, c in (n.get("credentials") or {}).items():
            if not CRED_OK.fullmatch(str(c.get("id"))):
                errs.append(f"node '{n.get('name')}': credential id for {ctype} is not a placeholder")
    for s in strings(wf):
        for m in SECRET.findall(s):
            errs.append(f"secret-like token: {m[:12]}...")
        for e in EMAIL.findall(s):
            if not OK_EMAIL.search(e):
                errs.append(f"email: {e}")
        for t in LONG.findall(UUID.sub("", s)):
            if CRED_OK.fullmatch(t):
                continue
            if re.search(r"\d", t) and re.search(r"[A-Za-z]", t) and not t.startswith(("n8n-nodes", "http")):
                errs.append(f"long id-like string: {t[:14]}...")
    return sorted(set(errs))


def check_csv(path):
    errs = []
    for line in open(path, encoding="utf-8"):
        for e in EMAIL.findall(line):
            if not OK_EMAIL.search(e):
                errs.append(f"email: {e}")
        for t in LONG.findall(line):
            if re.search(r"\d", t) and re.search(r"[A-Za-z]", t):
                errs.append(f"long id-like string: {t[:14]}...")
    return sorted(set(errs))


def main():
    files = sorted(glob.glob("templates/**/workflow*.json", recursive=True))
    if not files:
        print("no workflows found"); return 1
    bad = 0
    for f in files:
        errs = check(f)
        print(("FAIL " if errs else "ok   ") + f)
        for e in errs:
            print("     - " + e)
        bad += bool(errs)
    for f in sorted(glob.glob("templates/**/sheets/*.csv", recursive=True)):
        errs = check_csv(f)
        print(("FAIL " if errs else "ok   ") + f)
        for e in errs:
            print("     - " + e)
        bad += bool(errs)
    print(f"\n{len(files)} workflows, {bad} failing")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
