#!/usr/bin/env python3
"""Generate catalog.json, the root README table and each template README
from templates/*/meta.json and the workflow files themselves, so node counts,
triggers and credential lists can never drift from the actual JSON."""
import glob, json, os, re
from render_diagram import render

def short(t): return t.split(".")[-1]

def facts(path):
    wf = json.load(open(path, encoding="utf-8"))
    diagram = os.path.basename(path).replace("workflow", "diagram").replace(".json", ".svg")
    open(os.path.join(os.path.dirname(path), diagram), "w", encoding="utf-8").write(render(wf))
    nodes = wf.get("nodes", [])
    real = [n for n in nodes if "stickyNote" not in n["type"]]
    triggers = sorted({short(n["type"]) for n in real if re.search(r"(?i)trigger|webhook|schedule", n["type"])})
    creds = sorted({c for n in real for c in (n.get("credentials") or {})})
    services = sorted({short(n["type"]) for n in real if not re.search(r"(?i)^(set|if|switch|merge|code|noOp|wait|splitInBatches|function|filter|aggregate|sort|limit|stickyNote|respondToWebhook|executeWorkflow|manualTrigger)", short(n["type"]))})
    return dict(file=os.path.basename(path), diagram=diagram, name=wf.get("name"), nodes=len(real), triggers=triggers, credentials=creds, node_types=services)

def build():
    cat = []
    for meta_path in sorted(glob.glob("templates/*/meta.json")):
        d = os.path.dirname(meta_path); slug = os.path.basename(d)
        meta = json.load(open(meta_path, encoding="utf-8"))
        wfs = [facts(p) for p in sorted(glob.glob(d + "/workflow*.json"))]
        entry = dict(slug=slug, **meta, workflows=wfs, total_nodes=(max if meta.get("alternatives") else sum)(w["nodes"] for w in wfs),
                     credentials=sorted({c for w in wfs for c in w["credentials"]}))
        cat.append(entry)
        write_readme(d, entry)
    json.dump(cat, open("catalog.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False); open("catalog.json", "a").write("\n")
    write_root(cat)

def write_readme(d, e):
    L = [f"# {e['title']}", "", f"> {e['tagline']}", "", "## At a glance", "", "| | |", "|---|---|",
         f"| For | {e['persona']} |", f"| Language | {'Italian' if e['language']=='it' else 'English'} |",
         f"| Workflows | {len(e['workflows'])} {'alternative editions' if e.get('alternatives') else 'workflows'}, {e['total_nodes']} nodes{' each' if e.get('alternatives') else ''} (sticky notes excluded) |",
         f"| Credentials you need | {', '.join('`'+c+'`' for c in e['credentials']) or 'none'} |",
         f"| License | MIT |", "", "## What it does", "", e["description"], "", "## Files", "",
         "| File | Nodes | Triggers |", "|---|---|---|"]
    for w in e["workflows"]:
        L.append(f"| [`{w['file']}`]({w['file']}) | {w['nodes']} | {', '.join(w['triggers']) or 'called manually'} |")
    sheets = sorted(glob.glob(d + "/sheets/*.csv"))
    if sheets:
        L += ["", "## Google Sheet templates", "", "Create a spreadsheet with one tab per file and paste the headers into row 1:", ""]
        L += [f"- [`{os.path.basename(s)}`](sheets/{os.path.basename(s)})" for s in sheets]
    for x in e.get("extra_docs", []):
        L += ["", f"## {x['label']}", "", f"[{x['file']}]({x['file']})"]
    L += ["", "## Diagram", "", "Generated from the workflow JSON. Green = triggers, purple = AI, blue = HTTP, teal = sheets and data, amber = messaging and waits, red = error handling.", ""]
    for w in e["workflows"]:
        L += [f"**{w['file']}** (click to open full size)", "", f"[![{w['file']}]({w['diagram']})]({w['diagram']})", ""]
    L += ["", "## Patterns demonstrated", ""] + [f"- {p}" for p in e["patterns"]]
    L += ["", "## Setup", "",
          "1. In n8n choose **Workflows → Import from file** and pick the JSON above.",
          "2. Every credential id in the file is a placeholder (`*_CREDENTIAL_ID` or `YOUR_*`). Open each node showing a credential warning and select your own credential.",
          "3. Replace placeholder values such as `YOUR-SITE.com`, sheet names and webhook URLs with your own.",
          "4. Run once manually with test data before activating.", "",
          "No credentials, tokens or instance data are included. CI fails any change that adds them (`scripts/validate.py`).", ""]
    open(d + "/README.md", "w", encoding="utf-8").write("\n".join(L))

def write_root(cat):
    n = sum(e["total_nodes"] for e in cat)
    L = ["# n8n workflows", "",
         "Production-style n8n workflow templates I designed and built, published as open source (MIT).",
         "Each one is a complete, importable workflow with the integrations, triggers and human-approval or fallback logic spelled out.", "",
         f"**{len(cat)} templates, {sum(len(e['workflows']) for e in cat)} workflows, {n} nodes.** The table is generated from the workflow files by `scripts/build_catalog.py`.", "",
         "| | Template | For | Workflows | Nodes | Patterns |", "|---|---|---|---|---|---|"]
    for e in cat:
        thumb = f"templates/{e['slug']}/{sorted(e['workflows'], key=lambda w: 'followup' in w['diagram'])[0]['diagram']}"
        L.append(f"| <a href=\"templates/{e['slug']}\"><img src=\"{thumb}\" width=\"160\" alt=\"{e['title']} diagram\"></a> | [{e['title']}](templates/{e['slug']}) | {e['persona']} | {len(e['workflows'])} | {e['total_nodes']} | {', '.join(e['patterns'])} |")
    L += ["", "## How these are built", "",
          "- [Design principles](docs/design-principles.md): error handling, credential hygiene, human-in-the-loop, node budget.",
          "- No instance data ships. `scripts/sanitize.py` strips ids, `pinData` and personal emails from an export; `scripts/validate.py` runs in CI and fails on leaked credential ids, emails, tokens or Google Sheet/Drive ids.",
          "- Catalog, node counts and per-template READMEs are generated from the JSON, so they cannot drift.", "",
          "## Use", "", "Import any `workflow*.json` through **Workflows → Import from file** in n8n, then attach your own credentials. See each template's README.", "",
          "## Related", "",
          "- [n8n-flow-bridge-mcp](https://github.com/dorkian/n8n-flow-bridge-mcp): bridge dev and production n8n flows.",
          "- [n8n-Fan-Engine](https://github.com/dorkian/n8n-Fan-Engine): event-driven AI sports reactions.", "",
          "## License", "", "MIT. See [LICENSE](LICENSE).", ""]
    open("README.md", "w", encoding="utf-8").write("\n".join(L))

if __name__ == "__main__":
    build()
