# AI Usage Disclosure — EarthPulse (NASA Space Apps 2026)

In accordance with NASA International Space Apps Challenge rules on transparent disclosure of AI tools:

1. **Scope of AI Assistance**:
   - AI coding assistants were used during development for Streamlit UI layout (`lab.py`, `expert_en.py`, `expert_ar.py`), bilingual English/Arabic technical translation, ReportLab PDF layout (`brief_pdf.py` and `EarthPulse-Demo.pdf`), and `pytest` regression test scaffolding (`test_analysis.py`).
2. **Unaltered NASA Data**:
   - Every climate data file in `data/*.json` is an unaltered JSON response retrieved directly from the **NASA POWER Monthly and Annual API (`v2.10.0`)** backed by **NASA GMAO MERRA-2** (`0.5° × 0.625°` grid).
   - SHA-256 cryptographic checksums of the input files are embedded in every generated Scientific Evidence Brief PDF and verified in `test_analysis.py`.
3. **Deterministic Statistical Engine**:
   - All annual aggregations, Ordinary Least Squares (OLS) fits, Newey–West HAC covariance estimates, and paired difference trials (`D(year) = Variable_B(year) - Variable_A(year)`) are executed deterministically in Python (`analysis.py`) using `NumPy`, `SciPy`, and `statsmodels`. No AI model generates, modifies, or interprets statistical outputs at runtime.
