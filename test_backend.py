from backend import _format_quarter


def test_q1():
    assert _format_quarter("Q1 2025/26") == "Apr-Jun 2025"


def test_q2():
    assert _format_quarter("Q2 2025/26") == "Jul-Sep 2025"


def test_q3():
    assert _format_quarter("Q3 2025/26") == "Oct-Dec 2025"


def test_q4():
    assert _format_quarter("Q4 2025/26") == "Jan-Mar 2026"
