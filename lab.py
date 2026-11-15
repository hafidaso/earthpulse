"""EarthPulse — The Climate Evidence Lab (default English first-visit experience).

Every number, verdict and sentence below is derived at runtime from the bundled,
unaltered NASA POWER / MERRA-2 snapshots via the tested functions in analysis.py.
Nothing is hard-coded.
"""
import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from analysis import (
    LOCATIONS,
    climate_trial,
    compare_locations,
    evaluate_site,
    format_bound,
    format_interval,
)
from brief_pdf import build_scientific_evidence_brief_pdf

START, END = 1991, 2025
INK, MUTED, TEAL, OCHRE, PAPER, CHART_BG = '#14282d', '#3c5358', '#15616d', '#b55327', '#f5f2eb', '#f9f7f2'
RATE_UNIT = {'T2M': '°C/decade', 'PRECTOTCORR': 'mm/yr per decade'}
VAR_NAME = {'T2M': 'air temperature at 2 m', 'PRECTOTCORR': 'annual precipitation'}

st.markdown(
    """<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');
.stApp { background: #f5f2eb; color: #14282d; }
.block-container { max-width: 1180px; padding-top: 3.2rem !important; padding-bottom: 3rem !important; }
html, body, p, li, label, button, div { font-family: 'Inter', system-ui, sans-serif; }
.lab-kicker { font-size: 0.78rem; letter-spacing: 0.16em; text-transform: uppercase; color: #15616d; font-weight: 700; margin-bottom: 0.35rem; }
.lab-hero { font-family: 'Fraunces', Georgia, serif; font-size: clamp(2.1rem, 4.6vw, 3.5rem); line-height: 1.06; color: #14282d; margin: 0 0 0.6rem 0; text-wrap: balance; font-weight: 700; }
.lab-sub { font-size: 1.12rem; color: #2f474d; max-width: 46rem; line-height: 1.55; margin-bottom: 1.1rem; text-wrap: pretty; }
.lab-strip { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-bottom: 1.4rem; }
.lab-chip { font-size: 0.78rem; color: #2f474d; background: #e7e2d5; border-radius: 999px; padding: 0.2rem 0.75rem; }
.case-num { font-size: 0.72rem; letter-spacing: 0.14em; color: #b55327; font-weight: 700; }
.case-title { font-family: 'Fraunces', Georgia, serif; font-size: 1.3rem; color: #14282d; margin: 0.15rem 0 0.35rem 0; font-weight: 700; }
.case-q { font-size: 0.95rem; color: #2f474d; line-height: 1.5; min-height: 3em; }
div[data-testid="stVerticalBlockBorderWrapper"] { transition: transform 160ms ease, box-shadow 160ms ease; border-radius: 10px; }
div[data-testid="stVerticalBlockBorderWrapper"]:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(20,40,45,0.08); }
.case-stage { font-family: 'Fraunces', Georgia, serif; font-size: clamp(1.5rem, 3vw, 2.15rem); color: #14282d; line-height: 1.15; margin: 0.2rem 0 0.4rem 0; text-wrap: balance; }
.reveal { animation: epFade 520ms ease both; }
@keyframes epFade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { .reveal { animation: none; } div[data-testid="stVerticalBlockBorderWrapper"]:hover { transform: none; } }
.verdict { border-radius: 10px; padding: 1rem 1.15rem; margin: 0.3rem 0 0.8rem 0; border-inline-start: 6px solid; }
.verdict-yes { background: #f6e6dc; border-color: #b55327; }
.verdict-inc { background: #e4ecec; border-color: #15616d; }
.verdict-label { font-size: 0.75rem; letter-spacing: 0.12em; text-transform: uppercase; font-weight: 700; color: #3c5358; }
.verdict-head { font-family: 'Fraunces', Georgia, serif; font-size: 1.45rem; color: #14282d; margin: 0.15rem 0 0.35rem 0; }
.verdict p { margin: 0.2rem 0; color: #14282d; line-height: 1.55; max-width: 75ch; }
.caveat { font-size: 0.9rem; color: #2f474d; background: #faf8f3; border: 1px dashed #c9c1ad; border-radius: 8px; padding: 0.65rem 0.9rem; margin: 0.4rem 0 0.8rem 0; }
.num { font-variant-numeric: tabular-nums; white-space: nowrap; font-weight: 600; }
.foot { font-size: 0.8rem; color: #3c5358; border-top: 1px solid #d6d0c2; padding-top: 0.7rem; margin-top: 2rem; }
</style>""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_snapshot(city):
    return json.loads((Path(__file__).parent / 'data' / f'{city.lower()}.json').read_text())


def zero_whisker(rows, rate_unit, height=280):
    """rows: list of (label, slope, ci, color, symbol). Draws intervals against the zero line."""
    fig = go.Figure()
    for i, (label, slope, ci, color, symbol) in enumerate(rows):
        fig.add_trace(go.Scatter(
            x=[slope], y=[label], mode='markers', showlegend=False,
            marker=dict(size=12, color=color, symbol=symbol),
            error_x=dict(type='data', symmetric=False, array=[ci[1] - slope], arrayminus=[slope - ci[0]], color=color, thickness=3, width=7),
            hovertemplate=f'<b>{label}</b><br>slope {slope:+.3f} {rate_unit}<br>95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]<extra></extra>',
        ))
    fig.add_vline(x=0, line_width=2, line_color=INK)
    fig.add_annotation(x=0, y=1.08, yref='paper', text='zero = no trend', showarrow=False, font=dict(size=11, color=MUTED))
    fig.update_layout(
        height=height, margin=dict(l=10, r=20, t=30, b=40), paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(family='Inter, sans-serif', color=INK, size=13),
        xaxis=dict(title=f'Trend ({rate_unit}) with 95% interval', gridcolor='#e3ded2', zeroline=False),
        yaxis=dict(autorange='reversed', gridcolor='#ece8de'),
    )
    return fig


def prediction_block(case_key, options):
    return st.radio(
        'Before you look — what do you predict? (optional)',
        options, index=None, horizontal=True, key=f'pred_{case_key}',
    )


def prediction_feedback(pred, options, correct_idx):
    if pred is None:
        return
    if options.index(pred) == correct_idx:
        st.success(f'Your prediction ("{pred}") matches what the NASA data supports.')
    else:
        st.info(f'You predicted "{pred}". The evidence points to: "{options[correct_idx]}". That gap is exactly why we test claims.')


def evidence_footer(case_key, pdf_bytes, pdf_name):
    c1, c2, c3 = st.columns([1.2, 1, 1])
    c1.download_button('Download Evidence Passport (PDF)', data=pdf_bytes, file_name=pdf_name, mime='application/pdf',
                       type='primary', use_container_width=True, key=f'pdf_{case_key}')
    with c2:
        st.page_link('expert_en.py', label='Open full Expert Analysis →', icon='🔬')
    with c3:
        st.page_link('expert_ar.py', label='التحليل المتقدم بالعربية', icon='🌐')


# ---------------------------------------------------------------- hero
st.markdown('<div class="lab-kicker">EarthPulse · The Climate Evidence Lab · NASA Space Apps 2026</div>', unsafe_allow_html=True)
st.markdown('<h1 class="lab-hero">The climate tells a story. Can you prove it?</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="lab-sub">Investigate NASA climate data. Challenge statistical claims. '
    'Discover what the evidence really supports.</p>'
    '<div class="lab-strip"><span class="lab-chip">NASA POWER · MERRA-2 monthly data</span>'
    '<span class="lab-chip">4 Moroccan grid cells · 1991–2025 · 35 complete years</span>'
    '<span class="lab-chip">OLS vs. Newey–West HAC uncertainty</span>'
    '<span class="lab-chip">Exploratory analysis · not a forecast</span></div>',
    unsafe_allow_html=True,
)

CASES = [
    ('case1', 'CASE 001', 'The Two Cities', 'Is Marrakech warming faster than Casablanca?'),
    ('case2', 'CASE 002', 'The False Certainty', 'Can ignoring time dependence change a climate verdict?'),
    ('case3', 'CASE 003', 'The Rainfall Question', 'Can we establish a rainfall trend in these cities?'),
]
st.session_state.setdefault('lab_case', None)


def _open(case_key):
    st.session_state['lab_case'] = case_key


cols = st.columns(3)
for col, (key, num, title, q) in zip(cols, CASES):
    with col:
        with st.container(border=True):
            st.markdown(f'<div class="case-num">{num}</div><div class="case-title">{title}</div><div class="case-q">{q}</div>', unsafe_allow_html=True)
            active = st.session_state['lab_case'] == key
            st.button('Investigating ✓' if active else 'Open case →', key=f'open_{key}', on_click=_open, args=(key,),
                      type='primary' if active else 'secondary', use_container_width=True)

case = st.session_state['lab_case']
if case is None:
    st.caption('Choose a case to begin. Each one takes under a minute, and every result is computed live from the bundled NASA files.')

# ---------------------------------------------------------------- CASE 001
if case == 'case1':
    casa, marr = load_snapshot('Casablanca'), load_snapshot('Marrakech')
    trial = climate_trial('Casablanca', casa, 'Marrakech', marr, parameter='T2M', start=START, end=END)
    comp = compare_locations('Casablanca', casa, 'Marrakech', marr, parameter='T2M', start=START, end=END)
    opts = ['Yes — significantly faster', 'No — significantly slower', "The data can't tell"]
    correct = {'positive_difference': 0, 'negative_difference': 1}.get(trial['verdict_code'], 2)

    st.markdown('<div class="case-num" style="margin-top:1.4rem;">CASE 001 · THE TWO CITIES</div>'
                '<div class="case-stage">Is Marrakech warming faster than Casablanca?</div>', unsafe_allow_html=True)
    st.write('Both cities warmed between 1991 and 2025. The real question is whether the gap between their warming rates '
             'is larger than year-to-year noise. EarthPulse tests the difference directly: it subtracts the two annual '
             'series year by year, D(year) = Marrakech − Casablanca, and asks whether that difference has a trend.')
    pred = prediction_block('case1', opts)
    if st.button('Reveal the evidence', key='rev_case1', type='primary'):
        st.session_state['revealed_case1'] = True

    if st.session_state.get('revealed_case1'):
        dr = trial['diff_result']
        ra, rb = trial['aligned_site_a_result'], trial['aligned_site_b_result']
        ci = trial['active_ci']
        st.markdown('<div class="reveal">', unsafe_allow_html=True)
        left, right = st.columns([1.25, 1])
        with left:
            m = trial['merged']
            fig = go.Figure()
            fig.add_trace(go.Bar(x=m['year'], y=m['diff'], marker_color=[OCHRE if v > 0 else TEAL for v in m['diff']],
                                 name='D(year) = Marrakech − Casablanca', hovertemplate='%{x}: %{y:+.2f} °C<extra></extra>'))
            fig.add_trace(go.Scatter(x=m['year'], y=m['fitted_diff'], mode='lines', line=dict(color=INK, width=3),
                                     name=f'Trend of the gap: {format_bound(dr["slope_decade"])} °C/decade'))
            fig.add_hline(y=0, line_width=1.5, line_color=MUTED)
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                              legend=dict(orientation='h', y=-0.18), yaxis_title='Gap (°C)', font=dict(family='Inter, sans-serif', color=INK))
            st.plotly_chart(fig, use_container_width=True)
        with right:
            st.plotly_chart(zero_whisker([
                ('Casablanca alone', ra['slope_decade'], ra['ci95'], TEAL, 'circle'),
                ('Marrakech alone', rb['slope_decade'], rb['ci95'], OCHRE, 'diamond'),
                ('The gap (B − A)', dr['slope_decade'], ci, INK, 'star'),
            ], '°C/decade', height=320), use_container_width=True)

        decisive = trial['verdict_code'] in ('positive_difference', 'negative_difference')
        direction = 'faster' if trial['verdict_code'] == 'positive_difference' else 'slower'
        head = (f'Yes, the evidence supports it: Marrakech is warming {direction} than Casablanca.' if decisive
                else 'Inconclusive: the data cannot settle this claim.')
        st.markdown(
            f'<div class="verdict {"verdict-yes" if decisive else "verdict-inc"}">'
            f'<div class="verdict-label">Computed verdict · cautious max(SE_OLS, SE_HAC) interval</div>'
            f'<div class="verdict-head">{head}</div>'
            f'<p>The warming gap grows by <span class="num">{format_bound(dr["slope_decade"])} °C/decade</span> '
            f'(95% interval <span class="num">{format_interval(ci, "")}</span>, exploratory p = <span class="num">{trial["active_p"]:.2g}</span>, '
            f'{trial["n_paired"]} paired years).</p>'
            f'<p>Notice the trap: the two single-city intervals overlap, which tempts people to say "no difference". '
            f'Pairing years cancels weather both cities share (correlation r = <span class="num">{trial["residual_correlation"]:+.2f}</span>), '
            f'so the test of the gap is far sharper than comparing two separate intervals.</p></div>',
            unsafe_allow_html=True,
        )
        prediction_feedback(pred, opts, correct)
        st.markdown('<div class="caveat"><b>What this does not show:</b> these are ~50 km reanalysis grid cells, not city weather stations, '
                    'and the analysis is exploratory (no correction for testing many pairs). '
                    'An inconclusive result would mean "not established", never "proven equal".</div>', unsafe_allow_html=True)
        pdf = build_scientific_evidence_brief_pdf(
            question='Is Marrakech warming faster than Casablanca?', parameter='T2M', start=START, end=END,
            loc_a='Casablanca', lat_a=LOCATIONS['Casablanca'][0], lon_a=LOCATIONS['Casablanca'][1], data_a=casa,
            loc_b='Marrakech', lat_b=LOCATIONS['Marrakech'][0], lon_b=LOCATIONS['Marrakech'][1], data_b=marr,
            trial=trial, comp=comp, interval_mode='cautious')
        evidence_footer('case1', pdf, f'earthpulse_case001_Casablanca_Marrakech_T2M_{START}_{END}.pdf')
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- CASE 002
if case == 'case2':
    city_options = ['Casablanca', 'Marrakech', 'Rabat', 'Ouarzazate']
    st.markdown('<div class="case-num" style="margin-top:1.4rem;">CASE 002 · THE FALSE CERTAINTY</div>'
                '<div class="case-stage">Can ignoring time dependence change a climate verdict?</div>', unsafe_allow_html=True)
    st.write('Standard regression (OLS) treats every year as independent. But warm years tend to follow warm years. '
             'When that "memory" is ignored, uncertainty is understated and a trend can look more certain than it is. '
             'Newey–West HAC standard errors account for it.')
    city = st.selectbox('Grid cell to investigate', city_options, index=0, key='case2_city')
    site = evaluate_site(city, load_snapshot(city), 'T2M', START, END)
    res = site['result']
    opts = ['Yes — the verdict flips', 'No — the verdict holds']
    correct = 0 if site['time_dependence_changes_verdict'] else 1
    pred = prediction_block(f'case2_{city}', opts)
    if st.button('Reveal the evidence', key='rev_case2', type='primary'):
        st.session_state['revealed_case2'] = True

    if st.session_state.get('revealed_case2'):
        st.markdown('<div class="reveal">', unsafe_allow_html=True)
        left, right = st.columns([1.2, 1])
        with left:
            st.plotly_chart(zero_whisker([
                ('OLS (years independent)', res['slope_decade'], res['iid_ci95'], MUTED, 'circle-open'),
                ('Newey–West HAC (cautious)', res['slope_decade'], res['ci95'], OCHRE, 'circle'),
            ], '°C/decade', height=260), use_container_width=True)
        with right:
            st.metric('Warming trend', f'{format_bound(res["slope_decade"])} °C/decade')
            st.metric('Year-to-year residual memory ρ₁', f'{res["residual_lag1"]:+.2f}')
            st.metric('SE_HAC / SE_OLS', f'{res["hac_to_ols_se_ratio"]:.2f}×',
                      help='Relative change in the estimated standard error. It is NOT a Type-I error or false-positive rate.')
        flips = site['time_dependence_changes_verdict']
        ols_txt = 'excludes zero' if site['iid_excludes_zero'] else 'crosses zero'
        hac_txt = 'excludes zero' if site['cautious_excludes_zero'] else 'crosses zero'
        head = (f'Yes. In {city}, accounting for time dependence turns a "significant" warming trend into an inconclusive one.' if flips
                else f'No. In {city}, the verdict is the same under both assumptions.')
        st.markdown(
            f'<div class="verdict {"verdict-yes" if flips else "verdict-inc"}">'
            f'<div class="verdict-label">Computed from {res["n"]} complete years, {START}–{END}</div>'
            f'<div class="verdict-head">{head}</div>'
            f'<p>OLS interval <span class="num">{format_interval(res["iid_ci95"], "")}</span> {ols_txt}. '
            f'The cautious HAC interval <span class="num">{format_interval(res["ci95"], "")}</span> {hac_txt}.</p>'
            f'<p>The estimated trend is identical in both cases. Only our honesty about uncertainty changes.</p></div>',
            unsafe_allow_html=True,
        )
        prediction_feedback(pred, opts, correct)
        st.markdown('<div class="caveat"><b>Read carefully:</b> an interval that crosses zero means the warming trend is <i>not established</i> '
                    'with this record. It is not evidence that the climate is stable. With only ~35 annual values, HAC estimates themselves are uncertain. '
                    'Try Marrakech or Ouarzazate to see a trend that survives both lenses.</div>', unsafe_allow_html=True)
        lat, lon = LOCATIONS[city]
        pdf = build_scientific_evidence_brief_pdf(
            question=f'Does ignoring time dependence change the warming verdict for {city}?', parameter='T2M', start=START, end=END,
            loc_a=city, lat_a=lat, lon_a=lon, data_a=load_snapshot(city), single_site=site, interval_mode='cautious')
        evidence_footer('case2', pdf, f'earthpulse_case002_{city}_T2M_{START}_{END}.pdf')
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- CASE 003
if case == 'case3':
    cities = ['Casablanca', 'Rabat', 'Marrakech', 'Ouarzazate']
    st.markdown('<div class="case-num" style="margin-top:1.4rem;">CASE 003 · THE RAINFALL QUESTION</div>'
                '<div class="case-stage">Can we establish a rainfall trend in these cities?</div>', unsafe_allow_html=True)
    st.write('Rainfall in Morocco swings wildly from one year to the next. A fitted line will always have some slope. '
             'The question is whether 35 years of NASA data are enough to separate a real trend from that variability.')
    opts = ['Yes — at least one city shows a clear trend', 'No — not established anywhere']
    sites = {c: evaluate_site(c, load_snapshot(c), 'PRECTOTCORR', START, END) for c in cities}
    clear = [c for c, s in sites.items() if s['eligible'] and s['cautious_excludes_zero']]
    correct = 0 if clear else 1
    pred = prediction_block('case3', opts)
    if st.button('Reveal the evidence', key='rev_case3', type='primary'):
        st.session_state['revealed_case3'] = True

    if st.session_state.get('revealed_case3'):
        st.markdown('<div class="reveal">', unsafe_allow_html=True)
        colors = [TEAL, TEAL, OCHRE, OCHRE]
        rows = [(c, s['result']['slope_decade'], s['result']['ci95'], col, 'circle') for (c, s), col in zip(sites.items(), colors) if s['eligible']]
        st.plotly_chart(zero_whisker(rows, RATE_UNIT['PRECTOTCORR'], height=300), use_container_width=True)
        if clear:
            head = f'A trend is established in {len(clear)} of {len(rows)} cells: {", ".join(clear)}.'
        else:
            head = f'Not established: all {len(rows)} rainfall intervals cross zero.'
        detail = ' · '.join(f'{c}: <span class="num">{format_bound(s["result"]["slope_decade"])}</span> '
                            f'<span class="num">{format_interval(s["result"]["ci95"], "")}</span>' for c, s in sites.items() if s['eligible'])
        st.markdown(
            f'<div class="verdict {"verdict-yes" if clear else "verdict-inc"}">'
            f'<div class="verdict-label">Computed verdict · mm/yr per decade · cautious 95% intervals</div>'
            f'<div class="verdict-head">{head}</div><p>{detail}</p>'
            f'<p>This is the most important lesson in the lab: <b>inconclusive is not the same as "no change"</b>. '
            f'Rainfall may well be changing; this record is simply too short and too noisy to prove it either way.</p></div>',
            unsafe_allow_html=True,
        )
        prediction_feedback(pred, opts, correct)
        st.markdown('<div class="caveat"><b>Limits:</b> four cells were screened without multiple-testing correction; NASA POWER precipitation '
                    'is a corrected reanalysis product (PRECTOTCORR), not rain-gauge totals.</div>', unsafe_allow_html=True)
        pick = st.selectbox('Evidence Passport for', cities, index=2, key='case3_pdf_city')
        lat, lon = LOCATIONS[pick]
        pdf = build_scientific_evidence_brief_pdf(
            question=f'Can we establish an annual rainfall trend in {pick}?', parameter='PRECTOTCORR', start=START, end=END,
            loc_a=pick, lat_a=lat, lon_a=lon, data_a=load_snapshot(pick), single_site=sites[pick], interval_mode='cautious')
        evidence_footer('case3', pdf, f'earthpulse_case003_{pick}_PRECTOTCORR_{START}_{END}.pdf')
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="foot">Data: NASA POWER Monthly &amp; Annual API (MERRA-2 meteorology; T2M, PRECTOTCORR), bundled unaltered with SHA-256 '
    'checksums in every Evidence Passport. Method: day-weighted annual means, OLS trend, Newey–West HAC and a cautious '
    'max(SE_OLS, SE_HAC) interval; at least 30 consecutive complete years required. Exploratory analysis; not affiliated with or endorsed by NASA.</div>',
    unsafe_allow_html=True,
)
