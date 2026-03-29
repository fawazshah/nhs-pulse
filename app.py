import streamlit as st
import plotly.graph_objects as go
from backend import build_dataset

st.set_page_config(page_title="NHS Pulse", page_icon="assets/favicon.png", layout="wide")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading NHS data...")
def load():
    return build_dataset()

data = load()
scores = data["scores"]
trend_table = data["trend_table"]
all_trusts = data["all_trusts"]
quarters = data["quarters"]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown("<h1 style='text-align:center'>NHS Pulse</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='font-size:0.875rem; color:grey; margin:0; text-align:center'>Average metric score rankings for acute trusts.</p>"
    "<p style='font-size:0.875rem; color:grey; margin:0; text-align:center'>NHS quarters follow the April–March financial year: Q1 = Apr–Jun, Q2 = Jul–Sep, Q3 = Oct–Dec, Q4 = Jan-Mar.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Trust selector + ranking comparison
# ---------------------------------------------------------------------------

DEFAULT_TRUSTS = [
    "The Royal Marsden NHS Foundation Trust",
    "Royal Papworth Hospital NHS Foundation Trust",
    "The Christie NHS Foundation Trust",
]

st.subheader("Compare trusts")

selected_names = st.multiselect(
    label="Add / remove trusts",
    options=all_trusts,
    default=[t for t in DEFAULT_TRUSTS if t in all_trusts],
    placeholder="Search for a trust...",
)

selected_codes = scores.loc[
    scores["Trust_name"].isin(selected_names), "Trust_code"
].unique().tolist()

if not selected_names:
    st.info("Select one or more trusts above to see their rank trend.")
else:
    trend_data = scores[scores["Trust_code"].isin(selected_codes)].copy()

    COLOURS = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]
    colour_map = {
        name: COLOURS[i % len(COLOURS)]
        for i, name in enumerate(selected_names)
    }

    # Colour multiselect tags to match chart lines
    tag_css = " ".join(
        f'[data-baseweb="tag"]:nth-of-type({i + 1}) '
        f'{{ background-color: {COLOURS[i % len(COLOURS)]} !important; }}'
        for i in range(len(selected_names))
    )
    st.markdown(f"<style>{tag_css}</style>", unsafe_allow_html=True)

    # Y-axis ticks: every rank if range ≤ 20, otherwise multiples of 5
    visible_ranks = trend_data["Rank"].dropna()
    min_rank = int(visible_ranks.min())
    max_rank = int(visible_ranks.max())
    rank_range = max_rank - min_rank
    step = 1 if rank_range <= 20 else 5
    tick_vals = list(range(min_rank - (min_rank % step or step), max_rank + step, step))
    tick_vals = [v for v in tick_vals if v >= 1]

    fig = go.Figure()

    for name in selected_names:
        trust_df = (
            trend_data[trend_data["Trust_name"] == name]
            .sort_values("Quarter")
        )
        if trust_df.empty:
            continue

        fig.add_trace(go.Scatter(
            x=trust_df["Quarter"],
            y=trust_df["Rank"],
            mode="lines+markers",
            name=name,
            line=dict(color=colour_map[name], width=2),
            marker=dict(size=8),
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "Quarter: %{x}<br>"
                "Rank: %{y}<br>"
                "Score: %{customdata:.2f}"
                "<extra></extra>"
            ),
            customdata=trust_df["Score"],
        ))

    fig.update_layout(
        yaxis=dict(
            title="Rank (lower = better)",
            autorange="reversed",
            tickmode="array",
            tickvals=tick_vals,
            ticktext=[str(v) for v in tick_vals],
        ),
        xaxis=dict(title="Quarter"),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
        ),
        hovermode="x unified",
        height=480,
        margin=dict(l=50, r=200, t=30, b=50),
    )

    st.plotly_chart(fig, width='stretch')

# ---------------------------------------------------------------------------
# League table grid
# ---------------------------------------------------------------------------

st.subheader("League table")

display_cols = {"Trust_name": "Trust"}
for q in quarters:
    display_cols[f"{q} Score"] = f"{q} Score"
    display_cols[f"{q} Rank"] = f"{q} Rank"

display_df = trend_table[list(display_cols.keys())].rename(columns=display_cols)

score_cols = [c for c in display_df.columns if "Score" in c]
display_df[score_cols] = display_df[score_cols].round(2)

def highlight_selected(row):
    if row["Trust"] in selected_names:
        return ["background-color: #1a3a5c; color: white"] * len(row)
    return [""] * len(row)

styled = (
    display_df.style
    .apply(highlight_selected, axis=1)
    .format({c: "{:.2f}" for c in score_cols}, na_rep="—")
    .format({c: "{:.0f}" for c in display_df.columns if "Rank" in c}, na_rep="—")
)

st.dataframe(styled, width='stretch', height=700)
