# References & AI Usage Disclosure

## Official NASA Challenge & Data Sources
- **Official Challenge**: [NASA Space Apps 2026 — "Be An Earth System Trend Detective!"](https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/)
- **Primary NASA Data Source**: [NASA POWER Monthly and Annual API (v2.10.0)](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) — Agroclimatology (`AG`) community, monthly `T2M` (temperature at 2 meters, °C) and `PRECTOTCORR` (corrected total precipitation, mm/day). Every bundled snapshot in `data/*.json` preserves the exact NASA POWER API request URL and response payload unaltered, verified via SHA-256 checksums.
- **Underlying NASA Meteorological Reanalysis**: [NASA Global Modeling and Assimilation Office (GMAO) MERRA-2](https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/) — Modern-Era Retrospective analysis for Research and Applications, Version 2 (`0.5° latitude × 0.625° longitude` native horizontal grid spacing).
- **Challenge Resource Cross-Reference**: [NASA Giovanni (GES DISC Interactive Online Visualization ANd aNalysis Infrastructure)](https://giovanni.gsfc.nasa.gov/giovanni/) — official challenge resource for exploring NASA gridded Earth science time series, including MERRA-2 atmospheric and surface variables.

## Statistical Methodology
- **Newey, W. K., & West, K. D. (1987)**: *A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix*, Econometrica, 55(3), 703–708. [https://doi.org/10.2307/1913610](https://doi.org/10.2307/1913610)
- **WMO Climatological Standard Normals**: Minimum 30 consecutive complete years required before reporting a linear climate trend.

## Open-Source Software
- [Python 3.11+](https://www.python.org/), [Streamlit](https://streamlit.io/), [Plotly](https://plotly.com/python/), [pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), [SciPy](https://scipy.org/), [statsmodels](https://www.statsmodels.org/), [Requests](https://requests.readthedocs.io/), [pytest](https://pytest.org/), [ReportLab](https://www.reportlab.com/), [PyMuPDF](https://pymupdf.readthedocs.io/).

## AI Usage Disclosure (NASA Space Apps Transparency Requirement)
- **AI Assistance**: Generative AI coding assistants were used to assist with software engineering, user-interface layout, bilingual English/Arabic localization, automated test scaffolding, and PDF report formatting.
- **Scientific & Data Integrity**: **No climate measurements, coordinates, or statistical results were generated or altered by AI.** All bundled records (`data/casablanca.json`, `data/rabat.json`, `data/marrakech.json`, `data/ouarzazate.json`) come unaltered from the NASA POWER API (`MERRA-2` reanalysis), and all slopes, standard errors, `p`-values, and confidence intervals are computed deterministically by `analysis.py` using NumPy, SciPy, and `statsmodels`, verified by 20 automated `pytest` tests.
