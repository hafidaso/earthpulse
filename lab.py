"""EarthPulse — Earth Investigation Studio default landing experience."""
from __future__ import annotations

import streamlit as st

import analysis
import brief_pdf
import earth_3d
import studio_ui

studio_ui.inject_studio_styles()
studio_ui.render_masthead(
    title='The climate tells a story. Can you prove it?',
    subtitle='From the planet to the proof. Investigate NASA POWER climate records inside 3D Morocco terrain, challenge statistical assumptions, and verify every conclusion.',
)

if 'lab_focus_city' not in st.session_state:
    st.session_state['lab_focus_city'] = 'Marrakech'
if 'lab_case_choice' not in st.session_state:
    st.session_state['lab_case_choice'] = 'CASE 001 — THE TWO CITIES'

# Active Studio Investigation Strip
focus_city = st.session_state['lab_focus_city']
target_b = focus_city if focus_city != 'Casablanca' else 'Marrakech'

studio_ui.render_journey_bar(active_step=1)

# STAGE 1: 3D EARTH EVIDENCE EXPLORER
st.markdown('<p class="ep-sec-kicker">STAGE 1 · EXPLORE EARTH & MERRA-2 SPATIAL CONTEXT</p>', unsafe_allow_html=True)
st.markdown('<h2 class="ep-h2">3D Topographic Context & Approximate Reanalysis Scale</h2>', unsafe_allow_html=True)

c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([1.4, 1.0, 1.0])
with c_ctrl1:
    case_choice = st.selectbox(
        'Investigation Case',
        [
            'CASE 001 — THE TWO CITIES',
            'CASE 002 — THE FALSE CERTAINTY',
            'CASE 003 — THE RAINFALL QUESTION',
        ],
        key='lab_case_choice',
    )
with c_ctrl2:
    start_year = st.slider('Analysis start year (>=30 yr required)', 1991, 1996, 1991, key='lab_start_yr')
with c_ctrl3:
    lens_choice = st.selectbox(
        'Uncertainty assumption',
        ['Cautious max(SE_OLS, SE_HAC)', 'Raw Newey–West HAC (SE_HAC)', 'Conventional OLS (SE_OLS)'],
        index=0,
        key='lab_lens_choice',
    )

lens_map = {
    'Cautious max(SE_OLS, SE_HAC)': 'cautious',
    'Raw Newey–West HAC (SE_HAC)': 'hac',
    'Conventional OLS (SE_OLS)': 'conventional',
}
interval_mode = lens_map[lens_choice]
active_param_3d = 'PRECTOTCORR' if case_choice.startswith('CASE 003') else 'T2M'

exp_event = earth_3d.render_earth_explorer(
    selected_city=focus_city,
    compare_city='Casablanca' if focus_city != 'Casablanca' else 'Marrakech',
    parameter=active_param_3d,
    start=start_year,
    end=2025,
    interval_mode=interval_mode,
    key_prefix='lab_3d',
)
if exp_event['changed']:
    st.session_state['lab_focus_city'] = exp_event['selected_city']
    st.rerun()

# Load datasets cleanly from verified offline NASA snapshots
data_casa = analysis.load_city_dataset('Casablanca', parameter=active_param_3d)
data_focus = analysis.load_city_dataset(focus_city, parameter=active_param_3d)
data_target_b = analysis.load_city_dataset(target_b, parameter='T2M')
data_casa_t2m = analysis.load_city_dataset('Casablanca', parameter='T2M')
data_rain_focus = analysis.load_city_dataset(focus_city, parameter='PRECTOTCORR')

# STAGE 2 & 3: QUESTION & PREDICT
st.markdown('<p class="ep-sec-kicker">STAGE 2 & 3 · QUESTION & PREDICT BEFORE TESTING</p>', unsafe_allow_html=True)

if case_choice.startswith('CASE 001'):
    q_title = f"Is {target_b} warming faster than Casablanca?"
    q_subtitle = (
        f"Both cities sit in the same regional latitudes, separated by the Atlantic Ocean and interior plain topography. "
        f"Click any city on the 3D Earth Explorer above to pair it against Casablanca (currently: <strong>{target_b}</strong> vs <strong>Casablanca</strong>)."
    )
    pred_options = [
        f"Yes — {target_b} is clearly warming faster",
        'Maybe — year-to-year climate swings could mask a real gap',
        f"No — Casablanca and {target_b} warm at basically the same rate",
    ]
    pred_key = f'pred_case001_{target_b}'
