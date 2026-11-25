"""Architecture diagram for rag-serverless-aws, drawn as code.

Builds docs/architecture.svg with a hand-tuned layout and the official AWS
icons shipped with the `diagrams` package. Optionally renders a PNG with a
headless Chromium-based browser (Edge or Chrome).

Usage:
    pip install diagrams
    python docs/diagrams/architecture.py            # SVG only
    python docs/diagrams/architecture.py --png      # SVG + PNG
"""

from __future__ import annotations

import base64
import shutil
import subprocess
import sys
from pathlib import Path

import diagrams
from diagrams.aws.compute import Lambda
from diagrams.aws.general import Users
from diagrams.aws.integration import Eventbridge, SimpleQueueServiceSqs
from diagrams.aws.management import Cloudwatch
from diagrams.aws.ml import Bedrock
from diagrams.aws.network import APIGateway
from diagrams.aws.security import Cognito
from diagrams.aws.storage import SimpleStorageServiceS3

DOCS = Path(__file__).resolve().parent.parent
SVG_OUT = DOCS / "architecture.svg"
PNG_OUT = DOCS / "architecture.png"

WIDTH, HEIGHT = 1900, 1160
ICON = 84
FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

UPLOAD = "#1A73E8"
INGEST = "#E8710A"
QUERY = "#1E8E3E"
INK = "#232F3E"
MUTED = "#5F6B7A"

ICON_ROOT = Path(diagrams.__file__).resolve().parent.parent


def icon_data(node_cls) -> str:
    path = ICON_ROOT / node_cls._icon_dir / node_cls._icon
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


# name -> (icon class, x, y, title, subtitle)
NODES = {
    "client": (Users, 120, 500, "Client", "web / CLI"),
    "cognito": (Cognito, 360, 295, "Cognito", "User Pool"),
    "api": (APIGateway, 360, 560, "API Gateway", "REST API"),
    "presign": (Lambda, 620, 360, "presign_handler", "Lambda"),
    "query": (Lambda, 620, 800, "query_handler", "Lambda"),
    "docs": (SimpleStorageServiceS3, 880, 360, "Documents", "S3 bucket"),
    "bus": (Eventbridge, 1120, 360, "EventBridge", "rule"),
    "queue": (SimpleQueueServiceSqs, 1360, 360, "SQS", "ingestion queue"),
    "ingest": (Lambda, 1600, 360, "ingestion_handler", "Lambda"),
    "kb": (Bedrock, 1240, 700, "Knowledge Base", "Bedrock"),
    "llm": (Bedrock, 1240, 905, "Foundation model", "Converse API"),
    "embed": (Bedrock, 1520, 905, "Titan Embeddings", "Text v2"),
    "vectors": (SimpleStorageServiceS3, 1780, 700, "S3 Vectors", "vector index"),
}

# (label, color, points, label position, dashed)
EDGES = [
    ("1. sign in", UPLOAD, [(162, 462), (318, 330)], (220, 390), False),
    ("HTTPS + JWT", INK, [(166, 508), (312, 552)], (232, 482), False),
    ("authorizer", MUTED, [(360, 512), (360, 400)], (360, 440), True),
    ("2. upload URL", UPLOAD, [(406, 540), (574, 384)], (486, 470), False),
    ("3. PUT file (pre-signed URL)", UPLOAD, [(120, 452), (120, 118), (880, 118), (880, 312)], (500, 118), False),
    ("signs", UPLOAD, [(666, 360), (832, 360)], (750, 360), True),
    ("4. Object Created", INGEST, [(928, 360), (1072, 360)], (1000, 300), False),
    ("5. route", INGEST, [(1168, 360), (1312, 360)], (1240, 300), False),
    ("6. poll batch", INGEST, [(1408, 360), (1552, 360)], (1480, 300), False),
    ("7. StartIngestionJob", INGEST, [(1600, 448), (1600, 570), (1240, 570), (1240, 652)], (1420, 570), False),
    ("8. chunk + embed", INGEST, [(1286, 735), (1476, 868)], (1395, 812), False),
    ("9. store vectors", INGEST, [(1288, 700), (1732, 700)], (1545, 700), False),
    ("10. ask question", QUERY, [(406, 588), (574, 774)], (492, 690), False),
    ("11. Retrieve", QUERY, [(666, 790), (1192, 712)], (930, 752), False),
    ("12. Converse", QUERY, [(666, 815), (1192, 898)], (930, 856), False),
]

# (title, color, fill, x, y, w, h, title anchor)
GROUPS = [
    ("Auth & API", "#7B1FA2", "#F7F0FB", 268, 210, 184, 470, "start"),
    ("Async ingestion", INGEST, "#FFF5EB", 1040, 236, 660, 250, "start"),
    ("Amazon Bedrock", "#00796B", "#ECF7F5", 1110, 615, 540, 405, "end"),
]


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def marker_id(color: str) -> str:
    return "arrow-" + color.lstrip("#")


