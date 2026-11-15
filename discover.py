"""Guided Climate Discovery & Seasonal Fingerprints page for EarthPulse Investigation Studio."""
from __future__ import annotations

import streamlit as st

import analysis
import brief_pdf
import earth_3d
import studio_ui

studio_ui.inject_studio_styles()
studio_ui.render_masthead(
    title='Guided Climate Discovery & Seasonal Fingerprints',
    subtitle='Investigate 6 validated NASA POWER climate variables globally or explore how Morocco’s annual trends split across meteorological seasons.',
)

if 'discover_city' not in st.session_state:
    st.session_state['discover_city'] = 'Casablanca'
if 'discover_source_mode' not in st.session_state:
    st.session_state['discover_source_mode'] = 'Morocco Benchmark Cities (Verified Offline + Live)'
if 'discover_live_cache' not in st.session_state:
    st.session_state['discover_live_cache'] = {}

GUIDED_QUESTIONS = {
    'Is daytime heat climbing faster than nighttime warmth?': ('T2M_MAX', 'Marrakech'),
    'Does coastal air temperature mask a single-season trend?': ('T2M', 'Casablanca'),
    'Is atmospheric relative humidity drying inland vs. coast?': ('RH2M', 'Marrakech'),
    'Are nighttime minimum temperatures rising across cities?': ('T2M_MIN', 'Casablanca'),
    'Can we detect a rainfall shift above natural drought noise?': ('PRECTOTCORR', 'Marrakech'),
    'Have near-surface winds shifted over the past three decades?': ('WS2M', 'Casablanca'),
}

# Stage 1: Question & Variable
st.markdown('<p class="ep-sec-kicker">STEP 1 · WHAT TO INVESTIGATE</p>', unsafe_allow_html=True)
q_col1, q_col2 = st.columns([1.4, 1.0])
with q_col1:
    chosen_q = st.selectbox(
        'Start from a real scientific question (or pick any variable on the right)',
        list(GUIDED_QUESTIONS.keys()),
        index=1,
        key='disc_q_select',
    )
    suggested_param, suggested_city = GUIDED_QUESTIONS[chosen_q]
with q_col2:
    param_keys = list(analysis.DISCOVERY_VARIABLES.keys())
    param = st.selectbox(
        'Validated NASA POWER parameter',
        param_keys,
        index=param_keys.index(suggested_param),
        format_func=lambda k: f"{k} — {analysis.ALL_VARIABLES[k][0]} ({analysis.ALL_VARIABLES[k][1]})",
        key='disc_param_select',
    )

# Interactive 3D Earth Explorer synchronized with Discovery city
st.markdown('<p class="ep-sec-kicker">STEP 2 · WHERE ON EARTH (3D CONTEXT & CUSTOM COORDINATES)</p>', unsafe_allow_html=True)
exp_event = earth_3d.render_earth_explorer(
    selected_city=st.session_state['discover_city'],
    compare_city='Marrakech' if st.session_state['discover_city'] != 'Marrakech' else 'Casablanca',
    parameter=param,
    start=1991,
    end=2025,
    interval_mode='cautious',
    key_prefix='discover_3d',
)
if exp_event['changed']:
    st.session_state['discover_city'] = exp_event['selected_city']
    st.session_state['discover_source_mode'] = 'Morocco Benchmark Cities (Verified Offline + Live)'
    st.rerun()

loc_col1, loc_col2, loc_col3 = st.columns([1.2, 1.0, 1.0])
with loc_col1:
    source_mode = st.radio(
        'Coordinate Source',
        ['Morocco Benchmark Cities (Verified Offline + Live)', 'Custom Global Coordinate (Live NASA API)'],
        key='discover_source_mode',
    )
with loc_col2:
    if source_mode.startswith('Morocco'):
        cities = list(analysis.LOCATIONS.keys())
        sel_city = st.selectbox(
            'Benchmark City',
            cities,
            index=cities.index(st.session_state['discover_city']) if st.session_state['discover_city'] in cities else 0,
            key='discover_city_select',
        )
        if sel_city != st.session_state['discover_city']:
            st.session_state['discover_city'] = sel_city
            st.rerun()
        lat, lon = analysis.LOCATIONS[sel_city]
        loc_label = sel_city
        min_year, max_year = 1991, 2025
    else:
        lat = st.number_input('Latitude (°N)', min_value=-89.0, max_value=89.0, value=33.5731, step=0.1, format='%.4f')
        lon = st.number_input('Longitude (°E)', min_value=-179.0, max_value=179.0, value=-7.5898, step=0.1, format='%.4f')
        loc_label = st.text_input('Location label', value=f'Custom ({lat:.2f}°, {lon:.2f}°)')
        min_year, max_year = 1981, 2025
