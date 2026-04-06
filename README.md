# NHS Pulse

In 2025, the NHS (National Health Service in the UK) started publishing league tables of all hospital trusts for the first time. With this data I've built [NHS Pulse](https://nhs-pulse.fawazshah.xyz/), where you can see the trend in how your local trust has been performing over time. You can also select a list of trusts to compare and contrast, and view the full league table.

<p align="center">
  <img src="/assets/screenshot.png" width="700">
</p>

Data available from [NHS England](https://data.england.nhs.uk/dashboard/nofacute).

Built with Streamlit, and deployed with [Render](https://render.com/).

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
