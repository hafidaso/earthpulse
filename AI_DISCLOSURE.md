# AI Usage Disclosure — EarthPulse (NASA Space Apps 2026)

In accordance with NASA International Space Apps Challenge rules on transparent disclosure of AI tools:

1. **Scope of AI Assistance**:
   - AI coding assistants were used during software engineering for the interactive Three.js 3D viewport (`components/earth_explorer/frontend/index.html`, `earth_3d.py`), Streamlit UI architecture (`lab.py`, `discover.py`, `studio_ui.py`, `expert_en.py`, `expert_ar.py`), bilingual English/Arabic technical localization, ReportLab vector PDF Evidence Passport & 7-slide deck formatting (`brief_pdf.py`, `EarthPulse-Demo.pdf`), and `pytest` / Playwright test scaffolding (`test_analysis.py`).
2. **Unaltered NASA & Open Terrain Data**:
   - Every climate file in `data/*.json` and `data/discovery/*_extended.json` is an unaltered JSON response retrieved directly from the **NASA POWER Monthly and Annual API (`v2.10.0`)** backed by **NASA GMAO MERRA-2** (`0.5° × 0.625°` grid).
   - Terrain elevation context (`data/morocco_dem_terrarium.json`) is decoded directly from **AWS Open Data Terrain Tiles / Mapzen Terrarium** (`NASA SRTM + ETOPO1`).
   - SHA-256 cryptographic checksums of the climate inputs are embedded in every generated Scientific Evidence Brief PDF and verified in `test_analysis.py`.
3. **Deterministic Statistical Engine**:
   - All annual & cross-year seasonal (`DJF`, `MAM`, `JJA`, `SON`) aggregations, Ordinary Least Squares (OLS) fits, Newey–West HAC covariance estimates, and paired difference trials (`D(year) = Variable_B(year) - Variable_A(year)`) are executed deterministically in Python (`analysis.py`) using `NumPy`, `SciPy`, and `statsmodels`. No AI model generates, alters, or interpolates statistical outputs at runtime.
