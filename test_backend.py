from datetime import date

from backend import (
    _build_filename,
    _format_quarter,
    _last_completed_quarter,
    _quarter_before,
    _sort_key,
)


def test_format_quarter_formats_q1():
    assert _format_quarter("Q1 2025/26") == "Apr-Jun 2025"


def test_format_quarter_formats_q2():
    assert _format_quarter("Q2 2025/26") == "Jul-Sep 2025"


def test_format_quarter_formats_q3():
    assert _format_quarter("Q3 2025/26") == "Oct-Dec 2025"


def test_format_quarter_formats_q4():
    assert _format_quarter("Q4 2025/26") == "Jan-Mar 2026"


# _sort_key tests

def test_sort_key_ordering():
    quarters = ["Q3 2025/26", "Q1 2025/26", "Q4 2024/25", "Q2 2025/26"]
    assert sorted(quarters, key=_sort_key) == [
        "Q4 2024/25",
        "Q1 2025/26",
        "Q2 2025/26",
        "Q3 2025/26",
    ]


def test_sort_key_values():
    assert _sort_key("Q1 2025/26") == (2025, 1)
    assert _sort_key("Q4 2024/25") == (2024, 4)


# _last_completed_quarter tests

def test_last_completed_quarter_jan():
    assert _last_completed_quarter(date(2026, 1, 15)) == (3, 2025)


def test_last_completed_quarter_apr():
    assert _last_completed_quarter(date(2026, 4, 10)) == (4, 2025)


def test_last_completed_quarter_jul():
    assert _last_completed_quarter(date(2025, 7, 1)) == (1, 2025)


def test_last_completed_quarter_oct():
    assert _last_completed_quarter(date(2025, 10, 5)) == (2, 2025)


# _quarter_before tests

def test_quarter_before_q3():
    assert _quarter_before(3, 2025) == (2, 2025)


def test_quarter_before_q1_wraps():
    assert _quarter_before(1, 2025) == (4, 2024)


# _build_filename tests

def test_build_filename_q3():
    assert _build_filename(3, 2025) == "nhs-oversight-framework-acute-trust-data-q3-25-26.csv"


def test_build_filename_q1():
    assert _build_filename(1, 2024) == "nhs-oversight-framework-acute-trust-data-q1-24-25.csv"
