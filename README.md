# NHS Pulse

With NHS league tables being published for the first time in 2025, you can now see trends in how your local trust has been performing across multiple quarters. You can also view the full league table of scores and rankings per quarter.

<p align="center">
  <img src="/assets/screenshot.png" width="700">
</p>

Built with Streamlit. Data taken from NHS acute trust rankings, available at https://data.england.nhs.uk/dashboard/nofacute.

## Getting started

### Install dependencies

```bash
uv sync
```

### Run the app

```bash
uv run streamlit run app.py
```

### Run the backend individually

```bash
uv run backend.py
```

This fetches the latest data and prints the available quarters, trust count, and top 10 trusts by rank.

### Run backend tests

```
uv run pytest backend.py
```