with loc_col3:
    lens_label = st.selectbox(
        'Uncertainty Assumption',
        ['Cautious max(SE_OLS, SE_HAC)', 'Raw Newey–West HAC (SE_HAC)', 'Conventional OLS (SE_OLS)'],
        index=0,
        key='disc_lens_sel',
    )
    lens_map = {
        'Cautious max(SE_OLS, SE_HAC)': 'cautious',
        'Raw Newey–West HAC (SE_HAC)': 'hac',
        'Conventional OLS (SE_OLS)': 'conventional',
    }
    interval_mode = lens_map[lens_label]

yr_c1, yr_c2 = st.columns(2)
with yr_c1:
    start_yr = st.slider('Start year', min_value=min_year, max_value=max_year - 29, value=max(min_year, 1991), key='disc_start')
with yr_c2:
    end_yr = st.slider('End year', min_value=start_yr + 29 if source_mode.startswith('Morocco') else min_year + 29, max_value=max_year, value=2025, key='disc_end')

# Resolve dataset cleanly
dataset = None
fetch_err = None
if source_mode.startswith('Morocco'):
    dataset = analysis.load_city_dataset(loc_label, parameter=param)
else:
    cache_key = f"{lat:.4f},{lon:.4f},{param},{start_yr},{end_yr}"
    if cache_key in st.session_state['discover_live_cache']:
        dataset = st.session_state['discover_live_cache'][cache_key]
    else:
        if st.button('Fetch Live NASA POWER Data for Custom Coordinate', type='primary'):
            with st.spinner('Querying NASA POWER monthly API (unaltered measurements)...'):
                try:
                    dataset = analysis.fetch_power(lat, lon, start=start_yr, end=end_yr, parameters=param)
                    st.session_state['discover_live_cache'][cache_key] = dataset
                except Exception as exc:
                    fetch_err = str(exc)

if fetch_err:
    st.error(f'Live NASA fetch failed: {fetch_err}')

if dataset is None:
    st.info('Select **Fetch Live NASA POWER Data** above to run Discovery and Seasonal Fingerprints at your custom global coordinates.')
    st.stop()

# Compute Annual + Seasonal Fingerprints
sf = analysis.seasonal_fingerprints(loc_label, dataset, parameter=param, start=start_yr, end=end_yr, interval_mode=interval_mode)
ann = sf['annual']
var_name, ann_unit = analysis.ALL_VARIABLES[param]
seas_unit = sf['seasonal_unit']
rate_unit = sf['rate_unit']

st.markdown('<p class="ep-sec-kicker">STEP 3 · SEASONAL FINGERPRINTS — DOES THE ANNUAL TREND HIDE A SEASONAL DIFFERENCE?</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="ep-prose">Meteorological seasons aggregate three months each: <strong>DJF</strong> (cross-year Dec Y−1 + Jan Y + Feb Y), <strong>MAM</strong>, <strong>JJA</strong>, and <strong>SON</strong>. {sf["djf_boundary_note"]}</p>',
    unsafe_allow_html=True,
)

# Verdict highlight banner
sig_seasons = [k for k, v in sf['seasons'].items() if v.get('eligible') and v.get('excludes_zero')]
ann_ex0 = ann.get('eligible') and ann.get('active_excludes_zero')
if ann.get('eligible'):
    ar = ann['result']
    ann_txt = f"{analysis.format_bound(ar['slope_decade'])} {ann_unit}/dec (95% CI {analysis.format_interval(ann['active_ci'], f'{ann_unit}/dec')})"
else:
    ann_txt = 'Withheld (<30 consecutive complete years)'