elif case_choice.startswith('CASE 002'):
    q_title = f"Can ignoring time dependence change a climate verdict? ({focus_city})"
    q_subtitle = (
        "Consecutive years share slow ocean–atmosphere persistence. Standard OLS assumes yearly residuals are completely independent. "
        "Does testing with autocorrelation-aware HAC errors flip the verdict?"
    )
    pred_options = [
        'No — standard regression confidence intervals stay just as reliable',
        'Yes — assuming yearly independence can make noisy trends look decisive',
    ]
    pred_key = f'pred_case002_{focus_city}'
else:
    q_title = f"Can we establish a precipitation trend in {focus_city}?"
    q_subtitle = (
        "North African precipitation swings sharply between multi-year drought and wet winters. "
        "Do 35 years of NASA POWER precipitation records prove an upward or downward shift?"
    )
    pred_options = [
        f'Yes — {focus_city} has a decisive drying or wetting trend',
        'No — year-to-year rainfall variability dominates any clear linear slope',
    ]
    pred_key = f'pred_case003_{focus_city}'

st.markdown(f'<h2 class="ep-h2">{q_title}</h2>', unsafe_allow_html=True)
st.markdown(f'<p class="ep-prose">{q_subtitle}</p>', unsafe_allow_html=True)

pred_col, act_col = st.columns([2.2, 1.0])
with pred_col:
    user_pred = st.radio('What do you expect the NASA evidence to support? (Optional prediction)', pred_options, key=pred_key)
with act_col:
    if focus_city != 'Marrakech' and case_choice.startswith('CASE 001'):
        if st.button('Reset Case 001 to Marrakech vs Casablanca', use_container_width=True):
            st.session_state['lab_focus_city'] = 'Marrakech'
            st.rerun()

# STAGE 4 & 5: TEST DATA & CHALLENGE ASSUMPTIONS
st.markdown('<p class="ep-sec-kicker">STAGE 4 & 5 · TEST EVIDENCE & CHALLENGE ASSUMPTIONS</p>', unsafe_allow_html=True)

