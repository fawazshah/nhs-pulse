from datetime import date

import pandas as pd
import requests

_BASE_URL = "https://www.england.nhs.uk/wp-content/uploads"

_Q_MONTHS = {1: ("Apr", "Jun"), 2: ("Jul", "Sep"), 3: ("Oct", "Dec"), 4: ("Jan", "Mar")}


def _sort_key(quarter: str) -> tuple:
    """Parse 'Q3 2025/26' → (2025, 3) for chronological sorting."""
    q, year = quarter.split()
    return (int(year.split("/")[0]), int(q[1:]))


def _format_quarter(quarter: str) -> str:
    """Convert 'Q3 2025/26' → 'Oct-Dec 2025', 'Q4 2025/26' → 'Jan-Mar 2026'."""
    q, year = quarter.split()
    qnum = int(q[1:])
    start_year = int(year.split("/")[0])
    display_year = start_year + 1 if qnum == 4 else start_year
    start_month, end_month = _Q_MONTHS[qnum]
    return f"{start_month}-{end_month} {display_year}"


def _last_completed_quarter(today: date) -> tuple[int, int]:
    """Return (quarter_number, financial_year_start) for the last completed quarter."""
    y, m = today.year, today.month
    # Financial year starts in April. Q1=Apr-Jun, Q2=Jul-Sep, Q3=Oct-Dec, Q4=Jan-Mar
    if m >= 10:               # Oct-Dec → Q2 (Jul-Sep) is complete
        return 2, y
    if m >= 7:                # Jul-Sep → Q1 (Apr-Jun) is complete
        return 1, y
    if m >= 4:                # Apr-Jun → Q4 (Jan-Mar) of prev FY is complete
        return 4, y - 1
    # Jan-Mar → Q3 (Oct-Dec) of current FY is complete
    return 3, y - 1


def _quarter_before(q: int, fy: int) -> tuple[int, int]:
    """Return the quarter before (q, fy)."""
    if q == 1:
        return 4, fy - 1
    return q - 1, fy


def _build_filename(q: int, fy: int) -> str:
    """e.g. q=3, fy=2025 → 'nhs-oversight-framework-acute-trust-data-q3-25-26.csv'"""
    yy_start = fy % 100
    yy_end = (fy + 1) % 100
    return f"nhs-oversight-framework-acute-trust-data-q{q}-{yy_start:02d}-{yy_end:02d}.csv"