box_cls = 'is-amber' if sig_seasons else 'is-slate'
badge_cls = 'is-amber' if sig_seasons else 'is-slate'
badge_txt = f"◆ {len(sig_seasons)} / 4 seasons exclude zero ({', '.join(sig_seasons)})" if sig_seasons else '● All 4 seasons cross zero (inconclusive)'
st.markdown(
    f"""
    <div class="ep-verdict-box {box_cls}">
      <span class="ep-badge {badge_cls}">{badge_txt}</span>
      <h3 style="margin:0 0 0.3rem 0; font-size:1.1rem;">{loc_label} · {var_name} ({start_yr}–{end_yr})</h3>
      <p class="ep-prose" style="margin:0;">Annual baseline: <strong>{ann_txt}</strong>. Exploratory seasonal test: {sf['multiplicity_caveat']}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

fig_whisk = studio_ui.build_seasonal_whisker_fig(sf)
st.plotly_chart(fig_whisk, use_container_width=True, key='disc_whisker_chart')

# Tabular per-season metrics
s_cols = st.columns(4)
for col, scode in zip(s_cols, ('DJF', 'MAM', 'JJA', 'SON')):
    sdata = sf['seasons'][scode]
    with col:
        st.markdown(f"**{sdata['label']}**")
        if sdata.get('eligible'):
            ex = sdata['excludes_zero']
            icon = '◆ Excludes 0' if ex else '○ Crosses 0'
            st.metric(
                label=f"n = {sdata['n']} ({sdata['start']}–{sdata['end']})",
                value=f"{analysis.format_bound(sdata['slope_decade'])} {rate_unit}",
                delta=f"{icon} · p={sdata['active_p']:.3g}",
                delta_color='off',
            )
            st.caption(
                f"95% CI: {analysis.format_interval(sdata['active_ci'], rate_unit)} · "
                f"SE_OLS={sdata['se_ols_decade']:.3f}, SE_HAC={sdata['se_hac_decade']:.3f} ({sdata['hac_to_ols_se_ratio']:.2f}x)"
            )
            if sdata['omitted']:
                st.caption(f"Omitted incomplete/boundary years: {sdata['omitted']}")
        else:
            st.warning(sdata.get('status_label', 'Withheld (<30 complete seasons)'))

# Single season series inspector
insp_season = st.selectbox(
    'Inspect yearly seasonal series',
    ['DJF', 'MAM', 'JJA', 'SON'],
    format_func=lambda k: sf['seasons'][k]['label'],
    key='disc_insp_season',
)
s_sel = sf['seasons'][insp_season]
if len(s_sel['frame']) > 0:
    fig_ts = studio_ui.build_dual_city_fig(
        {
            'location': f"{loc_label} ({insp_season})",
            'frame': s_sel['frame'],
            'eligible': s_sel.get('eligible', False),
            'result': s_sel if s_sel.get('eligible') else None,
        },
        {'location': 'Baseline', 'frame': s_sel['frame'].iloc[0:0], 'eligible': False},
        param,
    )
    # Single-trace clean update
    fig_ts.data = fig_ts.data[:2] if s_sel.get('eligible') else fig_ts.data[:1]
    fig_ts.update_layout(yaxis_title=f"{insp_season} {var_name} ({seas_unit})")
    st.plotly_chart(fig_ts, use_container_width=True, key='disc_season_ts')

# 4-Level Scientific Communication Summary + Download Passport
st.markdown('<p class="ep-sec-kicker">STEP 4 · 4-LEVEL SCIENTIFIC SUMMARY & EVIDENCE PASSPORT V4</p>', unsafe_allow_html=True)
sha_info = analysis.source_sha256(loc_label, dataset)
plain_ans = (
    f"For {loc_label} ({var_name}, {start_yr}–{end_yr}), annual rate is {ann_txt}. "
    + (
        f"Seasonally, {', '.join(sig_seasons)} show intervals excluding zero ({lens_label})."
        if sig_seasons
        else f"Individually, none of the four 3-month seasons exclude zero under {lens_label}."
    )
)
key_nums = (
    f"n_annual = {ann['n_complete']}; "
    + "; ".join(
        f"{k}: {analysis.format_bound(sf['seasons'][k]['slope_decade'])} (n={sf['seasons'][k]['n']})"
        for k in ('DJF', 'MAM', 'JJA', 'SON')
        if sf['seasons'][k].get('eligible')
    )
)
meth_txt = (
    "Monthly NASA POWER point series checked against unit & physical bounds, day-weighted for means or summed for precipitation. "
    "DJF strictly pairs Dec(Y−1)+Jan(Y)+Feb(Y) with zero boundary padding. OLS on centered year with Newey–West HAC SE and max(SE_OLS, SE_HAC) safeguard."
)
prov_txt = f"{sha_info['scope']} · SHA-256: {sha_info['sha256'][:24]}…"
studio_ui.render_four_level_summary(plain_ans, key_nums, meth_txt, prov_txt)

pdf_bytes = brief_pdf.build_scientific_evidence_brief_pdf(
    question=f"Seasonal Fingerprints — {loc_label} ({var_name})",
    parameter=param,
    start=start_yr,
    end=end_yr,
    loc_a=loc_label,
    lat_a=lat,
    lon_a=lon,
    data_a=dataset,
    seasonal=sf,
    interval_mode=interval_mode,
)
st.download_button(
    label='Download One-Page Seasonal Evidence Passport (PDF)',
    data=pdf_bytes,
    file_name=f"EarthPulse_Seasonal_Brief_{loc_label.replace(' ', '_')}_{param}_{start_yr}_{end_yr}.pdf",
    mime='application/pdf',
)