if case_choice.startswith('CASE 001'):
    trial = analysis.climate_trial(
        'Casablanca',
        data_casa_t2m,
        target_b,
        data_target_b,
        parameter='T2M',
        start=start_year,
        end=2025,
        interval_mode=interval_mode,
    )
    comp = None
    single_site = None
    seasonal_data = None
    pdf_question = q_title
    pdf_param = 'T2M'
    pdf_loc_a, pdf_lat_a, pdf_lon_a, pdf_data_a = ('Casablanca', *analysis.LOCATIONS['Casablanca'], data_casa_t2m)
    pdf_loc_b, pdf_lat_b, pdf_lon_b, pdf_data_b = (target_b, *analysis.LOCATIONS[target_b], data_target_b)

    sa = trial['site_a']
    sb = trial['site_b']
    diff_res = trial['diff_result']
    ex0 = trial['active_excludes_zero']
    box_cls = 'is-amber' if ex0 and diff_res['slope_decade'] > 0 else ('is-teal' if ex0 else 'is-slate')
    badge_cls = 'is-amber' if ex0 and diff_res['slope_decade'] > 0 else ('is-teal' if ex0 else 'is-slate')
    badge_symbol = '◆ POSITIVE DIFFERENCE (EXCLUDES ZERO)' if (ex0 and diff_res['slope_decade'] > 0) else ('▲ NEGATIVE DIFFERENCE (EXCLUDES ZERO)' if ex0 else '● INCONCLUSIVE (CROSSES ZERO)')

    st.markdown(
        f"""
        <div class="ep-verdict-box {box_cls}">
          <span class="ep-badge {badge_cls}">{badge_symbol}</span>
          <h3 style="margin:0 0 0.35rem 0; font-size:1.12rem;">{trial['verdict_label']}</h3>
          <p class="ep-prose" style="margin:0;">{trial['interpretation']} {trial['overlap_insight']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        f"Casablanca slope",
        f"{analysis.format_bound(sa['result']['slope_decade'])} °C/dec",
        sa['active_status'],
        delta_color='off',
    )
    m2.metric(
        f"{target_b} slope",
        f"{analysis.format_bound(sb['result']['slope_decade'])} °C/dec",
        sb['active_status'],
        delta_color='off',
    )
    m3.metric(
        f"Paired difference D = {target_b} − Casa",
        f"{analysis.format_bound(diff_res['slope_decade'])} °C/dec",
        f"p = {trial['active_p']:.2e}",
        delta_color='off',
    )
    m4.metric(
        'Paired 95% Interval',
        analysis.format_interval(trial['active_ci'], ''),
        f"n = {trial['n_paired']} paired years",
        delta_color='off',
    )

    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(studio_ui.build_dual_city_fig(sa, sb, 'T2M'), use_container_width=True, key='lab_dual_fig')
    with ch2:
        st.plotly_chart(studio_ui.build_diff_trial_fig(trial, 'Casablanca', target_b, '°C/dec', '°C'), use_container_width=True, key='lab_diff_fig')

    # 4-Level summary content
    plain_ans = (
        f"Over {start_year}–2025, pairing each calendar year removes shared Moroccan regional heatwaves and cool years. "
        + (f"{target_b} warms faster than Casablanca by {analysis.format_bound(diff_res['slope_decade'])} °C/decade." if ex0 else "The paired difference interval crosses zero, so the evidence is inconclusive (not proof of equal warming).")
    )
    key_nums = (
        f"Casablanca: {analysis.format_bound(sa['result']['slope_decade'])} [{analysis.format_interval(sa['active_ci'], '')}] · "
        f"{target_b}: {analysis.format_bound(sb['result']['slope_decade'])} [{analysis.format_interval(sb['active_ci'], '')}] · "
        f"Difference D: {analysis.format_bound(diff_res['slope_decade'])} °C/dec (95% CI {analysis.format_interval(trial['active_ci'], '°C/dec')})."
    )
    meth_txt = (
        f"D(year) = {target_b}(year) − Casablanca(year). OLS slope matches slope(B) − slope(A) to {trial['slope_diff_identity_delta']:.1e}. "
        f"Active error mode: {lens_choice} with {diff_res['hac_lags']} Newey–West lags."
    )
    sha_c = analysis.source_sha256('Casablanca', data_casa_t2m)['sha256'][:14]
    sha_b = analysis.source_sha256(target_b, data_target_b)['sha256'][:14]
    prov_txt = f"NASA POWER MERRA-2 0.5° × 0.625° · Casa SHA-256: {sha_c}… · {target_b} SHA-256: {sha_b}…"

elif case_choice.startswith('CASE 002'):
    data_c2 = analysis.load_city_dataset(focus_city, parameter='T2M')
    site_c2 = analysis.evaluate_site(focus_city, data_c2, 'T2M', start_year, 2025, interval_mode=interval_mode)
    res_c2 = site_c2['result']
    lens_info = analysis.uncertainty_lens_summary(res_c2)
    trial = None
    comp = None
    single_site = site_c2
    seasonal_data = analysis.seasonal_fingerprints(focus_city, data_c2, 'T2M', start_year, 2025, interval_mode=interval_mode)
    pdf_question = q_title
    pdf_param = 'T2M'
    pdf_loc_a, pdf_lat_a, pdf_lon_a, pdf_data_a = (focus_city, *analysis.LOCATIONS[focus_city], data_c2)
    pdf_loc_b, pdf_lat_b, pdf_lon_b, pdf_data_b = (None, None, None, None)

    verdict_flipped = bool(site_c2['time_dependence_changes_verdict'])
    badge_txt = '◆ VERDICT FLIPS WHEN TIME DEPENDENCE IS INCLUDED' if verdict_flipped else ('◆ CONSISTENT SIGNAL ACROSS ASSUMPTIONS' if lens_info['cautious_excludes_zero'] else '● INTERVAL CROSSES ZERO ACROSS ASSUMPTIONS')
    st.markdown(
        f"""
        <div class="ep-verdict-box {'is-amber' if verdict_flipped else 'is-teal'}">
          <span class="ep-badge {'is-amber' if verdict_flipped else 'is-teal'}">{badge_txt}</span>
          <h3 style="margin:0 0 0.35rem 0; font-size:1.12rem;">{focus_city}: OLS SE vs. Raw Newey–West HAC vs. Cautious Safeguard</h3>
          <p class="ep-prose" style="margin:0;">
            OLS assumes residuals are independent across years (SE_OLS = {lens_info['se_ols_decade']:.4f} °C/dec, 95% CI {analysis.format_interval(lens_info['ols_ci95'], '°C/dec')}, p = {res_c2['iid_p']:.4g}).
            Accounting for lag-1 persistence (r₁ = {res_c2['residual_lag1']:+.2f}, {res_c2['hac_lags']} lags) yields Raw SE_HAC = {lens_info['se_hac_decade']:.4f} °C/dec
            (HAC/OLS ratio = {lens_info['hac_to_ols_se_ratio']:.2f}× — relative SE change only, NOT a false-positive rate),
            and cautious 95% CI {analysis.format_interval(lens_info['cautious_ci95'], '°C/dec')} (p = {res_c2['p_value']:.4g}).
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_ols, c_hac, c_cau, c_ratio = st.columns(4)
    c_ols.metric('Conv. OLS SE', f"{lens_info['se_ols_decade']:.4f}", 'Excludes 0' if lens_info['ols_excludes_zero'] else 'Crosses 0', delta_color='off')
    c_hac.metric('Raw HAC SE', f"{lens_info['se_hac_decade']:.4f}", 'Excludes 0' if lens_info['hac_excludes_zero'] else 'Crosses 0', delta_color='off')
    c_cau.metric('Cautious max SE', f"{lens_info['se_cautious_decade']:.4f}", 'Excludes 0' if lens_info['cautious_excludes_zero'] else 'Crosses 0', delta_color='off')
    c_ratio.metric('SE_HAC / SE_OLS', f"{lens_info['hac_to_ols_se_ratio']:.2f}×", 'Relative SE change only', delta_color='off')

    # Seasonal Fingerprint teaser revealing autumn/summer shifts inside annual series
    st.markdown(f"**Does the annual record in {focus_city} hide a seasonal signal?** Explore seasonal fingerprints below (exploratory 4-season slice):")
    st.plotly_chart(studio_ui.build_seasonal_whisker_fig(seasonal_data), use_container_width=True, key='lab_case002_seas')

    plain_ans = (
        f"In {focus_city}, conventional OLS says 95% CI {analysis.format_interval(lens_info['ols_ci95'], '°C/dec')}, "
        f"whereas cautious time-dependent bounds give {analysis.format_interval(lens_info['cautious_ci95'], '°C/dec')}. "
        + ("Naive independence makes an inconclusive annual average look statistically decisive!" if verdict_flipped else "Notice also how seasonal sub-trends (especially SON) differ from the smoothed annual average.")
    )
    key_nums = f"Slope = {analysis.format_bound(res_c2['slope_decade'])} °C/dec · SE_OLS = {lens_info['se_ols_decade']:.4f} · Raw SE_HAC = {lens_info['se_hac_decade']:.4f} · Ratio = {lens_info['hac_to_ols_se_ratio']:.2f}×."
    meth_txt = f"Bartlett kernel Newey–West HAC ({res_c2['hac_lags']} lags, finite-sample t df={res_c2['n']-2}); cautious safeguard uses max(SE_OLS, SE_HAC) to prevent accidental small-sample downward HAC variance shrinkage."
    sha_f = analysis.source_sha256(focus_city, data_c2)['sha256'][:14]
    prov_txt = f"Unaltered NASA POWER snapshot ({focus_city.lower()}.json) · SHA-256: {sha_f}…"

else:
    site_r = analysis.evaluate_site(focus_city, data_rain_focus, 'PRECTOTCORR', start_year, 2025, interval_mode=interval_mode)
    res_r = site_r['result']
    trial = None
    comp = None
    single_site = site_r
    seasonal_data = None
    pdf_question = q_title
    pdf_param = 'PRECTOTCORR'
    pdf_loc_a, pdf_lat_a, pdf_lon_a, pdf_data_a = (focus_city, *analysis.LOCATIONS[focus_city], data_rain_focus)
    pdf_loc_b, pdf_lat_b, pdf_lon_b, pdf_data_b = (None, None, None, None)

    ex0_r = site_r['active_excludes_zero']
    st.markdown(
        f"""
        <div class="ep-verdict-box is-slate">
          <span class="ep-badge is-slate">{'◆ EXCLUDES ZERO' if ex0_r else '● INCONCLUSIVE (CROSSES ZERO — NOT PROOF OF ZERO CHANGE)'}</span>
          <h3 style="margin:0 0 0.35rem 0; font-size:1.12rem;">{focus_city}: Annual Precipitation Slope = {analysis.format_bound(res_r['slope_decade'])} mm/year/decade</h3>
          <p class="ep-prose" style="margin:0;">
            With wide 95% confidence interval {analysis.format_interval(site_r['active_ci'], 'mm/year/dec')} (p = {site_r['active_p']:.3g}),
            natural interannual wet/dry variability dwarfs any smooth linear trend over {res_r['n']} years.
            <strong>Inconclusive means zero is not excluded — never conclude rainfall is unchanging.</strong>
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    fig_r = studio_ui.build_dual_city_fig(
        site_r,
        {'location': 'Reference', 'frame': site_r['frame'].iloc[0:0], 'eligible': False},
        'PRECTOTCORR',
    )
    fig_r.data = fig_r.data[:2]
    st.plotly_chart(fig_r, use_container_width=True, key='lab_rain_fig')

    plain_ans = f"Over {res_r['n']} years in {focus_city}, rainfall fluctuates strongly year to year; a linear trend is inconclusive (interval crosses zero), which is NOT evidence of no change."
    key_nums = f"Mean = {res_r['mean']:.1f} mm/yr · Slope = {analysis.format_bound(res_r['slope_decade'])} mm/yr/dec · 95% CI {analysis.format_interval(site_r['active_ci'], 'mm/yr/dec')} · R² = {res_r['r_squared']:.3f}."
    meth_txt = "Sum of daily precipitation rate × calendar days/month (leap years preserved); PRECTOTCORR >= 0 validated across all 12 months."
    sha_r = analysis.source_sha256(focus_city, data_rain_focus)['sha256'][:14]
    prov_txt = f"NASA POWER PRECTOTCORR (mm/day -> mm/yr) · SHA-256: {sha_r}…"

studio_ui.render_four_level_summary(plain_ans, key_nums, meth_txt, prov_txt)

# STAGE 6: VERIFY & DOWNLOAD ONE-PAGE EVIDENCE PASSPORT V4
st.markdown('<p class="ep-sec-kicker">STAGE 6 · VERIFY EVIDENCE PASSPORT V4 & EXPLORE FURTHER</p>', unsafe_allow_html=True)
pdf_bytes = brief_pdf.build_scientific_evidence_brief_pdf(
    question=pdf_question,
    parameter=pdf_param,
    start=start_year,
    end=2025,
    loc_a=pdf_loc_a,
    lat_a=pdf_lat_a,
    lon_a=pdf_lon_a,
    data_a=pdf_data_a,
    loc_b=pdf_loc_b,
    lat_b=pdf_lat_b,
    lon_b=pdf_lon_b,
    data_b=pdf_data_b,
    trial=trial,
    comp=comp,
    single_site=single_site,
    interval_mode=interval_mode,
)

nav_c1, nav_c2, nav_c3, nav_c4 = st.columns([1.5, 1.0, 1.0, 0.9])
with nav_c1:
    st.download_button(
        label='Download Evidence Passport (1-Page PDF with Chart & SHA-256)',
        data=pdf_bytes,
        file_name=f"EarthPulse_Evidence_Passport_{pdf_loc_a}_{pdf_param}.pdf",
        mime='application/pdf',
        use_container_width=True,
    )
with nav_c2:
    st.page_link('discover.py', label='Discovery & Seasonal Fingerprints →', icon='🛰️')
with nav_c3:
    st.page_link('expert_en.py', label='Full Expert Analysis Lab →', icon='🔬')
with nav_c4:
    st.page_link('expert_ar.py', label='الواجهة العربية →', icon='🌐')
