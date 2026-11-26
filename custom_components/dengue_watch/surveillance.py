"""Parsing and statistics for the DDC dengue surveillance export (Report 506 / DDS).

Pure Python without Home Assistant imports, so it can be tested on its own.

The CSV export of the DDS dashboard "Disease situation" (line chart sheet) lists the
weekly number of cases per epidemiological week. The five years before carry their
Buddhist Era year in the first column; the rows of the current year have no year
("# ลักษณะจำนวน (copy)"). Each row has its value in one of the value columns:

    Measure Names,สัปดาห์,# ลักษณะจำนวน (copy),Measure Values
    # ลักษณะจำนวน (copy),1,5,
    ปี พ.ศ. 2568,1,,2

A labelled current year ("ปี พ.ศ. 2569") is understood as well.
Years are Buddhist Era (CE + 543).
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from math import sqrt
from statistics import median

BE_OFFSET = 543
WINDOW_WEEKS = 4

LEVEL_LOW = "low"
LEVEL_NORMAL = "normal"
LEVEL_ELEVATED = "elevated"
LEVEL_HIGH = "high"
LEVELS = [LEVEL_LOW, LEVEL_NORMAL, LEVEL_ELEVATED, LEVEL_HIGH]

_YEAR_RE = re.compile(r"(25\d\d)")


class SurveillanceParseError(ValueError):
    """The export does not look like the expected weekly table."""


def _num(text: str) -> float | None:
    text = (text or "").replace(",", "").replace('"', "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_csv(text: str) -> dict[int, dict[int, float]]:
    """Return {buddhist_year: {epi_week: cases}}; weeks without a value are left out."""
    text = text.lstrip("﻿")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or len(rows[0]) < 3 or "สัปดาห์" not in rows[0][1]:
        raise SurveillanceParseError("unexpected header: " + (",".join(rows[0]) if rows else "empty"))
    series: dict[int, dict[int, float]] = {}
    current: dict[int, float] = {}
    for row in rows[1:]:
        if len(row) < 3:
            continue
        week = _num(row[1])
        if week is None:
            continue
        values = [_num(v) for v in row[2:]]
        value = next((v for v in values if v is not None), None)
        m = _YEAR_RE.search(row[0])
        if m:
            target = series.setdefault(int(m.group(1)), {})
        elif row[0].strip():
            target = current
        else:
            continue
        if value is not None:
            target[int(week)] = value
    if current:
        series[(max(series) + 1) if series else 0] = current
    if not series or 0 in series:
        raise SurveillanceParseError("no weekly values in the export")
    return series


# ---------- epidemiological weeks ----------
# The DDS dashboard counts weeks like Tableau: weeks run Sunday to Saturday and restart on
# 1 January, so week 1 and the last week (53, rarely 54) of a year can be short.

def _offset(year: int) -> int:
    return (date(year, 1, 1).weekday() + 1) % 7  # days of the Sunday-week before 1 January


def epi_week(day: date) -> tuple[int, int]:
    """(year CE, week) of the day."""
    return day.year, (day.timetuple().tm_yday - 1 + _offset(day.year)) // 7 + 1


def weeks_in_year(year: int) -> int:
    return epi_week(date(year, 12, 31))[1]


def week_start(year: int, week: int) -> date:
    """First day of the week inside the year (1 January for week 1)."""
    d = date(year, 1, 1) + timedelta(days=7 * (week - 1) - _offset(year))
    return max(d, date(year, 1, 1))


def _shift(year: int, week: int, delta: int) -> tuple[int, int]:
    """Move delta weeks (negative = back), across year ends."""
    for _ in range(abs(delta)):
        if delta < 0:
            year, week = (year, week - 1) if week > 1 else (year - 1, weeks_in_year(year - 1))
        else:
            year, week = (year, week + 1) if week < weeks_in_year(year) else (year + 1, 1)
    return year, week


# ---------- statistics ----------

@dataclass
class WeekPoint:
    year: int  # CE
    week: int
    cases: float | None
    median: float | None


@dataclass
class DengueStatus:
    level: str
    cases_window: float  # last WINDOW_WEEKS complete weeks
    expected_window: float  # sum of the 5-year weekly medians over the same weeks
    ratio: float | None
    cases_year: float  # current year so far
    cases_year_last: float | None  # same weeks of the previous year
    last_week: tuple[int, int]  # (year CE, week) of the newest complete week
    trend: str  # rising / falling / steady
    weeks: list[WeekPoint] = field(default_factory=list)  # last 12 weeks, oldest first
    baseline_years: list[int] = field(default_factory=list)  # CE years used for the median


def classify(cases: float, expected: float) -> tuple[str, float | None]:
    """Level of the recent cases against the 5-year median of the same weeks.

    Case counts scatter by about the square root of their size, so a level needs more than
    that noise: elevated means more than the median plus twice its square root (at least
    3 cases more), high more than twice the median, at least 10 cases and clearly outside
    the noise as well.
    """
    ratio = cases / expected if expected > 0 else None
    noise = max(3.0, 2 * sqrt(expected))
    if cases >= 10 and cases > 2 * expected and cases > expected + 1.5 * noise:
        return LEVEL_HIGH, ratio
    if cases > expected + noise:
        return LEVEL_ELEVATED, ratio
    if expected >= 4 and cases < 0.5 * expected:
        return LEVEL_LOW, ratio
    return LEVEL_NORMAL, ratio


def is_dense(series: dict[int, dict[int, float]], today: date) -> bool:
    """True when the current year reports a value in most weeks (dengue in most provinces).

    Sparse series (malaria, Zika, small provinces) leave out the weeks without cases, so
    a missing week there means zero, not "not reported yet".
    """
    cur_year, cur_week = epi_week(today)
    values = series.get(cur_year + BE_OFFSET, {})
    return cur_week > 3 and len(values) >= 0.7 * (cur_week - 2)


def newest_week(series: dict[int, dict[int, float]], today: date) -> tuple[int, int]:
    """Newest complete week with a value; the export may lag up to 2 weeks."""
    cur_year, cur_week = epi_week(today)
    last = _shift(cur_year, cur_week, -1)
    for _ in range(2):
        if series.get(last[0] + BE_OFFSET, {}).get(last[1]) is not None:
            break
        last = _shift(last[0], last[1], -1)
    return last


def evaluate(series: dict[int, dict[int, float]], today: date,
             last: tuple[int, int] | None = None) -> DengueStatus:
    """Compare the newest complete weeks with the median of the five years before.

    last: newest reported week to use (from a dense series of the same export date);
    by default it is found in this series, or taken as last week for sparse series.
    """
    cur_year, cur_week = epi_week(today)
    cur_be = cur_year + BE_OFFSET
    if last is None:
        last = newest_week(series, today) if is_dense(series, today) else _shift(cur_year, cur_week, -1)

    baseline_be = sorted(y for y in series if y < cur_be)[-5:]

    def cases_at(y: int, w: int) -> float | None:
        # weeks without cases are left out of the export: a week of a listed year is 0
        if y + BE_OFFSET not in series and not (y == cur_year and series):
            return None
        return series.get(y + BE_OFFSET, {}).get(w, 0.0)

    def median_at(y: int, w: int) -> float | None:
        # the same week number in each of the five years before year y
        vals = []
        for i in range(1, 6):
            yb = y + BE_OFFSET - i
            if yb in series:
                weeks_then = weeks_in_year(yb - BE_OFFSET)
                vals.append(series[yb].get(min(w, weeks_then), 0.0))
        return float(median(vals)) if vals else None

    weeks: list[WeekPoint] = []
    for back in range(11, -1, -1):
        y, w = _shift(last[0], last[1], -back)
        weeks.append(WeekPoint(y, w, cases_at(y, w), median_at(y, w)))

    window = weeks[-WINDOW_WEEKS:]
    cases_window = sum(p.cases or 0 for p in window)
    expected_window = sum(p.median or 0 for p in window)
    level, ratio = classify(cases_window, expected_window)

    year_vals = series.get(cur_be, {})
    cases_year = sum(year_vals.values())
    prev = series.get(cur_be - 1)
    cases_year_last = None
    if prev is not None and last[0] == cur_year:
        cases_year_last = sum(v for w, v in prev.items() if w <= last[1])

    recent2 = sum(p.cases or 0 for p in weeks[-2:])
    before2 = sum(p.cases or 0 for p in weeks[-4:-2])
    if recent2 > before2 * 1.3 + 2:
        trend = "rising"
    elif recent2 < before2 * 0.7 - 2:
        trend = "falling"
    else:
        trend = "steady"

    return DengueStatus(
        level=level,
        cases_window=cases_window,
        expected_window=round(expected_window, 1),
        ratio=round(ratio, 2) if ratio is not None else None,
        cases_year=cases_year,
        cases_year_last=cases_year_last,
        last_week=last,
        trend=trend,
        weeks=weeks,
        baseline_years=[y - BE_OFFSET for y in baseline_be],
    )
