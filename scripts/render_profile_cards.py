#!/usr/bin/env python3
"""Render animated SVG profile cards. Set STATIC=1 to freeze the final frame."""
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
OWNER = "Sudhanshu-Patil"
ACCENT, INK, SURFACE, FG, MUTED, LINE = "#bfe36b", "#0b0c0e", "#131418", "#ecedee", "#9a9da4", "#292b30"
FEATURED = [
    ("MediClaim", "Agentic RAG for insurance claims adjudication", "Hybrid + graph retrieval, QLoRA and human review.", f"https://github.com/{OWNER}/MediClaim", "PYTHON · AI / RAG"),
    ("Waypoint", "An AI travel concierge that plans and adapts", "Verified travel plans, honest pricing and in-trip alerts.", "https://itinerary-concierge.onrender.com/", "AI · TRAVEL"),
    ("Cedar Lane", "Voice AI receptionist that books real appointments", "Voice, calendar tools and reliable human handoff.", f"https://github.com/{OWNER}/Cedar-Lane-Receptionist", "TYPESCRIPT · VOICE AI"),
    ("Redline", "Deterministic diffs for engineering drawings", "Compare revisions, then answer with cited, grounded chat.", f"https://github.com/{OWNER}/Redline", "PYTHON · DOCUMENT AI"),
    ("Telecom Triage", "Confidence-gated AI for customer operations", "Automate clear requests; route uncertain cases to people.", f"https://github.com/{OWNER}/telecom-request-workflow", "PYTHON · AGENTS"),
    ("AI Email Reply", "Grounded email drafts with a quality metric", "Evaluate grounding, intent, similarity, style and sendability.", f"https://github.com/{OWNER}/AI-Email-Reply", "PYTHON · EVALUATION"),
    ("Glance", "An open-source AI assistant for any portfolio", "A playful, zero-dependency chat widget for the web.", f"https://github.com/{OWNER}/glance-chat", "JAVASCRIPT · OPEN SOURCE"),
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def font_subset(characters: str) -> str:
    """Fetch Geist's Latin subset, pyftsubset it, and embed it as a base64 WOFF."""
    url = "https://fonts.googleapis.com/css2?family=Geist:wght@100..900&display=swap"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    css = urllib.request.urlopen(request, timeout=30).read().decode("utf-8")
    latin = re.search(r"/\* latin \*/\s*@font-face\s*\{([^}]+)\}", css, re.S)
    source_block = latin.group(1) if latin else css
    match = re.search(r"url\((https://[^)]+\.woff2?)\)", source_block)
    if not match:
        raise RuntimeError("Google Fonts did not return a Geist Latin WOFF/WOFF2 URL")
    request = urllib.request.Request(match.group(1), headers={"User-Agent": "Mozilla/5.0"})
    font_bytes = urllib.request.urlopen(request, timeout=30).read()
    with tempfile.TemporaryDirectory() as temp:
        source = Path(temp) / "geist.woff2"
        target = Path(temp) / "geist-subset.woff"
        source.write_bytes(font_bytes)
        subprocess.run([
            "pyftsubset", str(source), f"--output-file={target}", "--flavor=woff",
            "--layout-features=*", "--name-IDs=0,1,2,4,6", "--name-languages=0x409",
            f"--text={characters}",
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return base64.b64encode(target.read_bytes()).decode("ascii")


def load_days() -> list[dict]:
    if not DATA.exists():
        return []
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        raw_days = payload
    else:
        raw_days = payload.get("contributionDays", [])
        if not raw_days:
            raw_days = [day for week in payload.get("weeks", []) for day in week.get("contributionDays", [])]
    result = []
    for item in raw_days:
        try:
            result.append({"date": dt.date.fromisoformat(item["date"]), "count": int(item.get("contributionCount", item.get("count", 0)))})
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(result, key=lambda day: day["date"])


def start_svg(width: int, height: int, font_data: str, delay: float = 0) -> str:
    css = "" if STATIC else f"""
      .reveal {{ animation: rise .75s cubic-bezier(.16,1,.3,1) {delay:.2f}s both; }}
      @keyframes rise {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
      .pulse {{ animation: glow 2.8s ease-in-out {delay:.2f}s infinite; }}
      @keyframes glow {{ 0%,100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}
      @media (prefers-reduced-motion: reduce) {{ .reveal, .pulse {{ animation: none !important; }} .smil {{ display: none; }} }}
    """
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
      <title>Sudhanshu Patil — AI Engineer profile card</title>
      <style>
        @font-face {{ font-family: Geist; src: url(data:font/woff;base64,{font_data}) format('woff'); font-weight: 100 900; }}
        text {{ font-family: Geist, Arial, sans-serif; }}
        .card {{ fill: {SURFACE}; stroke: {LINE}; stroke-width: 1; }}
        {css}
      </style>
      <rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="20" class="card"/>
      <circle cx="{width-30}" cy="28" r="3" fill="{ACCENT}" class="pulse smil">{'<animate attributeName="opacity" values=".45;1;.45" dur="2.8s" begin="' + f'{delay:.2f}' + 's" repeatCount="indefinite"/>' if not STATIC else ''}</circle>
    '''


def save(name: str, body: str, width: int, height: int, font_data: str, delay: float = 0) -> None:
    (OUT / name).write_text(start_svg(width, height, font_data, delay) + body + "</svg>\n", encoding="utf-8")


def hero(font_data: str) -> None:
    body = f'''<g class="reveal">
      <text x="42" y="46" fill="{ACCENT}" font-size="13" font-weight="600" letter-spacing="2">AI ENGINEER · NAGPUR, INDIA</text>
      <text x="42" y="104" fill="{FG}" font-size="42" font-weight="700">Sudhanshu Patil</text>
      <text x="42" y="138" fill="{MUTED}" font-size="17">Building grounded AI systems — agentic RAG, MCP tooling and voice agents.</text>
      <rect x="42" y="153" width="140" height="1" fill="{ACCENT}"/>
      <text x="200" y="159" fill="{MUTED}" font-size="12">Available for AI Engineer / FDE roles</text>
    </g>'''
    save("hero.svg", body, 960, 184, font_data, 0)


def tiles(font_data: str) -> None:
    choices = [
        ("tile-linkedin.svg", "LinkedIn", "Let's connect", "https://www.linkedin.com/in/sudhpatil"),
        ("tile-work.svg", "Selected work", "Explore my portfolio", "https://sudhanshu-patil.vercel.app/"),
        ("tile-contact.svg", "Get in touch", "sudhanshupatil588@gmail.com", "mailto:sudhanshupatil588@gmail.com"),
    ]
    for i, (filename, heading, subtitle, href) in enumerate(choices):
        body = f'''<a href="{esc(href)}"><g class="reveal">
          <rect x="1" y="1" width="298" height="94" rx="17" fill="{SURFACE}" stroke="{LINE}"/>
          <text x="22" y="40" fill="{FG}" font-size="17" font-weight="650">{esc(heading)}</text>
          <text x="22" y="65" fill="{MUTED}" font-size="12">{esc(subtitle)}</text>
          <text x="269" y="42" fill="{ACCENT}" font-size="19">↗</text>
          <rect x="22" y="80" width="44" height="2" rx="1" fill="{ACCENT}"/>
        </g></a>'''
        save(filename, body, 300, 96, font_data, .55 + i * .2)


def contribution_summary(days: list[dict]) -> tuple[list[tuple[str, int]], int, int, str]:
    today = dt.datetime.now(dt.timezone.utc).date()
    recent = [day for day in days if today - dt.timedelta(days=364) <= day["date"] <= today]
    totals: dict[tuple[int, int], int] = defaultdict(int)
    for day in recent:
        totals[(day["date"].year, day["date"].month)] += day["count"]
    cursor = today.replace(day=1)
    months = []
    for _ in range(12):
        months.append((cursor.strftime("%b"), totals.get((cursor.year, cursor.month), 0)))
        cursor = (cursor - dt.timedelta(days=1)).replace(day=1)
    months.reverse()
    active = {day["date"] for day in recent if day["count"] > 0}
    cursor_day = today if today in active else today - dt.timedelta(days=1)
    streak = 0
    while cursor_day in active:
        streak += 1
        cursor_day -= dt.timedelta(days=1)
    busiest = max(recent, key=lambda day: day["count"], default=None)
    busiest_day = busiest["date"].strftime("%b %-d") if busiest and busiest["count"] else "—"
    return months, len(active), streak, busiest_day


def stats_card(days: list[dict], font_data: str) -> None:
    months, active, streak, busiest = contribution_summary(days)
    maximum = max((value for _, value in months), default=0) or 1
    baseline, chart_height = 194, 90
    bars = []
    for i, (month, value) in enumerate(months):
        x = 48 + i * 66
        height = max(3, round(chart_height * value / maximum))
        y = baseline - height
        bars.append(f'<rect x="{x}" y="{y}" width="40" height="{height}" rx="6" fill="{ACCENT}" opacity="{.38 + .62 * value / maximum:.2f}"/>')
        bars.append(f'<text x="{x+2}" y="218" fill="{MUTED}" font-size="11">{month}</text>')
    body = f'''<g class="reveal">
      <text x="42" y="42" fill="{ACCENT}" font-size="13" font-weight="600" letter-spacing="1.5">CONTRIBUTIONS · LAST 12 MONTHS</text>
      {''.join(bars)}<line x1="42" y1="195" x2="900" y2="195" stroke="{LINE}"/>
      <text x="48" y="259" fill="{FG}" font-size="20" font-weight="650">{streak} days</text><text x="48" y="280" fill="{MUTED}" font-size="12">current streak</text>
      <text x="344" y="259" fill="{FG}" font-size="20" font-weight="650">{active}</text><text x="344" y="280" fill="{MUTED}" font-size="12">active days</text>
      <text x="640" y="259" fill="{FG}" font-size="20" font-weight="650">{esc(busiest)}</text><text x="640" y="280" fill="{MUTED}" font-size="12">busiest day</text>
    </g>'''
    save("contributions.svg", body, 960, 310, font_data, 1.15)


def render_repo_cards(font_data: str) -> None:
    for index, (title, tagline, description, href, stack) in enumerate(FEATURED, start=1):
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        body = f'''<a href="{esc(href)}"><g class="reveal">
          <text x="38" y="42" fill="{ACCENT}" font-size="12" font-weight="600" letter-spacing="1.4">FEATURED PROJECT / {index:02d}</text>
          <text x="38" y="86" fill="{FG}" font-size="28" font-weight="700">{esc(title)}</text>
          <text x="38" y="116" fill="{FG}" font-size="16" font-weight="500">{esc(tagline)}</text>
          <text x="38" y="143" fill="{MUTED}" font-size="13">{esc(description)}</text>
          <text x="885" y="42" fill="{MUTED}" font-size="10" font-weight="600" text-anchor="end" letter-spacing="1">{esc(stack)}</text>
          <text x="886" y="91" fill="{ACCENT}" font-size="23">↗</text><rect x="38" y="158" width="82" height="2" rx="1" fill="{ACCENT}"/>
        </g></a>'''
        save(f"repo-{slug}.svg", body, 960, 178, font_data, 2.0 + index * .48)


def graph_card(days: list[dict], font_data: str) -> None:
    today = dt.datetime.now(dt.timezone.utc).date()
    first_day = today - dt.timedelta(days=364)
    start = first_day - dt.timedelta(days=first_day.weekday())
    counts = {entry["date"]: entry["count"] for entry in days}
    levels = ["#1b1d21", "#26351b", "#3e5b29", "#668c3b", ACCENT]
    cells = []
    x0, y0, size, gap = 48, 80, 11, 4
    date = start
    while date <= today:
        week = (date - start).days // 7
        value = counts.get(date, 0)
        level = 0 if value == 0 else min(4, 1 + int(value >= 2) + int(value >= 5) + int(value >= 10))
        cells.append(f'<rect x="{x0 + week*(size+gap)}" y="{y0 + date.weekday()*(size+gap)}" width="{size}" height="{size}" rx="3" fill="{levels[level]}"/>')
        date += dt.timedelta(days=1)
    month_labels = []
    date = start
    previous_month = None
    while date <= today:
        if date.weekday() == 0 and date.month != previous_month:
            x = x0 + ((date - start).days // 7) * (size + gap)
            month_labels.append(f'<text x="{x}" y="68" fill="{MUTED}" font-size="10">{date.strftime("%b")}</text>')
            previous_month = date.month
        date += dt.timedelta(days=1)
    legend = ''.join(f'<rect x="{770+i*19}" y="194" width="12" height="12" rx="3" fill="{color}"/>' for i, color in enumerate(levels))
    body = f'''<g class="reveal">
      <text x="42" y="42" fill="{ACCENT}" font-size="13" font-weight="600" letter-spacing="1.5">CONTRIBUTION GRAPH</text>
      <text x="45" y="86" fill="{MUTED}" font-size="10">M</text><text x="45" y="116" fill="{MUTED}" font-size="10">W</text><text x="45" y="146" fill="{MUTED}" font-size="10">F</text>
      {''.join(month_labels)}{''.join(cells)}{legend}
      <text x="45" y="216" fill="{MUTED}" font-size="11">Less</text><text x="895" y="216" fill="{MUTED}" font-size="11" text-anchor="end">More</text>
    </g>'''
    save("contribution-graph.svg", body, 960, 238, font_data, 6.0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    days = load_days()
    alphabet = "Sudhanshu Patil AI ENGINEER NAGPUR INDIA Building grounded AI systems agentic RAG MCP tooling voice agents Available for AI Engineer FDE roles LinkedIn Let's connect Selected work Explore my portfolio Get in touch MediClaim Waypoint Cedar Lane Redline Telecom Triage AI Email Reply Glance Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec current streak active days busiest day 0123456789↗·—"
    font_data = font_subset(alphabet)
    hero(font_data)
    tiles(font_data)
    stats_card(days, font_data)
    render_repo_cards(font_data)
    graph_card(days, font_data)
    print(f"Rendered {len(list(OUT.glob('*.svg')))} SVG cards ({'static' if STATIC else 'animated'}).")


if __name__ == "__main__":
    main()
