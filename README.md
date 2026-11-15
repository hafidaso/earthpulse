# EarthPulse — The Climate Trend Detective

Hafida Belayd, EarthPulse Labs, Casablanca. An independent 2026 NASA Space Apps project for “Be An Earth System Trend Detective!”

[Open the live EarthPulse dashboard](https://earthpulse-labs-hafidaso.streamlit.app/) · [Seven-slide demo](EarthPulse-Demo.pdf)

Run with Python 3.11:
```sh
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

Select a Moroccan example or enter coordinates. Choose temperature or precipitation and a window of at least 30 consecutive complete years. The four bundled NASA responses cover 1991–2025. Other requests use NASA POWER live.

## Method

For each year, require 12 finite values and reject the NASA fill value. Ignore the API's month 13 annual summary. Weight temperature by days per month. Multiply precipitation's mean daily rate by days per month and sum the resulting monthly amounts. Use OLS on calendar year, reporting the slope per decade and exploratory two-sided t inference with the larger of conventional and Newey–West HAC standard errors. HAC uses Bartlett weights, finite-sample correction and floor(4(n/100)^(2/9)) annual lags. Annual aggregation addresses within-year seasonality. It does not resolve long-memory dependence, nonlinear trends or changes in the observing system. No adjustment for multiple comparisons.

Marrakech temperature rose an estimated +0.48 °C per decade for 1991–2025 (exploratory 95% interval +0.23 to +0.73). Casablanca's estimate was +0.22 °C per decade (−0.03 to +0.46). All four precipitation intervals included zero. These are gridded reanalysis estimates. Trends describe the selected cells and period. Statistical significance does not establish causation.

Source responses carry request URLs and retrieval times. See data/results.json for verified estimates and snapshot checksums, REFERENCES.md for credits, and AI_DISCLOSURE.md for AI use.
