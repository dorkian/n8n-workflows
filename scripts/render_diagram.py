#!/usr/bin/env python3
"""Render an n8n workflow JSON to a standalone SVG diagram (nodes, connections,
node-type colours). Deterministic: same JSON in, same SVG out."""
import json, re, sys
from html import escape

W, H = 168, 48
MAX_W = 2400  # cap on rendered width in px; viewBox keeps it crisp at any zoom
COLORS = [  # (regex on node type or name, fill, label)
    (r"(?i)error|alert|guard|failed", "#fde8e8", "#b42318"),
    (r"(?i)trigger|webhook|schedule", "#e3f6e8", "#1a7f37"),
    (r"(?i)openai|anthropic|langchain|agent|claude|gpt|llm", "#efe7fb", "#6f42c1"),
    (r"(?i)httprequest", "#e4f0fd", "#0969da"),
    (r"(?i)googlesheets|sheet|airtable|postgres|mysql", "#e0f5f2", "#0f766e"),
    (r"(?i)gmail|slack|telegram|twilio|email|wait", "#fff1d6", "#9a6700"),
]


def style(node):
    key = node["type"] + " " + node["name"]
    for pat, fill, stroke in COLORS:
        if re.search(pat, key):
            return fill, stroke
    return "#f1f3f5", "#57606a"


def wrap(text, width=22):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines[:2] if len(lines) <= 2 else [lines[0], lines[1][: width - 1] + "…"]


def render(wf: dict) -> str:
    nodes = [n for n in wf["nodes"] if "stickyNote" not in n["type"]]
    if not nodes:
        return ""
    pos = {n["name"]: n["position"] for n in nodes}
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    pad = 30
    x0, y0 = min(xs) - pad, min(ys) - pad
    vw, vh = max(xs) - min(xs) + W + 2 * pad, max(ys) - min(ys) + H + 2 * pad
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {vw} {vh}" width="{min(vw, MAX_W)}" height="{round(min(vw, MAX_W) * vh / vw)}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
           f'<rect x="{x0}" y="{y0}" width="{vw}" height="{vh}" fill="#ffffff"/>']
    for src, outs in sorted(wf.get("connections", {}).items()):
        if src not in pos:
            continue
        for branch in outs.get("main", []):
            for link in branch or []:
                dst = link["node"]
                if dst not in pos:
                    continue
                sx, sy = pos[src][0] + W, pos[src][1] + H / 2
                dx, dy = pos[dst][0], pos[dst][1] + H / 2
                c = max(40, abs(dx - sx) / 2)
                err = re.search(COLORS[0][0], dst)
                look = 'stroke="#e5a5a5" stroke-width="1.2" stroke-dasharray="5 4"' if err else 'stroke="#8c959f" stroke-width="1.6"'
                out.append(f'<path d="M{sx} {sy} C{sx + c} {sy} {dx - c} {dy} {dx} {dy}" fill="none" {look}/>')
                out.append(f'<circle cx="{dx}" cy="{dy}" r="3" fill="#8c959f"/>')
    for n in nodes:
        x, y = pos[n["name"]]; fill, stroke = style(n)
        out.append(f'<rect x="{x}" y="{y}" width="{W}" height="{H}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
        lines = wrap(n["name"])
        base = y + H / 2 - (len(lines) - 1) * 7 + 4
        for i, ln in enumerate(lines):
            out.append(f'<text x="{x + W / 2}" y="{base + i * 14}" text-anchor="middle" font-size="12" fill="#1f2328">{escape(ln)}</text>')
    out.append("</svg>\n")
    return "\n".join(out)


if __name__ == "__main__":
    wf = json.load(open(sys.argv[1], encoding="utf-8"))
    open(sys.argv[2], "w", encoding="utf-8").write(render(wf))