def _candidate_urls(q: int, fy: int) -> list[str]:
    """Generate candidate URLs for a given quarter, searching recent months.

    For each month, tries versioned filenames first (v3, v2) then the base name,
    since NHS England sometimes publishes revised versions.
    """
    base = _build_filename(q, fy)
    stem, ext = base.rsplit(".", 1)
    today = date.today()
    urls = []
    y, m = today.year, today.month
    for _ in range(6):
        month_path = f"{_BASE_URL}/{y}/{m:02d}"
        for v in range(2, 1, -1):
            print(f"{month_path}/{stem}-v{v}.{ext}")
            urls.append(f"{month_path}/{stem}-v{v}.{ext}")
        print(f"{month_path}/{base}")
        urls.append(f"{month_path}/{base}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return urls


def _find_data_url() -> str:
    """Search for the latest available CSV, trying the last completed quarter first."""
    q, fy = _last_completed_quarter(date.today())
    for _ in range(2):  # try two quarters
        for url in _candidate_urls(q, fy):
            try:
                resp = requests.head(url, timeout=5, allow_redirects=True)
                if resp.status_code == 200:
                    return url
            except requests.RequestException:
                continue
        q, fy = _quarter_before(q, fy)
    raise RuntimeError("Could not find NHS oversight framework data for recent quarters")


def load_raw_data() -> pd.DataFrame:
    """Fetch raw data from NHS England."""
    url = _find_data_url()
    return pd.read_csv(url)


def get_average_metric_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to 'Average metric score' rows. Includes all quarters present in the file.

    Returns columns: Quarter, Region, Trust_code, Trust_name, Score, Rank
    """
    mask = df["Metric_description"] == "Average metric score"
    cols = ["Quarter", "Region", "Trust_code", "Trust_name", "Value", "Rank"]
    scores = df.loc[mask, cols].copy()
    scores["Score"] = pd.to_numeric(scores["Value"], errors="coerce")
    scores = scores.drop(columns=["Value"])
    scores["Rank"] = pd.to_numeric(scores["Rank"], errors="coerce")
    return scores


def get_sorted_quarters(scores: pd.DataFrame) -> list[str]:
    """Return quarters present in the data, sorted chronologically."""
    return sorted(scores["Quarter"].unique(), key=_sort_key)


def get_trend_table(scores: pd.DataFrame, quarters: list[str]) -> pd.DataFrame:
    """
    Pivot to wide format for the league table grid.

    For each quarter, produces two columns: '<Q> Score' and '<Q> Rank'.
    Sorted by most recent quarter rank ascending (best first).
    """
    rank_pivot = scores.pivot_table(
        index="Trust_name",
        columns="Quarter",
        values="Rank",
        aggfunc="min",
    )
    score_pivot = scores.pivot_table(
        index="Trust_name",
        columns="Quarter",
        values="Score",
        aggfunc="mean",
    )

    rank_pivot.columns = [f"{q} Rank" for q in rank_pivot.columns]
    score_pivot.columns = [f"{q} Score" for q in score_pivot.columns]

    pivot = rank_pivot.join(score_pivot).reset_index()
    pivot.columns.name = None

    quarter_cols = [col for q in quarters for col in (f"{q} Score", f"{q} Rank")]
    sort_cols = [f"{q} Rank" for q in reversed(quarters) if f"{q} Rank" in pivot.columns]
    pivot = pivot.sort_values(sort_cols, na_position="last").reset_index(drop=True)

    return pivot[["Trust_name"] + quarter_cols]


def get_trust_score_trend(scores: pd.DataFrame, trust_codes: list[str], quarters: list[str]) -> pd.DataFrame:
    """
    Long-format rank + score data for selected trusts, ordered for charting.

    Columns: Trust_code, Trust_name, Quarter, Score, Rank
    """
    quarter_order = {q: i for i, q in enumerate(quarters)}
    filtered = scores[scores["Trust_code"].isin(trust_codes)].copy()
    filtered["_order"] = filtered["Quarter"].map(quarter_order)
    return (
        filtered.sort_values(["Trust_code", "_order"])
        .drop(columns="_order")
        .reset_index(drop=True)
    )


def get_all_trusts(scores: pd.DataFrame) -> list[str]:
    """Unique trust names sorted alphabetically."""
    return sorted(scores["Trust_name"].unique().tolist())


def build_dataset() -> dict:
    """
    Main entry point. Returns:
        - scores:       long-format Average metric score rows (with Rank)
        - trend_table:  wide pivot for grid display
        - all_trusts:   unique trust list
        - quarters:     available quarter labels sorted chronologically
    """
    raw = load_raw_data()
    scores = get_average_metric_scores(raw)
    quarters = get_sorted_quarters(scores)
    scores["Quarter"] = scores["Quarter"].map(_format_quarter)
    quarters = [_format_quarter(q) for q in quarters]
    trend_table = get_trend_table(scores, quarters)
    all_trusts = get_all_trusts(scores)

    return {
        "scores": scores,
        "trend_table": trend_table,
        "all_trusts": all_trusts,
        "quarters": quarters,
    }


if __name__ == "__main__":
    print("Loading data...")
    data = build_dataset()

    print(f"\nQuarters found: {data['quarters']}")
    print(f"Total trusts:   {len(data['all_trusts'])}")
    print(f"\nTop 10 trusts by most recent rank:")
    print(data["trend_table"].head(10).to_string(index=False))
