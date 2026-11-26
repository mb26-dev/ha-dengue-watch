"""Tests for the dengue surveillance parser and statistics (no Home Assistant needed)."""

import importlib.util
import pathlib
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("surveillance", ROOT / "custom_components/dengue_watch/surveillance.py")
sv = importlib.util.module_from_spec(spec)
sys.modules["surveillance"] = sv
spec.loader.exec_module(sv)

FIXTURE = (ROOT / "tests/fixtures/krabi_2026-11-26.csv").read_text(encoding="utf-8")
PHUKET = (ROOT / "tests/fixtures/phuket_2026-11-26.csv").read_text(encoding="utf-8")


def test_epi_weeks():
    # DDC: week 48 of 2026 runs 22 - 28 November
    assert sv.epi_week(date(2026, 11, 22)) == (2026, 48)
    assert sv.epi_week(date(2026, 11, 28)) == (2026, 48)
    assert sv.epi_week(date(2026, 11, 29)) == (2026, 49)
    assert sv.week_start(2026, 48) == date(2026, 11, 22)
    # weeks restart on 1 January: 1 - 3 January 2026 are week 1, from Sunday 4 January week 2
    assert sv.epi_week(date(2026, 1, 3)) == (2026, 1)
    assert sv.epi_week(date(2026, 1, 4)) == (2026, 2)
    assert sv.epi_week(date(2025, 12, 31)) == (2025, 53)
    assert sv.weeks_in_year(2025) == 53
    assert sv.week_start(2026, 1) == date(2026, 1, 1)


def test_parse():
    s = sv.parse_csv(FIXTURE)
    assert sorted(s) == [2564, 2565, 2566, 2567, 2568, 2569]
    assert sum(s[2569].values()) == 315  # matches the DDS dashboard for Krabi
    assert 48 not in s[2569]  # running week has no value yet
    assert s[2568][52] == 3


def test_parse_quoted_thousands_and_labelled_year():
    text = 'Measure Names,สัปดาห์,Measure Values,ผู้ป่วย\nปี พ.ศ.2567,1,"1,891",\nปี พ.ศ. 2569,1,,"2,005"\n'
    s = sv.parse_csv(text)
    assert s[2567][1] == 1891 and s[2569][1] == 2005


def test_phuket_is_high():
    s = sv.parse_csv(PHUKET)
    assert sum(s[2569].values()) == 1834
    assert s[2567][1] == 216
    st = sv.evaluate(s, date(2026, 11, 26))
    assert st.last_week == (2026, 47)
    assert st.cases_window == 34 + 45 + 56 + 51
    assert st.level == sv.LEVEL_HIGH, (st.level, st.cases_window, st.expected_window)


def test_parse_rejects_other_tables():
    try:
        sv.parse_csv("วัน/สถานที่\nตามวันและสถานที่เริ่มป่วย\n")
    except sv.SurveillanceParseError:
        return
    raise AssertionError("expected SurveillanceParseError")


def test_evaluate_krabi():
    st = sv.evaluate(sv.parse_csv(FIXTURE), date(2026, 11, 26))
    assert st.last_week == (2026, 47)
    assert [p.week for p in st.weeks[-4:]] == [44, 45, 46, 47]
    assert st.cases_window == 8 + 12 + 2 + 6
    # medians of weeks 44-47 over 2021-2025
    assert [p.median for p in st.weeks[-4:]] == [7.0, 8.0, 8.0, 3.0]
    assert st.expected_window == 26.0
    assert st.trend == "falling"
    assert st.level == sv.LEVEL_NORMAL
    assert st.cases_year == 315
    assert st.baseline_years == [2021, 2022, 2023, 2024, 2025]
    assert st.cases_year_last == sum(sv.parse_csv(FIXTURE)[2568][w] for w in range(1, 48))


def test_lagging_export_steps_back():
    s = sv.parse_csv(FIXTURE)
    del s[2569][47]
    st = sv.evaluate(s, date(2026, 11, 26))
    assert st.last_week == (2026, 46)


def test_classify():
    assert sv.classify(3, 2)[0] == sv.LEVEL_NORMAL  # within the small-number margin
    assert sv.classify(6, 2)[0] == sv.LEVEL_ELEVATED
    assert sv.classify(25, 10)[0] == sv.LEVEL_HIGH
    assert sv.classify(9, 3)[0] == sv.LEVEL_ELEVATED  # high needs at least 10 cases
    assert sv.classify(5, 37)[0] == sv.LEVEL_LOW
    assert sv.classify(0, 1)[0] == sv.LEVEL_NORMAL


def test_year_start_window_crosses_years():
    s = sv.parse_csv(FIXTURE)
    # pretend it is mid-January 2027 (BE 2570) with two weeks reported
    s[2570] = {1: 4, 2: 6}
    st = sv.evaluate(s, date(2027, 1, 20))
    assert st.last_week == (2027, 2)
    assert [(p.year, p.week) for p in st.weeks[-4:]] == [(2026, 52), (2026, 53), (2027, 1), (2027, 2)]


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok  ", name)
            except AssertionError as err:
                fails += 1
                print("FAIL", name, err)
    sys.exit(1 if fails else 0)