def render() -> str:
    out: list[str] = []
    add = out.append
    add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" font-family="{FONT}">')

    colors = {c for _, c, *_ in EDGES}
    add("<defs>")
    for c in colors:
        add(f'<marker id="{marker_id(c)}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
    add('<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.12"/></filter>')
    add("</defs>")

    add(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#FFFFFF"/>')

    # Title
    add(f'<text x="40" y="58" font-size="36" font-weight="700" fill="{INK}">Serverless RAG on AWS</text>')
    add(f'<text x="40" y="92" font-size="19" fill="{MUTED}">Bedrock Knowledge Bases · S3 Vectors · '
        f'Lambda · EventBridge · SQS · API Gateway · Cognito — no VPC, pay-per-use</text>')

    # AWS Cloud container
    add(f'<rect x="232" y="150" width="1638" height="900" rx="16" fill="#F8FAFC" '
        f'stroke="{INK}" stroke-width="2"/>')
    add(f'<rect x="232" y="150" width="150" height="40" rx="16" fill="{INK}"/>')
    add(f'<rect x="232" y="170" width="150" height="20" fill="{INK}"/>')
    add('<text x="307" y="177" font-size="19" font-weight="700" fill="#FFFFFF" '
        'text-anchor="middle">AWS Cloud</text>')

    # Groups
    for title, color, fill, x, y, w, h, anchor in GROUPS:
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" '
            f'stroke="{color}" stroke-width="2" stroke-dasharray="8 6"/>')
        tx = x + 14 if anchor == "start" else x + w - 14
        add(f'<text x="{tx}" y="{y + 28}" font-size="19" font-weight="700" fill="{color}" '
            f'text-anchor="{anchor}">{esc(title)}</text>')

    # Edges (lines first, labels later so they sit on top)
    for _, color, pts, _, dashed in EDGES:
        d = "M" + " L".join(f"{x},{y}" for x, y in pts)
        dash = ' stroke-dasharray="7 6"' if dashed else ""
        add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="3"{dash} '
            f'stroke-linejoin="round" marker-end="url(#{marker_id(color)})"/>')

    # Nodes
    for cls, x, y, title, sub in NODES.values():
        half = ICON // 2
        add(f'<image href="{icon_data(cls)}" x="{x - half}" y="{y - half}" width="{ICON}" '
            f'height="{ICON}" filter="url(#shadow)"/>')
        add(f'<text x="{x}" y="{y + half + 26}" font-size="20" font-weight="700" fill="{INK}" '
            f'text-anchor="middle">{esc(title)}</text>')
        add(f'<text x="{x}" y="{y + half + 49}" font-size="17" fill="{MUTED}" '
            f'text-anchor="middle">{esc(sub)}</text>')

    # Edge labels as pills
    for label, color, _, (lx, ly), _ in EDGES:
        w = len(label) * 9.6 + 24
        add(f'<rect x="{lx - w / 2:.0f}" y="{ly - 16}" width="{w:.0f}" height="32" rx="16" '
            f'fill="#FFFFFF" stroke="{color}" stroke-width="1.5"/>')
        add(f'<text x="{lx}" y="{ly + 6}" font-size="17" font-weight="700" fill="{color}" '
            f'text-anchor="middle">{esc(label)}</text>')

    # Legend
    ly = 1100
    items = [("Upload", UPLOAD), ("Ingestion (async)", INGEST), ("Query", QUERY)]
    x = 40
    for text, color in items:
        add(f'<line x1="{x}" y1="{ly}" x2="{x + 44}" y2="{ly}" stroke="{color}" stroke-width="4" '
            f'marker-end="url(#{marker_id(color)})"/>')
        add(f'<text x="{x + 56}" y="{ly + 7}" font-size="19" fill="{INK}">{esc(text)}</text>')
        x += 90 + len(text) * 10.5
    add(f'<image href="{icon_data(Cloudwatch)}" x="{x + 20}" y="{ly - 22}" width="44" height="44"/>')
    add(f'<text x="{x + 76}" y="{ly + 7}" font-size="19" fill="{INK}">'
        f'All Lambdas log to CloudWatch Logs · each one has its own least-privilege IAM role</text>')

    add("</svg>")
    return "\n".join(out)


def find_browser() -> str | None:
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return shutil.which("chromium") or shutil.which("google-chrome")


def render_png() -> None:
    browser = find_browser()
    if not browser:
        sys.exit("No Chromium-based browser found to render the PNG.")
    subprocess.run(
        [browser, "--headless", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=2", f"--window-size={WIDTH},{HEIGHT}",
         f"--screenshot={PNG_OUT}", SVG_OUT.as_uri()],
        check=True, capture_output=True,
    )


if __name__ == "__main__":
    SVG_OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {SVG_OUT}")
    if "--png" in sys.argv:
        render_png()
        print(f"wrote {PNG_OUT}")
