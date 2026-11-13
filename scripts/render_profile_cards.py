#!/usr/bin/env python3
"""Render animated, self-contained SVG cards for the profile README.

Usage:
  python scripts/render_profile_cards.py
  STATIC=1 python scripts/render_profile_cards.py
"""
from __future__ import annotations

import base64
import datetime as dt
import html
import json
import os
import re
import subprocess
import tempfile
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "cards"
DATA = ROOT / "data" / "contributions.json"
STATIC = os.getenv("STATIC", "0") == "1"
NAME = "Sudhanshu Patil"
ACCENT = "#bfe36b"
INK = "#0b0c0e"
SURFACE = "#131418"
FG = "#ecedee"
MUTED = "#9a9da4"
LINE = "#292b30"

FEATURED = [
    ("MediClaim", "Agentic RAG for insurance claims adjudication", "Hybrid + graph retrieval, QLoRA and human review.", "https://github.com/Sudhanshu-Patil/MediClaim", "PYTHON · AI / RAG"),
    ("Waypoint", "An AI travel concierge that plans and adapts", "Verified travel plans, honest pricing and in-trip alerts.", "https://itinerary-concierge.onrender.com/", "AI · TRAVEL"),
    ("Cedar Lane", "Voice AI receptionist that books real appointments", "Voice, calendar tools and reliable human handoff.", "https://github.com/Sudhanshu-Patil/Cedar-Lane-Receptionist", "TYPESCRIPT · VOICE AI"),
    ("Redline", "Deterministic diffs for engineering drawings", "Compare revisions, then answer with cited, grounded chat.", "https://github.com/Sudhanshu-Patil/Redline", "PYTHON · DOCUMENT AI"),
    ("Telecom Triage", "Confidence-gated AI for customer operations", "Automate clear requests; route uncertain cases to people.", "https://github.com/Sudhanshu-Patil/telecom-request-workflow", "PYTHON · AGENTS"),
    ("AI Email Reply", "Grounded email drafts with a quality metric", "Evaluate grounding, intent, similarity, style and sendability.", "https://github.com/Sudhanshu-Patil/AI-Email-Reply", "PYTHON · EVALUATION"),
    ("Glance", "An open-source AI assistant for any portfolio", "A playful, zero-dependency chat widget for the web.", "https://github.com/Sudhanshu-Patil/glance-chat", "JAVASCRIPT · OPEN SOURCE"),
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def fetch_geist_subset(characters: str) -> str:
    css_url = "https://fonts.googleapis.com/css2?family=Geist:wght@100..900&display=swap"
    req = urllib.request.Request(css_url, headers={"User-Agent": "Mozilla/5.0"})
    css = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    match = re.search(r"url\((https://[^)]+\.woff2?)\)", css)
    if not match:
        raise RuntimeError("Could not find Geist font URL")
    font_req = urllib.request.Request(match.group(1), headers={"User-Agent": "Mozilla/5.0"})
    source = urllib.request.urlopen(font_req, timeout=30).read()
    with tempfile.TemporaryDirectory() as tmp_dir:
        in_path = Path(tmp_dir) / "geist.woff2"
        out_path = Path(tmp_dir) / "geist-subset.woff"
        in_path.write_bytes(source)
        subprocess.run([
            "pyftsubset",
            str(in_path),
            f"--output-file={out_path}",
            "--flavor=woff",
            "--layout-features=*",
            f"--text={characters}",
            "--name-IDs=*,+calt,+liga,+kern",
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return base64.b64encode(out_path.read_bytes()).decode("ascii")


def read_contributions() -> list[dict]:
    if not DATA.exists():
        return []
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    days = payload if isinstance(payload, list) else payload.get("contributionDays", [])
    if not days:
        weeks = payload.get("weeks", []) if isinstance(payload, dict) else []
        days = [day for week in weeks for day in week.get("contributionDays", [])]
    results = []
    for day in days:
        try:
            results.append({
                "date": dt.date.fromisoformat(day["date"]),
                "count": int(day.get("contributionCount", day.get("count", 0))),
            })
        except Exception:
            continue
    return sorted(results, key=lambda item: item["date"])


def svg_start(width: int, height: int, font_data: str) -> str:
    motion = "" if STATIC else """
      .reveal { animation: rise .75s cubic-bezier(.16,1,.3,1) both; }
      @keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      @media (prefers-reduced-motion: reduce) { .reveal { animation: none; } }
    """
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
      <style>
        @font-face {{ font-family: Geist; src: url(data:font/woff;base64,{font_data}) format('woff'); font-weight: 100 900; }}
        text {{ font-family: Geist, Arial, sans-serif; }}
        .card {{ fill: {SURFACE}; stroke: {LINE}; stroke-width: 1; }}
        {motion}
      </style>
      <rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="20" class="card"/>
    '''


def save_card(filename: str, body: str, width: int, height: int, font_data: str) -> None:
    svg = svg_start(width, height, font_data) + body + "</svg>\n"
    (OUT / filename).write_text(svg, encoding="utf-8")


def text(x: int, y: int, value: str, size: int, color: str = FG, weight: int = 400, anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{esc(value)}</text>'


def hero(font_data: str) -> None:
    body = f'''
    <g class="reveal">
      <text x="42" y="46" fill="{ACCENT}" font-size="13" font-weight="600" letter-spacing="2">AI ENGINEER · NAGPUR, INDIA</text>
      <text x="42" y="104" fill="{FG}" font-size="42" font-weight="700">{NAME}</text>
      <text x="42" y="138" fill="{MUTED}" font-size="17">Building grounded AI systems — agentic RAG, MCP tooling and voice agents.</text>
      <rect x="42" y="153" width="140" height="1" fill="{ACCENT}" opacity="0.9"/>
      <text x="200" y="159" fill="{MUTED}" font-size="12">Available for AI Engineer / FDE roles</text>
    </g>
    '''
    save_card("hero.svg", body, 960, 184, font_data)


def tiles(font_data: str) -> None:
    cards = [
        ("tile-linkedin.svg", "LinkedIn", "Let’s connect", "https://www.linkedin.com/in/sudhpatil"),
        ("tile-work.svg", "Selected work", "See my portfolio", "https://sudhanshu-patil.vercel.app/"),
        ("tile-contact.svg", "Get in touch", "sudhanshupatil588@gmail.com", "mailto:sudhanshupatil588@gmail.com"),
    ]
    for filename, title, desc, href in cards:
        body = f'''
        <a href="{esc(href)}" target="_blank">
          <g class="reveal">
            <rect x="1" y="1" width="298" height="94" rx="17" fill="{SURFACE}" stroke="{LINE}"/>
            <text x="22" y="40" fill="{FG}" font-size="17" font-weight="650">{esc(title)}</text>
            <text x="22" y="65" fill="{MUTED}" font-size="12">{esc(desc)}</text>
            <text x="269" y="42" fill="{ACCENT}" font-size="19">↗</text>
            <rect x="22" y="80" width="44" height="2" rx="1" fill="{ACCENT}"/>
          </g>
        </a>
        '''
        save_card(filename, body, 300, 96, font_data)


def contribution_summary(days: list[dict]) -> tuple[int, int, str, list[tuple[str, int]]]:
    today = dt.datetime.now(dt.timezone.utc).date()
    recent = [day for day in days if day["date"] >= today - dt.timedelta(days=364)]
    month_totals: dict[tuple[int, int], int] = defaultdict(int)
    for day in recent:
        month_totals[(day["date"].year, day["date"].month)] += day["count"]
    month_series = []
    cursor = today.replace(day=1)
    for _ in range(12):
        year, month = cursor.year, cursor.month
        month_series.append((cursor.strftime("%b"), month_totals.get((year, month), 0)))
        cursor = (cursor - dt.timedelta(days=1)).replace(day=1)
    month_series.reverse()
    active_days = len({day["date"] for day in recent if day["count"] > 0})
    streak = 0
    current = today
    seen = {day["date"] for day in recent if day["count"] > 0}
    while current in seen:
        streak += 1
        current -= dt.timedelta(days=1)
    busiest = max(recent, key=lambda item: item["count"], default={"date": None, "count": 0})
    busiest_label = busiest["date"].strftime("%b %-d") if busiest.get("date") else "—"
    return active_days, streak, busiest_label, month_series


def stats_card(days: list[dict], font_data: str) -> None:
    active_days, streak, busiest, month_series = contribution_summary(days)
    max_value = max((value for _, value in month_series), default=1) or 1
    left = 48
    gap = 26
    bar_w = 40
    baseline = 194
    chart_h = 90
    bars = []
    for index, (month, value) in enumerate(month_series):
        height = max(8, int(chart_h * value / max_value))
        x = left + index * (bar_w + gap)
        y = baseline - height
        bars.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{height}" rx="6" fill="{ACCENT}" opacity="{0.4 + 0.6 * value / max_value:.2f}"/>')
        bars.append(f'<text x="{x + 4}" y="{baseline + 18}" fill="{MUTED}" font-size="11">{esc(month[:3])}</text>')
    body = f'''
    <g class="reveal">
      <text x="42" y="42" fill="{ACCENT}" font-size="13" font-weight="600" letter-spacing="1.5">CONTRIBUTIONS · LAST 12 MONTHS</text>
      {''.join(bars)}
      <line x1="42" y1="195" x2="900" y2="195" stroke="{LINE}"/>
      <text x="48" y="259" fill="{FG}" font-size="20" font-weight="650">{streak} days</text>
      <text x="48" y="280" fill="{MUTED}" font-size="12">current streak</text>
      <text x="344" y="259" fill="{FG}" font-size="20" font-weight="650">{active_days}</text>
      <text x="344" y="280" fill="{MUTED}" font-size="12">active days</text>
      <text x="640" y="259" fill="{FG}" font-size="20" font-weight="650">{esc(busiest)}</text>
      <text x="640" y="280" fill="{MUTED}" font-size="12">busiest day</text>
    </g>
    '''
    save_card("contributions.svg", body, 960, 310, font_data)


def repo_cards(font_data: str) -> None:
    for idx, repo in enumerate(FEATURED, start=1):
        title, tagline, description, href, stack = repo
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        body = f'''
        <a href="{esc(href)}" target="_blank"><g class="reveal">
          <text x="38" y="42" fill="{ACCENT}" font-size="12" font-weight="600" letter-spacing="1.4">FEATURED PROJECT / {idx:02d}</text>
          <text x="38" y="86" fill="{FG}" font-size="28" font-weight="700">{esc(title)}</text>
          <text x="38" y="116" fill="{FG}" font-size="16" font-weight="500">{esc(tagline)}</text>
          <text x="38" y="143" fill="{MUTED}" font-size="13">{esc(description)}</text>
          <text x="885" y="42" fill="{MUTED}" font-size="10" font-weight="600" text-anchor="end" letter-spacing="1">{esc(stack)}</text>
          <text x="886" y="91" fill="{ACCENT}" font-size="23">↗</text>
          <rect x="38" y="158" width="82" height="2" rx="1" fill="{ACCENT}"/>
        </g></a>
        '''
        save_card(f"repo-{slug}.svg", body, 960, 178, font_data)


def graph_card(days: list[dict], font_data: str) -> None:
    today = dt.datetime.now(dt.timezone.utc).date()
    start = today - dt.timedelta(days=364)
    start = start - dt.timedelta(days=start.weekday())
    by_count = {entry["date"]: entry["count"] for entry in days}
    colors = ["#1b1d21", "#243319", "#3d5f27", "#5d8232", ACCENT]
    cells = []
    x0, y0, cell, gap = 48, 80, 11, 4
    current = start
    while current <= today:
        week = (current - start).days // 7
        weekday = current.weekday()
        x = x0 + week * (cell + gap)
        y = y0 + weekday * (cell + gap)
        val = by_count.get(current, 0)
        color_idx = 0 if val == 0 else min(4, 1 + int(val >= 2) + int(val >= 5) + int(val >= 10))
        cells.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{colors[color_idx]}"/>')
        current += dt.timedelta(days=1)
    legends = []
    x = 760
    for color in colors:
        legends.append(f'<rect x="{x}" y="194" width="12" height="12" rx="3" fill="{color}"/>')
        x += 18
    body = f'''<g class="reveal">
      <text x="42" y="42" fill="{ACCENT}" font-size="13" font-weight="600" letter-spacing="1.5">CONTRIBUTION GRAPH</text>
      {''.join(cells)}
      <text x="45" y="216" fill="{MUTED}" font-size="11">Less</text>
      <text x="895" y="216" fill="{MUTED}" font-size="11" text-anchor="end">More</text>
      {''.join(legends)}
    </g>
    '''
    save_card("contribution-graph.svg", body, 960, 238, font_data)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    days = read_contributions()
    font_text = "Sudhanshu Patil AI ENGINEER NAGPUR INDIA BUILDING GROUNDED AI SYSTEMS agentic RAG MCP tooling and voice agents Available for AI Engineer / FDE roles LinkedIn Selected work Get in touch MediClaim Waypoint Cedar Lane Redline Telecom Triage AI Email Reply Glance Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec " + "0123456789"
    font_data = fetch_geist_subset(font_text)
    hero(font_data)
    tiles(font_data)
    stats_card(days, font_data)
    repo_cards(font_data)
    graph_card(days, font_data)
    print(f"Rendered {len(list(OUT.glob('*.svg')))} SVG cards to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
