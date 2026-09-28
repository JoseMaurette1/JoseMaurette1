"""Render a cropped GitHub contribution graph as light and dark SVGs.

Uses the same public contributions API as the portfolio's calendar, which
includes private contribution counts when the account has them enabled.
"""

import datetime as dt
import html
import json
import sys
import urllib.request
from pathlib import Path

USER = "Jose-Zensah"
START = dt.date(2026, 5, 1)
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"

CELL, GAP, RADIUS = 13, 4, 3
LEFT, TOP, BOTTOM = 34, 44, 30

THEMES = {
    "light": {
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "text": "#57606a",
        "title": "#1f2328",
    },
    "dark": {
        "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "text": "#8b949e",
        "title": "#e6edf3",
    },
}


def fetch_days():
    url = f"https://github-contributions-api.jogruber.de/v4/{USER}?y=all"
    req = urllib.request.Request(url, headers={"User-Agent": "contrib-graph"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    days = {
        dt.date.fromisoformat(day["date"]): (day["level"], day["count"])
        for day in data["contributions"]
    }
    if not days:
        sys.exit(f"No contribution data returned for {USER}.")
    return days


def render(days, theme):
    colors = THEMES[theme]
    today = min(max(days), dt.date.today())
    first_sunday = START - dt.timedelta(days=(START.weekday() + 1) % 7)
    weeks = (today - first_sunday).days // 7 + 1
    step = CELL + GAP
    width = LEFT + weeks * step
    height = TOP + 7 * step + BOTTOM

    total = sum(count for date, (_, count) in days.items() if date >= START)
    headline = f"{total:,} contributions since {START:%B %Y}"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">',
        f'<text x="{LEFT}" y="16" font-size="14" font-weight="600" fill="{colors["title"]}">'
        f'{headline}</text>',
    ]

    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        y = TOP + row * step + CELL - 3
        parts.append(f'<text x="0" y="{y}" font-size="10" fill="{colors["text"]}">{label}</text>')

    last_month = None
    for week in range(weeks):
        week_start = first_sunday + dt.timedelta(weeks=week)
        month_day = next(
            (week_start + dt.timedelta(days=d) for d in range(7)
             if START <= week_start + dt.timedelta(days=d) <= today),
            None,
        )
        if month_day and month_day.month != last_month:
            last_month = month_day.month
            parts.append(
                f'<text x="{LEFT + week * step}" y="{TOP - 8}" font-size="10" '
                f'fill="{colors["text"]}">{month_day:%b}</text>'
            )
        for weekday in range(7):
            date = week_start + dt.timedelta(days=weekday)
            if date < START or date > today:
                continue
            level, count = days.get(date, (0, 0))
            noun = "contribution" if count == 1 else "contributions"
            parts.append(
                f'<rect x="{LEFT + week * step}" y="{TOP + weekday * step}" width="{CELL}" height="{CELL}" '
                f'rx="{RADIUS}" fill="{colors["levels"][level]}">'
                f'<title>{html.escape(f"{count} {noun} on {date:%b %-d, %Y}")}</title></rect>'
            )

    legend_y = TOP + 7 * step + 10
    legend_x = width - 5 * (CELL + 3) - 30
    parts.append(f'<text x="{legend_x - 30}" y="{legend_y + CELL - 3}" font-size="10" fill="{colors["text"]}">Less</text>')
    for i, color in enumerate(colors["levels"]):
        parts.append(f'<rect x="{legend_x + i * (CELL + 3)}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="{RADIUS}" fill="{color}"/>')
    parts.append(f'<text x="{legend_x + 5 * (CELL + 3) + 2}" y="{legend_y + CELL - 3}" font-size="10" fill="{colors["text"]}">More</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    days = fetch_days()
    OUT_DIR.mkdir(exist_ok=True)
    for theme in THEMES:
        (OUT_DIR / f"contributions-{theme}.svg").write_text(render(days, theme))


if __name__ == "__main__":
    main()
