# References & AI Usage Disclosure

## Official NASA Challenge & Data Sources
- **Official Challenge**: [NASA Space Apps 2026 — "Be An Earth System Trend Detective!"](https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/)
- **Primary NASA Data Source**: [NASA POWER Monthly and Annual API (v2.10.0)](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) — Agroclimatology (`AG`) community, monthly `T2M` (°C), `T2M_MAX` (°C), `T2M_MIN` (°C), `PRECTOTCORR` (mm/day), `RH2M` (%), and `WS2M` (m/s). Unaltered JSON responses and exact API URLs are archived under `data/*.json` and `data/discovery/*_extended.json`, verified via SHA-256 checksums.
- **Underlying NASA Meteorological Reanalysis**: [NASA Global Modeling and Assimilation Office (GMAO) MERRA-2](https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/) — Modern-Era Retrospective analysis for Research and Applications, Version 2 (`0.5° latitude × 0.625° longitude` native horizontal grid spacing).
- **Challenge Resource Cross-Reference**: [NASA Giovanni (GES DISC Interactive Online Visualization ANd aNalysis Infrastructure)](https://giovanni.gsfc.nasa.gov/giovanni/) — official challenge resource for exploring NASA gridded Earth science time series.
- **Topographic Elevation Context (Non-Interpolated 3D Explorer)**: [AWS Open Data Terrain Tiles / Mapzen Terrarium](https://registry.opendata.aws/terrain-tiles/) (`elevation-tiles-prod`), combining NASA SRTM/NASADEM land elevation with ETOPO1 ocean bathymetry (`data/morocco_dem_terrarium.json`). Terrain mesh provides geographic context only; no climate trends are interpolated across terrain.

## Statistical Methodology
- **Newey, W. K., & West, K. D. (1987)**: *A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix*, Econometrica, 55(3), 703–708. [https://doi.org/10.2307/1913610](https://doi.org/10.2307/1913610)
- **WMO Climatological Standard Normals**: Minimum 30 consecutive complete years required before reporting a linear climate trend.

## Open-Source Software
- [Python 3.11+](https://www.python.org/), [Streamlit](https://streamlit.io/), [Three.js](https://threejs.org/) (`r128`), [Plotly](https://plotly.com/python/), [pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), [SciPy](https://scipy.org/), [statsmodels](https://www.statsmodels.org/), [Requests](https://requests.readthedocs.io/), [pytest](https://pytest.org/), [ReportLab](https://www.reportlab.com/), [PyMuPDF](https://pymupdf.readthedocs.io/).

## AI Usage Disclosure (NASA Space Apps Transparency Requirement)
- **AI Assistance**: Generative AI coding assistants were used to assist with software engineering (Three.js 3D terrain explorer component, Streamlit multipage layout, bilingual English/Arabic technical localization, ReportLab vector PDF chart formatting, and automated test scaffolding).
- **Scientific & Data Integrity**: **No climate measurements, terrain elevations, coordinates, or statistical results were generated or altered by AI.** All bundled JSON records (`data/*.json`, `data/discovery/*_extended.json`) come unaltered from the NASA POWER API (`MERRA-2`), terrain grids come directly from decoded AWS/Mapzen Terrarium tiles (`data/morocco_dem_terrarium.json`), and all slopes, standard errors, `p`-values, and confidence intervals are computed deterministically by `analysis.py` and verified by 24 automated `pytest` tests.
