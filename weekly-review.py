#!/usr/bin/env python3
"""weekly-review.py — scaffold a weekly review note from the week's day files.

Collects the "### Stand Up" section of each day/day-YYYYMMDD.md in the target
week (Mon-Sun) and writes day/week-YYYY-Www.md: the weekly-review template
plus the raw standup notes as source material to distill outcomes from.

Usage:
    ./weekly-review.py                 # current week
    ./weekly-review.py 2026-09-22      # week containing that date
    ./weekly-review.py --stdout        # print instead of writing
    ./weekly-review.py --force         # overwrite an existing week file
"""
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

DAY_DIR = Path(__file__).resolve().parent / "day"

TEMPLATE_SECTIONS = [
    "Outcomes (Impact)",
    "Decisions & Tradeoffs",
    "Risks & Gaps (leadership signal)",
    "Next Week Focus",
    "Insights/Ideas Summary",
]

STANDUP_RE = re.compile(r"^###\s*stand ?up\s*$", re.IGNORECASE)
HEADING_RE = re.compile(r"^#{1,6}\s")
FENCE_RE = re.compile(r"^```")
EMPTY_BULLET_RE = re.compile(r"^[-*]\s*$")


def week_days(anchor: date) -> list[date]:
    monday = anchor - timedelta(days=anchor.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def extract_standup(path: Path) -> list[str]:
    """Stand Up section body, without template cruft (empty fences/bullets)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((i for i, line in enumerate(lines) if STANDUP_RE.match(line)), None)
    if start is None:
        return []
    body = []
    for line in lines[start + 1:]:
        if HEADING_RE.match(line):
            break
        if not FENCE_RE.match(line) and not EMPTY_BULLET_RE.match(line):
            body.append(line)
    cleaned: list[str] = []
    for line in body:  # collapse blank runs, drop leading blanks
        if line.strip() or (cleaned and cleaned[-1].strip()):
            cleaned.append(line)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return cleaned


def main() -> None:
    args = sys.argv[1:]
    to_stdout, force = "--stdout" in args, "--force" in args
    dates = [a for a in args if not a.startswith("--")]
    anchor = datetime.strptime(dates[0], "%Y-%m-%d").date() if dates else date.today()

    days = week_days(anchor)
    iso_year, iso_week, _ = days[0].isocalendar()
    out = DAY_DIR / f"week-{iso_year}-W{iso_week:02d}.md"

    notes = []
    for day in days:
        path = DAY_DIR / f"day-{day:%Y%m%d}.md"
        if path.exists():
            standup = extract_standup(path)
            if standup:
                notes.append((day, standup))

    lines = [f"# Weekly Review: Week {iso_year}-W{iso_week:02d}", ""]
    for section in TEMPLATE_SECTIONS:
        lines += [f"## {section}", "- ", ""]
    lines += ["---", "", "## Standup notes (source material)", ""]
    if notes:
        for day, standup in notes:
            lines += [f"### {day:%a %Y-%m-%d}", *standup, ""]
    else:
        lines.append("_no standup notes found this week_")

    text = "\n".join(lines).rstrip() + "\n"
    if to_stdout:
        print(text, end="")
    elif out.exists() and not force:
        sys.exit(f"error: {out} already exists (use --force to overwrite)")
    else:
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
