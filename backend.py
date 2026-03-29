import pandas as pd

DATA_URL = "https://www.england.nhs.uk/wp-content/uploads/2026/03/nhs-oversight-framework-acute-trust-data-q3-25-26.csv"

QUARTERS = ["Q1 2025/26", "Q2 2025/26", "Q3 2025/26"]


def load_raw_data() -> pd.DataFrame:
    """Fetch raw data from NHS England."""
    return pd.read_csv(DATA_URL)


def get_average_metric_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to 'Average metric score' rows for Q1-Q3 2025/26.

    Returns columns: Quarter, Region, Trust_code, Trust_name, Value, Rank
    """
    mask = (
        (df["Metric_description"] == "Average metric score")
        & (df["Quarter"].isin(QUARTERS))
    )
    cols = ["Quarter", "Region", "Trust_code", "Trust_name", "Value", "Rank"]
    scores = df.loc[mask, cols].copy()
    scores["Score"] = pd.to_numeric(scores["Value"], errors="coerce")
    scores.drop(columns=["Value"])
    scores["Rank"] = pd.to_numeric(scores["Rank"], errors="coerce")
    return scores


def get_trend_table(scores: pd.DataFrame) -> pd.DataFrame:
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

    # Interleave Score + Rank columns per quarter
    quarter_cols = []
    for q in QUARTERS:
        score_col = f"{q} Score"
        rank_col = f"{q} Rank"
        if score_col not in pivot.columns:
            pivot[score_col] = None
        if rank_col not in pivot.columns:
            pivot[rank_col] = None
        quarter_cols += [score_col, rank_col]

    # Sort by most recent quarter rank
    sort_cols = [f"{q} Rank" for q in reversed(QUARTERS) if f"{q} Rank" in pivot.columns]
    pivot = pivot.sort_values(sort_cols, na_position="last").reset_index(drop=True)

    return pivot[["Trust_name"] + quarter_cols]


def get_trust_score_trend(scores: pd.DataFrame, trust_codes: list[str]) -> pd.DataFrame:
    """
    Long-format rank + score data for selected trusts, ordered for charting.

    Columns: Trust_code, Trust_name, Quarter, Value, Rank
    """
    quarter_order = {q: i for i, q in enumerate(QUARTERS)}
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
        - quarters:     available quarter labels present in data
    """
    raw = load_raw_data()
    scores = get_average_metric_scores(raw)
    trend_table = get_trend_table(scores)
    all_trusts = get_all_trusts(scores)
    quarters = [q for q in QUARTERS if q in scores["Quarter"].unique()]

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
