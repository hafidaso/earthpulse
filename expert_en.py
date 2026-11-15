"""EarthPulse — Expert Analysis (English): Climate Trial, Trend Verdict and single-site tools."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from analysis import (
    LOCATIONS,
    MERRA2_LAT_RES_DEG,
    MERRA2_LON_RES_DEG,
    VARIABLES,
    annual_series,
    climate_trial,
    compare_locations,
    evaluate_site,
    excludes_zero,
    extract_grid_metadata,
    fetch_power,
    format_bound,
    format_interval,
    source_sha256,
    trend,
    uncertainty_lens_summary,
)
from brief_pdf import build_scientific_evidence_brief_pdf


st.markdown(
    """<style>
.stApp {
    background-color: #f5f2eb;
    color: #14282d;
}
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 2.2rem !important;
}
.block-container {
    max-width: 1380px;
    padding-top: 3.05rem !important;
    padding-bottom: 2.5rem !important;
}
h1, h2, h3, .editorial-headline, .step-title {
    font-family: Georgia, "Times New Roman", serif !important;
    color: #14282d;
    letter-spacing: -0.025em;
    text-wrap: balance;
}
.eyebrow-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    border-bottom: 1px solid #d6d0c2;
    padding-bottom: 0.35rem;
    margin-bottom: 0.45rem;
}
.eyebrow {
    letter-spacing: 0.14em;
    font-size: 0.78rem;
    color: #15616d;
    font-weight: 700;
    text-transform: uppercase;
}
.provenance-badge {
    font-size: 0.8rem;
    color: #2f474d;
    background: #e7e2d5;
    padding: 0.15rem 0.65rem;
    border-radius: 999px;
    border: 1px solid #d0c9b8;
    font-weight: 500;
}
.editorial-headline {
    font-size: clamp(1.65rem, 1.15rem + 2vw, 2.35rem);
    line-height: 1.15;
    font-weight: 700;
    margin: 0.1rem 0 0.3rem 0;
    color: #14282d;
}
.verdict-lead, .trial-subq, .evidence-panel p, .step-banner-sub {
    line-height: 1.5;
    color: #243b40;
    max-width: 75ch;
    text-wrap: pretty;
    overflow-wrap: break-word;
}
.verdict-lead {
    font-size: 1.02rem;
    margin: 0 0 0.65rem 0;
}
.step-ribbon {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.65rem;
    margin: 0.35rem 0 0.75rem 0;
}
.step-card {
    background: #ece8de;
    border: 1px solid #d0c9b8;
    border-left: 4px solid #15616d;
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
}
.step-card-num {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #15616d;
}
.step-card-q {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 0.96rem;
    font-weight: 700;
    color: #14282d;
    margin: 0.08rem 0;
}
.step-card-desc {
    font-size: 0.8rem;
    color: #2f474d;
    line-height: 1.38;
}
.step-banner {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.45rem;
    border-top: 2px solid #d0c9b8;
    padding-top: 0.7rem;
    margin: 0.95rem 0 0.45rem 0;
}
.step-banner-kicker {
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #b55327;
}
.step-title {
    font-size: 1.28rem;
    font-weight: 700;
    margin: 0.05rem 0 0.15rem 0;
}
.step-banner-sub {
    font-size: 0.92rem;
    margin: 0 0 0.45rem 0;
}
.reality-callout {
    background: #f9f7f2;
    border: 1px solid #d6d0c2;
    border-left: 4px solid #b55327;
    border-radius: 6px;
    padding: 0.65rem 0.85rem;
    margin: 0.35rem 0 0.5rem 0;
    font-size: 0.86rem;
    color: #243b40;
    line-height: 1.46;
}
.passport-hero {
    background: #ece8de;
    border: 1px solid #cbc3b2;
    border-left: 5px solid #14282d;
    border-radius: 8px;
    padding: 0.9rem 1.05rem;
    margin: 0.45rem 0 0.65rem 0;
}
.chart-header-box {
    background: #ece8de;
    border: 1px solid #d6d0c2;
    border-bottom: 0;
    border-radius: 6px 6px 0 0;
    padding: 0.5rem 0.85rem;
    margin-top: 0.15rem;
}
.chart-header-title {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1.02rem;
    font-weight: 700;
    color: #14282d;
    margin: 0;
}
.chart-header-sub {
    font-size: 0.82rem;
    color: #42595f;
    margin: 0.1rem 0 0 0;
}
div[data-testid="stPlotlyChart"] {
    background: #f9f7f2;
    border: 1px solid #d6d0c2;
    border-radius: 0 0 6px 6px;
    padding: 0.15rem 0.25rem 0.1rem 0.25rem;
    margin-bottom: 0.45rem;
}
.evidence-panel {
    background: #ece8de;
    border: 1px solid #d6d0c2;
    border-left: 4px solid #15616d;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    margin-top: 0.25rem;
    margin-bottom: 0.75rem;
}
.evidence-panel h4 {
    font-family: Georgia, serif !important;
    font-size: 1.05rem;
    margin: 0 0 0.35rem 0;
    color: #14282d;
}
.evidence-panel p {
    font-size: 0.91rem;
    line-height: 1.46;
    color: #243b40;
    margin: 0.25rem 0 0.5rem 0;
}
.verdict-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.87rem;
    margin: 0.35rem 0 0.45rem 0;
    background: #faf8f3;
    border: 1px solid #d6d0c2;
}
.verdict-table th {
    text-align: left;
    padding: 0.45rem 0.65rem;
    background: #e4dfd1;
    color: #14282d;
    font-weight: 600;
    border-bottom: 1px solid #cbc3b2;
}
.verdict-table td {
    padding: 0.45rem 0.65rem;
    border-bottom: 1px solid #e4dfd2;
    color: #1c3338;
    vertical-align: middle;
}
.badge-clear {
    display: inline-block;
    background: #f6e3d8;
    color: #8a350f;
    border: 1px solid #d99b7e;
    font-weight: 600;
    font-size: 0.78rem;
    padding: 0.08rem 0.45rem;
    border-radius: 4px;
    margin-left: 0.25rem;
}
.badge-cautious {
    display: inline-block;
    background: #dcebed;
    color: #124e57;
    border: 1px solid #8eb8be;
    font-weight: 600;
    font-size: 0.78rem;
    padding: 0.08rem 0.45rem;
    border-radius: 4px;
    margin-left: 0.25rem;
}
.badge-ineligible {
    display: inline-block;
    background: #f5e6c8;
    color: #6e4b0c;
    border: 1px solid #d4b475;
    font-weight: 600;
    font-size: 0.78rem;
    padding: 0.08rem 0.45rem;
    border-radius: 4px;
}
.caveat-strip {
    font-size: 0.85rem;
    color: #324a50;
    background: #e4dfd1;
    padding: 0.45rem 0.75rem;
    border-radius: 4px;
    margin-top: 0.4rem;
}
.trial-tagline {
    font-size: 0.96rem;
    color: #15616d;
    font-weight: 600;
    letter-spacing: 0.02em;
    margin: 0 0 0.2rem 0;
}
.trial-subq {
    font-size: 1.03rem;
    color: #243b40;
    line-height: 1.45;
    margin: 0 0 0.75rem 0;
}
.city-card {
    background: #faf8f3;
    border: 1px solid #d6d0c2;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    min-height: 100%;
}
.city-card-a {
    border-top: 4px solid #15616d;
}
.city-card-b {
    border-top: 4px solid #b55327;
}
.city-card-kicker {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #485e64;
    margin-bottom: 0.15rem;
}
.city-card-name {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #14282d;
    margin-bottom: 0.25rem;
}
.city-card-rate {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1.55rem;
    font-weight: 700;
    margin: 0.2rem 0 0.3rem 0;
}
.city-card-meta {
    font-size: 0.84rem;
    color: #334a50;
    line-height: 1.42;
}
.vs-card {
    background: #ece8de;
    border: 1px solid #cbc3b2;
    border-radius: 8px;
    padding: 0.85rem 0.9rem;
    text-align: center;
}
.vs-pill {
    display: inline-block;
    background: #14282d;
    color: #f5f2eb;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.18rem 0.6rem;
    border-radius: 999px;
    margin-bottom: 0.35rem;
}
.vs-prompt {
    font-size: 0.85rem;
    color: #243b40;
    line-height: 1.38;
    margin: 0.2rem 0 0.45rem 0;
}
.verdict-banner {
    background: #faf8f3;
    border: 1px solid #cbc3b2;
    border-radius: 8px;
    padding: 0.95rem 1.15rem;
    margin: 0.55rem 0 0.75rem 0;
}
.verdict-positive {
    border-left: 6px solid #b55327;
}
.verdict-negative {
    border-left: 6px solid #15616d;
}
.verdict-inconclusive {
    border-left: 6px solid #6b7274;
}
.verdict-ineligible {
    border-left: 6px solid #b88b2e;
}
.verdict-pill-pos {
    display: inline-block;
    background: #f6e3d8;
    color: #8a350f;
    border: 1px solid #d99b7e;
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.16rem 0.65rem;
    border-radius: 4px;
}
.verdict-pill-neg {
    display: inline-block;
    background: #dcebed;
    color: #124e57;
    border: 1px solid #8eb8be;
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.16rem 0.65rem;
    border-radius: 4px;
}
.verdict-pill-inc {
    display: inline-block;
    background: #e7e5df;
    color: #38494c;
    border: 1px solid #b5b0a4;
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.16rem 0.65rem;
    border-radius: 4px;
}
.verdict-pill-warn {
    display: inline-block;
    background: #f5e6c8;
    color: #6e4b0c;
    border: 1px solid #d4b475;
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.16rem 0.65rem;
    border-radius: 4px;
}
.trial-metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.65rem;
    margin: 0.6rem 0 0.55rem 0;
}
.trial-metric-box {
    background: #f1eee5;
    border: 1px solid #d8d1c2;
    border-radius: 6px;
    padding: 0.5rem 0.7rem;
}
.trial-metric-label {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #465c62;
    font-weight: 600;
}
.trial-metric-value {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1.18rem;
    font-weight: 700;
    color: #14282d;
    margin-top: 0.1rem;
}
.trial-metric-sub {
    font-size: 0.76rem;
    color: #4e6368;
}
.table-wrapper {
    overflow: auto;
    max-inline-size: 100%;
    max-block-size: 320px;
    border: 1px solid #d6d0c2;
    border-radius: 6px;
    background: #faf8f3;
}
.table-wrapper.table-wrapper-auto {
    max-block-size: none;
    overflow-y: visible;
    overflow-x: auto;
}
.table-wrapper table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.84rem;
}
.table-wrapper thead th {
    position: sticky;
    inset-block-start: 0;
    z-index: 2;
    background: #e4dfd1;
    color: #14282d;
    padding: 0.45rem 0.6rem;
    text-align: right;
    border-bottom: 1px solid #cbc3b2;
}
.table-wrapper thead th:first-child {
    text-align: left;
}
.table-wrapper tbody td {
    padding: 0.36rem 0.6rem;
    text-align: right;
    border-bottom: 1px solid #ebe6da;
    color: #1e353a;
    font-variant-numeric: tabular-nums;
}
.table-wrapper tbody td:first-child {
    text-align: left;
    font-weight: 600;
}
@keyframes trialReveal {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
@media (prefers-reduced-motion: no-preference) {
    .trial-reveal-panel {
        animation: trialReveal 0.55s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
}
[data-testid="stSidebar"] {
    background-color: #e8e4d8;
}
[data-testid="stMetricValue"] {
    color: #15616d;
    font-family: Georgia, serif;
    font-size: 2.0rem;
}
.stButton > button, .stDownloadButton > button {
    background-color: #15616d;
    color: #ffffff;
    border: 1px solid transparent;
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    background-color: #b55327;
    color: #ffffff;
    font-weight: 700;
    letter-spacing: 0.04em;
    padding: 0.55rem 1.1rem;
    border-radius: 6px;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
    background-color: #96411c;
    color: #ffffff;
}
a {
    color: #15616d;
}
@media (forced-colors: active) {
    .city-card, .verdict-banner, .evidence-panel, .step-card, .reality-callout, .passport-hero,
    .stButton > button, .stDownloadButton > button {
        border: 1px solid ButtonText !important;
    }
}
@media (max-width: 768px) {
    .block-container {
        padding-top: 2.2rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
    .editorial-headline {
        font-size: 1.5rem;
    }
    .verdict-lead {
        font-size: 0.94rem;
    }
    .trial-metrics-grid, .step-ribbon {
        grid-template-columns: minmax(0, 1fr);
    }
    .verdict-table {
        font-size: 0.78rem;
        display: block;
        overflow-x: auto;
    }
}
</style>""",
    unsafe_allow_html=True,
)

SITE_A_COLOR = '#15616d'  # Deep Atlantic teal
SITE_B_COLOR = '#b55327'  # Warm Atlas ochre
INK_COLOR = '#14282d'
CHART_BG = '#f9f7f2'


@st.cache_data(ttl=86400, show_spinner=False)
def load_live(lat, lon, start, end):
    return fetch_power(lat, lon, start, end)


def load_location_data(location, lat, lon, start, end, mode):
    """Load bundled NASA snapshot when eligible (1991-2025 for the 4 example sites) or query live NASA POWER API."""
    snapshot = Path(__file__).parent / 'data' / f'{location.lower()}.json'
    is_bundled = (
        mode.startswith('Verified')
        and location in LOCATIONS
        and start >= 1991
        and end <= 2025
        and snapshot.exists()
    )
    if is_bundled:
        return json.loads(snapshot.read_text()), True
    return load_live(lat, lon, start, end), False


def build_comparison_series_figure(comp):
    """Build aligned annual series chart with shared year axis, shared value scale, distinct markers/lines, and fits."""
    site_a = comp['site_a']
    site_b = comp['site_b']
    unit = comp['unit']
    var_name = comp['variable_name']
    fa, fb = site_a['frame'], site_b['frame']
    ra, rb = site_a['result'], site_b['result']

    fig = go.Figure()

    if not fa.empty:
        fig.add_trace(
            go.Scatter(
                x=fa['year'],
                y=fa['value'],
                mode='lines+markers',
                name=f"● {site_a['location']} annual ({len(fa)} yr)",
                line=dict(color=SITE_A_COLOR, width=2.0, dash='solid'),
                marker=dict(symbol='circle', size=5.5, color=SITE_A_COLOR),
                hovertemplate=f"<b>{site_a['location']}</b> (%{{x}}): %{{y:.2f}} {unit}<extra></extra>",
            )
        )
    if ra is not None:
        fig.add_trace(
            go.Scatter(
                x=fa['year'],
                y=ra['fitted'],
                mode='lines',
                name=f"● {site_a['location']} fit ({format_bound(ra['slope_decade'])} {unit}/dec)",
                line=dict(color=SITE_A_COLOR, width=3.2, dash='solid'),
                hovertemplate=f"<b>{site_a['location']} linear fit</b> (%{{x}}): %{{y:.2f}} {unit}<extra></extra>",
            )
        )

    if not fb.empty:
        fig.add_trace(
            go.Scatter(
                x=fb['year'],
                y=fb['value'],
                mode='lines+markers',
                name=f"◆ {site_b['location']} annual ({len(fb)} yr)",
                line=dict(color=SITE_B_COLOR, width=2.0, dash='dot'),
                marker=dict(symbol='diamond', size=6.0, color=SITE_B_COLOR),
                hovertemplate=f"<b>{site_b['location']}</b> (%{{x}}): %{{y:.2f}} {unit}<extra></extra>",
            )
        )
    if rb is not None:
        fig.add_trace(
            go.Scatter(
                x=fb['year'],
                y=rb['fitted'],
                mode='lines',
                name=f"◆ {site_b['location']} fit ({format_bound(rb['slope_decade'])} {unit}/dec)",
                line=dict(color=SITE_B_COLOR, width=3.2, dash='dash'),
                hovertemplate=f"<b>{site_b['location']} linear fit</b> (%{{x}}): %{{y:.2f}} {unit}<extra></extra>",
            )
        )

    fig.update_layout(
        height=310,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family='Arial, sans-serif', color=INK_COLOR, size=12),
        margin=dict(l=48, r=18, t=42, b=38),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.03,
            xanchor='left',
            x=0.0,
            font=dict(size=11.2),
            bgcolor='rgba(249,247,242,0.0)',
        ),
        xaxis=dict(
            title='Calendar year (shared axis)',
            range=[comp['start'] - 0.6, comp['end'] + 0.6],
            gridcolor='#e3ded2',
            zeroline=False,
        ),
        yaxis=dict(
            title=f"{var_name} ({unit})",
            gridcolor='#e3ded2',
            zeroline=False,
        ),
        hovermode='x unified',
    )
    return fig


def build_whisker_figure(comp, lens_mode):
    """Build aligned dot-and-whisker slope plot with a prominent zero reference line and both uncertainty intervals."""
    site_a = comp['site_a']
    site_b = comp['site_b']
    rate_unit = comp['rate_unit']
    fig = go.Figure()

    fig.add_vline(
        x=0.0,
        line_width=2.5,
        line_dash='solid',
        line_color=INK_COLOR,
    )

    if not comp['both_eligible']:
        fig.add_annotation(
            x=0.0,
            y=0.5,
            xref='x',
            yref='paper',
            text=(
                "<b>Trend inference withheld</b><br>"
                "At least 30 consecutive complete annual values are required<br>"
                "to plot slope estimates and 95% confidence intervals."
            ),
            showarrow=False,
            font=dict(size=12.5, color=INK_COLOR, family='Georgia, serif'),
            bgcolor='#f5e6c8',
            bordercolor='#d4b475',
            borderwidth=1,
            borderpad=10,
        )
        fig.update_layout(
            height=310,
            template='plotly_white',
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            margin=dict(l=20, r=20, t=42, b=38),
            xaxis=dict(title=f"Estimated slope ({rate_unit})", range=[-1, 1], gridcolor='#e3ded2'),
            yaxis=dict(visible=False),
        )
        return fig

    sites = [
        (site_a, 1.0, SITE_A_COLOR, 'circle', '●'),
        (site_b, 0.0, SITE_B_COLOR, 'diamond', '◆'),
    ]

    show_cautious = lens_mode in ('both', 'cautious')
    show_iid = lens_mode in ('both', 'conventional')

    all_bounds = [0.0]
    for s, _, _, _, _ in sites:
        r = s['result']
        all_bounds.extend(r['ci95'])
        all_bounds.extend(r['iid_ci95'])

    span = max(all_bounds) - min(all_bounds)
    pad_left = max(span * 0.28, 0.10)
    pad_right = max(span * 0.36, 0.14)
    x_min = min(all_bounds) - pad_left
    x_max = max(all_bounds) + pad_right
    x_mid = 0.5 * (x_min + x_max)

    fig.add_annotation(
        x=0.0,
        y=0.48,
        xref='x',
        yref='y',
        text='<b>0.0 (Zero trend)</b>',
        showarrow=False,
        font=dict(size=11, color=INK_COLOR, family='Arial, sans-serif'),
        bgcolor='#e5e0d3',
        bordercolor='#b8b09c',
        borderwidth=1,
        borderpad=3,
    )

    active_mode = comp.get('interval_mode', 'cautious')
    primary_trace_name = (
        'Raw Newey–West HAC 95% CI (SE_HAC)'
        if active_mode == 'hac'
        else 'Cautious 95% CI (HAC / max SE)'
    )
    primary_hover_tag = (
        'Raw HAC 95% CI (SE_HAC)'
        if active_mode == 'hac'
        else 'Cautious 95% CI (HAC / max SE)'
    )

    for idx, (s, y_base, color, symbol, glyph) in enumerate(sites):
        r = s['result']
        slope = r['slope_decade']
        cautious_ci = r['ci95']
        iid_ci = r['iid_ci95']

        y_cautious = y_base + (0.10 if lens_mode == 'both' else 0.0)
        cautious_opacity = 1.0 if show_cautious else 0.25
        fig.add_trace(
            go.Scatter(
                x=[slope],
                y=[y_cautious],
                mode='markers',
                name=primary_trace_name,
                legendgroup='cautious',
                showlegend=(idx == 0),
                opacity=cautious_opacity,
                marker=dict(symbol=symbol, size=11, color=color, line=dict(width=1.5, color='#ffffff')),
                error_x=dict(
                    type='data',
                    symmetric=False,
                    array=[cautious_ci[1] - slope],
                    arrayminus=[slope - cautious_ci[0]],
                    color=color,
                    thickness=4.0,
                    width=7,
                ),
                hovertemplate=(
                    f"<b>{s['location']} · {primary_hover_tag}</b><br>"
                    f"Slope: {format_bound(slope)} {rate_unit}<br>"
                    f"Interval: {format_interval(cautious_ci, rate_unit)}<br>"
                    f"Status: {s['cautious_status']}<extra></extra>"
                ),
            )
        )

        y_iid = y_base - (0.12 if lens_mode == 'both' else 0.0)
        iid_opacity = 0.95 if show_iid else 0.22
        fig.add_trace(
            go.Scatter(
                x=[slope],
                y=[y_iid],
                mode='markers',
                name='Conventional 95% CI (OLS, independent years)',
                legendgroup='iid',
                showlegend=(idx == 0),
                opacity=iid_opacity,
                marker=dict(symbol=f"{symbol}-open", size=8.5, color='#455c61', line=dict(width=2, color='#455c61')),
                error_x=dict(
                    type='data',
                    symmetric=False,
                    array=[iid_ci[1] - slope],
                    arrayminus=[slope - iid_ci[0]],
                    color='#52696e',
                    thickness=2.0,
                    width=5,
                ),
                hovertemplate=(
                    f"<b>{s['location']} · Conventional 95% CI (OLS)</b><br>"
                    f"Slope: {format_bound(slope)} {rate_unit}<br>"
                    f"Interval: {format_interval(iid_ci, rate_unit)}<br>"
                    f"Status: {s['iid_status']}<extra></extra>"
                ),
            )
        )

        active_ci = iid_ci if lens_mode == 'conventional' else cautious_ci
        active_ex = s['iid_excludes_zero'] if lens_mode == 'conventional' else s['cautious_excludes_zero']
        verdict_tag = 'Excludes 0' if active_ex else 'Crosses 0'
        ci_center = 0.5 * (active_ci[0] + active_ci[1])
        label_x = 0.45 * ci_center + 0.55 * x_mid
        fig.add_annotation(
            x=label_x,
            y=y_base + 0.31,
            xref='x',
            yref='y',
            text=(
                f"<b>{glyph} {s['location']}: {format_bound(slope)}</b> "
                f"[{format_bound(active_ci[0])}, {format_bound(active_ci[1])} · <b>{verdict_tag}</b>]"
            ),
            showarrow=False,
            font=dict(size=10.8, color=color, family='Arial, sans-serif'),
            bgcolor='rgba(249,247,242,0.92)',
        )

    fig.update_layout(
        height=310,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family='Arial, sans-serif', color=INK_COLOR, size=12),
        margin=dict(l=98, r=18, t=42, b=38),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.03,
            xanchor='left',
            x=0.0,
            font=dict(size=11.2),
            bgcolor='rgba(249,247,242,0.0)',
        ),
        xaxis=dict(
            title=f"Estimated linear slope ({rate_unit})",
            range=[x_min, x_max],
            gridcolor='#e3ded2',
            zeroline=False,
        ),
        yaxis=dict(
            tickmode='array',
            tickvals=[0.0, 1.0],
            ticktext=[f"<b>◆ {site_b['location']}</b>", f"<b>● {site_a['location']}</b>"],
            range=[-0.38, 1.50],
            gridcolor='#ece8de',
        ),
    )
    return fig


def build_residual_persistence_figure(comp):
    """Build a side-by-side lag-1 residual persistence plot (e_{t-1} vs e_t) showing why HAC widens Casablanca's interval."""
    sa, sb = comp['site_a'], comp['site_b']
    unit = comp['unit']
    fig = go.Figure()
    for s, color, symbol, glyph in [(sa, SITE_A_COLOR, 'circle', '●'), (sb, SITE_B_COLOR, 'diamond', '◆')]:
        if not s['eligible']:
            continue
        frame = s['frame']
        res = s['result']
        residuals = frame['value'].to_numpy(dtype=float) - np.array(res['fitted'], dtype=float)
        if len(residuals) < 3:
            continue
        r_prev = residuals[:-1]
        r_curr = residuals[1:]
        years_curr = frame['year'].to_numpy()[1:]
        fig.add_trace(
            go.Scatter(
                x=r_prev,
                y=r_curr,
                mode='markers',
                name=f"{glyph} {s['location']} (ρ₁ = {res['residual_lag1']:+.2f})",
                marker=dict(symbol=symbol, size=8, color=color, opacity=0.85),
                text=years_curr,
                hovertemplate=(
                    f"<b>{s['location']}</b> (year %{{text}})<br>"
                    f"Prior year residual (eₜ₋₁): %{{x:+.2f}} {unit}<br>"
                    f"Current year residual (eₜ): %{{y:+.2f}} {unit}<extra></extra>"
                ),
            )
        )
        # Fit simple lag-1 line to visualize persistence slope
        if np.std(r_prev) > 1e-9:
            xs = np.linspace(float(r_prev.min()), float(r_prev.max()), 20)
            slope_ar1 = float(np.polyfit(r_prev, r_curr, 1)[0])
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=slope_ar1 * xs,
                    mode='lines',
                    name=f"{s['location']} AR(1) slope ({res['residual_lag1']:+.2f})",
                    line=dict(color=color, width=2.2, dash='solid' if glyph == '●' else 'dash'),
                    showlegend=False,
                )
            )
    fig.add_hline(y=0, line_width=1, line_dash='dot', line_color='#8c8576')
    fig.add_vline(x=0, line_width=1, line_dash='dot', line_color='#8c8576')
    fig.update_layout(
        height=290,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family='Arial, sans-serif', color=INK_COLOR, size=12),
        margin=dict(l=48, r=18, t=38, b=38),
        legend=dict(orientation='h', y=1.04, x=0.0),
        xaxis=dict(title=f"Prior year detrended residual eₜ₋₁ ({unit})", gridcolor='#e3ded2', zeroline=False),
        yaxis=dict(title=f"Current year detrended residual eₜ ({unit})", gridcolor='#e3ded2', zeroline=False),
    )
    return fig


def build_window_sensitivity_figure(loc_a, data_a, loc_b, data_b, parameter):
    """Evaluate all consecutive >=30-year windows ending in 2025 (start=1991..1996) and starting in 1991 (end=2020..2025)."""
    unit = VARIABLES[parameter][1]
    rate_unit = f"{unit}/decade"
    windows = [
        (1991, 2020),
        (1991, 2022),
        (1991, 2025),
        (1993, 2025),
        (1995, 2025),
        (1996, 2025),
    ]
    labels = [f"{s}–{e} ({e - s + 1}y)" for s, e in windows]
    fig = go.Figure()
    fig.add_hline(y=0.0, line_width=2.2, line_color=INK_COLOR)

    for loc, data, color, symbol, glyph, offset in [
        (loc_a, data_a, SITE_A_COLOR, 'circle', '●', -0.08),
        (loc_b, data_b, SITE_B_COLOR, 'diamond', '◆', +0.08),
    ]:
        slopes, err_plus, err_minus, valid_labels = [], [], [], []
        for (s_yr, e_yr), lbl in zip(windows, labels):
            ev = evaluate_site(loc, data, parameter, s_yr, e_yr)
            if ev['eligible']:
                r = ev['result']
                sl = r['slope_decade']
                ci = r['ci95']
                slopes.append(sl)
                err_plus.append(ci[1] - sl)
                err_minus.append(sl - ci[0])
                valid_labels.append(lbl)
        if slopes:
            fig.add_trace(
                go.Scatter(
                    x=valid_labels,
                    y=slopes,
                    mode='lines+markers',
                    name=f"{glyph} {loc} (cautious 95% CI)",
                    line=dict(color=color, width=2.2, dash='solid' if glyph == '●' else 'dash'),
                    marker=dict(symbol=symbol, size=9, color=color),
                    error_y=dict(
                        type='data',
                        symmetric=False,
                        array=err_plus,
                        arrayminus=err_minus,
                        color=color,
                        thickness=2.5,
                        width=5,
                    ),
                    hovertemplate=f"<b>{loc}</b> (%{{x}}): %{{y:+.2f}} {rate_unit}<extra></extra>",
                )
            )
    fig.update_layout(
        height=290,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family='Arial, sans-serif', color=INK_COLOR, size=12),
        margin=dict(l=48, r=18, t=38, b=38),
        legend=dict(orientation='h', y=1.04, x=0.0),
        xaxis=dict(title='30+ year consecutive window within bundled record', gridcolor='#e3ded2'),
        yaxis=dict(title=f"Slope ({rate_unit})", gridcolor='#e3ded2', zeroline=False),
    )
    return fig


def build_grid_reality_map(
    parameter,
    start=1991,
    end=2025,
    loc_a='Casablanca',
    data_a=None,
    lat_a=None,
    lon_a=None,
    loc_b='Marrakech',
    data_b=None,
    lat_b=None,
    lon_b=None,
    interval_mode='cautious',
):
    """Build an interactive geographic reality map showing cities, Atlas/Atlantic context, and approximate 0.5°x0.625° MERRA-2 footprints."""
    unit = VARIABLES[parameter][1]
    rate_unit = f"{unit}/decade"
    fig = go.Figure()

    # Check if custom locations extend beyond Morocco
    active_pts = []
    if lat_a is not None and lon_a is not None:
        active_pts.append((float(lat_a), float(lon_a)))
    if lat_b is not None and lon_b is not None:
        active_pts.append((float(lat_b), float(lon_b)))
    in_morocco = all(27.0 <= p_lat <= 37.5 and -14.5 <= p_lon <= -0.5 for p_lat, p_lon in active_pts)

    # Schematic physiographic Atlas Mountains terrain context (explicitly labeled non-DEM context)
    high_atlas_lats = [30.65, 31.10, 31.65, 32.25, 33.15, 33.75, 33.35, 32.00, 31.35, 30.85, 30.35, 30.65]
    high_atlas_lons = [-9.65, -8.50, -7.35, -5.85, -4.45, -3.55, -3.15, -4.95, -6.45, -7.85, -9.25, -9.65]
    fig.add_trace(
        go.Scattergeo(
            lat=high_atlas_lats,
            lon=high_atlas_lons,
            mode='lines',
            fill='toself',
            fillcolor='rgba(155, 128, 92, 0.22)',
            line=dict(color='rgba(122, 95, 62, 0.55)', width=1.4, dash='dot'),
            name='Atlas Mountains (schematic terrain context)',
            hovertemplate=(
                '<b>Atlas Mountains Corridor</b><br>'
                'Schematic High &amp; Middle Atlas terrain context.<br>'
                'Separates humid Atlantic coastal plains from semi-arid Haouz &amp; Pre-Saharan valleys.<extra></extra>'
            ),
        )
    )
    fig.add_trace(
        go.Scattergeo(
            lat=[32.95, 31.32],
            lon=[-10.45, -6.10],
            mode='text',
            text=['<i>Atlantic Ocean<br>(marine cooling)</i>', '<i>High Atlas Range<br>(schematic context)</i>'],
            textfont=dict(family='Georgia, serif', size=10.2, color='#455c61'),
            showlegend=False,
            hoverinfo='skip',
        )
    )

    # Gather all four reference cities + any custom active locations
    ref_records = []
    pos_map = {
        'Casablanca': 'top left',
        'Rabat': 'top right',
        'Marrakech': 'middle left',
        'Ouarzazate': 'bottom right',
    }
    for city, (clat, clon) in LOCATIONS.items():
        snap = Path(__file__).parent / 'data' / f'{city.lower()}.json'
        if not snap.exists():
            continue
        cdata = json.loads(snap.read_text())
        if city == loc_a and data_a is not None:
            cdata = data_a
        elif city == loc_b and data_b is not None:
            cdata = data_b
        meta = extract_grid_metadata(city, cdata, clat, clon)
        ev = evaluate_site(city, cdata, parameter, start, end, interval_mode=interval_mode)
        ref_records.append((city, cdata, meta, ev))

    # Add custom coordinates if chosen for A or B
    custom_records = []
    for role_loc, role_data, role_lat, role_lon in [
        (loc_a, data_a, lat_a, lon_a),
        (loc_b, data_b, lat_b, lon_b),
    ]:
        if role_loc and role_loc not in LOCATIONS and role_data is not None and role_lat is not None and role_lon is not None:
            meta = extract_grid_metadata(role_loc, role_data, role_lat, role_lon)
            ev = evaluate_site(role_loc, role_data, parameter, start, end, interval_mode=interval_mode)
            custom_records.append((role_loc, role_data, meta, ev))

    all_records = ref_records + custom_records

    # Draw approximate MERRA-2 0.5° x 0.625° resolution footprints first (behind markers)
    for idx_rec, (cname, _, meta, _) in enumerate(all_records):
        fp = meta['footprint']
        is_a = cname == loc_a
        is_b = cname == loc_b
        if is_a:
            fill_rgba = 'rgba(21, 97, 109, 0.16)'
            line_col = SITE_A_COLOR
            line_w = 2.0
            trace_name = f"Approx. {MERRA2_LAT_RES_DEG}°×{MERRA2_LON_RES_DEG}° cell · ● {cname}"
            show_leg = True
        elif is_b:
            fill_rgba = 'rgba(181, 83, 39, 0.16)'
            line_col = SITE_B_COLOR
            line_w = 2.0
            trace_name = f"Approx. {MERRA2_LAT_RES_DEG}°×{MERRA2_LON_RES_DEG}° cell · ◆ {cname}"
            show_leg = True
        else:
            fill_rgba = 'rgba(80, 96, 100, 0.05)'
            line_col = 'rgba(80, 96, 100, 0.48)'
            line_w = 1.2
            trace_name = f"Approx. {MERRA2_LAT_RES_DEG}°×{MERRA2_LON_RES_DEG}° reference scale"
            show_leg = False

        elev_txt = f"{meta['grid_elevation_m']:.1f} m (grid metadata)" if meta['grid_elevation_m'] is not None else 'N/A'
        fig.add_trace(
            go.Scattergeo(
                lat=fp['lats'],
                lon=fp['lons'],
                mode='lines',
                fill='toself',
                fillcolor=fill_rgba,
                line=dict(color=line_col, width=line_w, dash='dash'),
                name=trace_name,
                showlegend=show_leg,
                hovertemplate=(
                    f"<b>{cname} · {meta['footprint_label']}</b><br>"
                    f"Span: {meta['resolution_deg']} ({meta['approx_km']})<br>"
                    f"Returned NASA GeoJSON Point: {meta['returned_lat']:.3f}°N, {meta['returned_lon']:.3f}°E<br>"
                    f"Metadata Grid Elev: {elev_txt}<br>"
                    f"<i>Point JSON omits exact cell bounds; box illustrates approximate MERRA-2 resolution scale.</i><extra></extra>"
                ),
            )
        )

    # Plot city / selected coordinate point markers on top
    for cname, _, meta, ev in all_records:
        is_a = cname == loc_a
        is_b = cname == loc_b
        plat, plon = meta['requested_lat'], meta['requested_lon']
        elev_txt = f"{meta['grid_elevation_m']:.0f} m grid elev" if meta['grid_elevation_m'] is not None else 'global cell'
        if ev['eligible']:
            r = ev['result']
            sl_short = f"{format_bound(r['slope_decade'])} {unit}/dec"
            ci_str = format_interval(ev['active_ci'], rate_unit)
            verdict_txt = ev['active_status']
        else:
            sl_short = 'Ineligible (<30 yr)'
            ci_str = 'N/A'
            verdict_txt = 'Ineligible'

        if is_a:
            m_col, m_sym, m_size = SITE_A_COLOR, 'circle', 13
            role_tag = '● Selected A'
        elif is_b:
            m_col, m_sym, m_size = SITE_B_COLOR, 'diamond', 14
            role_tag = '◆ Selected B'
        else:
            m_col, m_sym, m_size = '#53686d', 'circle-open', 10
            role_tag = '○ Reference city'

        fig.add_trace(
            go.Scattergeo(
                lat=[plat],
                lon=[plon],
                mode='markers+text',
                text=[f"<b>{cname}</b><br>{sl_short}"],
                textposition=pos_map.get(cname, 'top center'),
                textfont=dict(family='Arial, sans-serif', size=10.8, color=INK_COLOR),
                name=f"{role_tag}: {cname}",
                showlegend=(is_a or is_b),
                marker=dict(size=m_size, color=m_col, symbol=m_sym, line=dict(width=2, color='#ffffff')),
                hovertemplate=(
                    f"<b>{cname}</b> ({role_tag}) · {meta['region_name']}<br>"
                    f"Selected query coords: {meta['requested_lat']:.4f}°N, {meta['requested_lon']:.4f}°E<br>"
                    f"NASA returned coords: {meta['returned_lat']:.3f}°N, {meta['returned_lon']:.3f}°E ({elev_txt})<br>"
                    f"Slope: {sl_short}<br>"
                    f"Active 95% CI: {ci_str} ({verdict_txt})<extra></extra>"
                ),
            )
        )

    if in_morocco or not active_pts:
        geo_cfg = dict(
            scope='africa',
            center=dict(lat=32.35, lon=-7.2),
            lataxis_range=[28.8, 35.8],
            lonaxis_range=[-12.5, -1.8],
        )
    else:
        all_lats = [p[0] for p in active_pts] + [32.35]
        all_lons = [p[1] for p in active_pts] + [-7.2]
        lat_pad = max(3.5, 0.25 * (max(all_lats) - min(all_lats)))
        lon_pad = max(4.5, 0.25 * (max(all_lons) - min(all_lons)))
        geo_cfg = dict(
            scope='world',
            lataxis_range=[max(-85.0, min(all_lats) - lat_pad), min(85.0, max(all_lats) + lat_pad)],
            lonaxis_range=[max(-179.0, min(all_lons) - lon_pad), min(179.0, max(all_lons) + lon_pad)],
        )

    fig.update_geos(
        **geo_cfg,
        showland=True,
        landcolor='#efeadd',
        showocean=True,
        oceancolor='#dcebed',
        showcountries=True,
        countrycolor='#b8b09c',
        showcoastlines=True,
        coastlinecolor='#5d7e84',
        showrivers=True,
        rivercolor='#9ec2c9',
        projection_type='mercator',
    )
    fig.update_layout(
        height=390,
        paper_bgcolor=CHART_BG,
        margin=dict(l=4, r=4, t=8, b=58),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.03,
            xanchor='left',
            x=0.0,
            font=dict(size=10.2, color=INK_COLOR),
            bgcolor='rgba(249,247,242,0.0)',
        ),
    )
    return fig


def build_morocco_grid_map(parameter, start=1991, end=2025):
    """Backwards-compatible wrapper for map calls."""
    return build_grid_reality_map(parameter, start=start, end=end)


def render_grid_reality_section(
    loc_a,
    data_a,
    lat_a,
    lon_a,
    loc_b=None,
    data_b=None,
    lat_b=None,
    lon_b=None,
    parameter='T2M',
    start=1991,
    end=2025,
    interval_mode='cautious',
):
    """Render STEP 1 · The Grid-Cell Reality Map and metadata-verified point-vs-grid explanation."""
    meta_a = extract_grid_metadata(loc_a, data_a, lat_a, lon_a)
    has_b = bool(loc_b and data_b is not None and lat_b is not None and lon_b is not None)
    meta_b = extract_grid_metadata(loc_b, data_b, lat_b, lon_b) if has_b else None

    st.markdown(
        '<div class="step-banner">'
        '<div><div class="step-banner-kicker">STEP 1 · WHERE IS THE EVIDENCE?</div>'
        '<div class="step-title">The Grid-Cell Reality Map · Selected Coordinates vs. MERRA-2 Resolution</div></div>'
        '<span class="provenance-badge">Approx. 0.5° × 0.625° MERRA-2 Scale · Exact Cell Bounds Not Published in Point JSON</span>'
        '</div>'
        '<p class="step-banner-sub">Compare point city coordinates against the regional reanalysis scale of NASA POWER '
        'along Morocco’s Atlantic coastline and schematic Atlas Mountains barrier.</p>',
        unsafe_allow_html=True,
    )

    m_col1, m_col2 = st.columns([1.22, 1.0], gap='medium')
    with m_col1:
        st.markdown(
            f'<div class="chart-header-box">'
            f'<div class="chart-header-title">Morocco Terrain Context &amp; Approximate MERRA-2 0.5° × 0.625° Cells</div>'
            f'<div class="chart-header-sub">Dashed boxes illustrate approximate MERRA-2 horizontal resolution (~55–56 km × ~58–59 km at 31°–34°N); '
            f'solid points mark selected query coordinates</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        fig = build_grid_reality_map(
            parameter,
            start=start,
            end=end,
            loc_a=loc_a,
            data_a=data_a,
            lat_a=lat_a,
            lon_a=lon_a,
            loc_b=loc_b if has_b else None,
            data_b=data_b if has_b else None,
            lat_b=lat_b if has_b else None,
            lon_b=lon_b if has_b else None,
            interval_mode=interval_mode,
        )
        st.plotly_chart(fig, use_container_width=True)
    with m_col2:
        rows_html = []
        paired_metas = [('● A', meta_a)] + ([('◆ B', meta_b)] if meta_b is not None else [])
        for glyph, m in paired_metas:
            elev_str = f"{m['grid_elevation_m']:.2f} m" if m['grid_elevation_m'] is not None else 'N/A'
            rows_html.append(
                f"<tr>"
                f"<td style='text-align:left;'><b>{glyph}: {m['location']}</b><br><span style='font-size:0.78rem;color:#4a5f65;'>{m['region_name']}</span></td>"
                f"<td style='text-align:left;'>Query: {m['requested_lat']:.4f}°N, {m['requested_lon']:.4f}°E<br>"
                f"<span style='font-size:0.78rem;color:#4a5f65;'>NASA JSON Point: {m['returned_lat']:.3f}°N, {m['returned_lon']:.3f}°E</span></td>"
                f"<td style='text-align:left;'><b>{elev_str}</b><br><span style='font-size:0.78rem;color:#4a5f65;'>{m['approx_km']}</span></td>"
                f"</tr>"
            )
        meta_table = (
            f'<div class="table-wrapper table-wrapper-auto" tabindex="0" role="region" aria-label="Selected city coordinates versus NASA MERRA-2 grid metadata">'
            f'<table><thead><tr>'
            f'<th style="text-align:left;">Location &amp; Setting</th>'
            f'<th style="text-align:left;">Selected vs. Returned Coords</th>'
            f'<th style="text-align:left;">Grid Metadata Elev &amp; Scale</th>'
            f'</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'
        )
        st.markdown(meta_table, unsafe_allow_html=True)
        elev_a_str = f"{meta_a['grid_elevation_m']:.1f} m" if meta_a['grid_elevation_m'] is not None else 'unavailable'
        if meta_b is not None:
            elev_b_str = f"{meta_b['grid_elevation_m']:.1f} m" if meta_b['grid_elevation_m'] is not None else 'unavailable'
            elev_phrase = f"{elev_a_str} for {loc_a}, {elev_b_str} for {loc_b}"
            phys_phrase = f"{meta_a['station_vs_grid_note']} {meta_b['station_vs_grid_note']}"
        else:
            elev_phrase = f"{elev_a_str} for {loc_a}"
            phys_phrase = f"{meta_a['station_vs_grid_note']}"
        callout_html = (
            f'<div class="reality-callout">'
            f'<b>Grid-Cell Estimates vs. Weather Stations:</b><br>'
            f'• <b>Metadata check ({meta_a["header_title"]}):</b> Point JSON geometry reports <code>type: {meta_a["geometry_type"]}</code> '
            f'with coarse reanalysis elevation ({elev_phrase}) '
            f'and <i>omits exact MERRA-2 cell polygon boundaries</i>; map boxes therefore depict approximate <code>0.5° × 0.625°</code> scale rather than invented cell vertices.<br>'
            f'• <b>Physical scale effect:</b> {phys_phrase}<br>'
            f'• <b>Honesty rule:</b> {meta_a["elevation_caveat"]}'
            f'</div>'
        )
        st.markdown(callout_html, unsafe_allow_html=True)


LENS_OPTIONS = {
    'Compare: Cautious max(SE_OLS, SE_HAC) + OLS': ('cautious', 'both'),
    'Cautious safeguard: max(SE_OLS, SE_HAC)': ('cautious', 'cautious'),
    'Raw Newey–West HAC (SE_HAC, unfloored)': ('hac', 'both'),
    'Conventional OLS (SE_OLS, independent years)': ('conventional', 'conventional'),
}


def resolve_lens(label):
    """Map UI uncertainty lens radio selection to (interval_mode, lens_mode)."""
    return LENS_OPTIONS.get(label, ('cautious', 'both'))


def render_step_ribbon(active_step=None):
    """Render concise 3-step analytical narrative header connecting map, stats, and PDF passport."""
    steps = [
        ('STEP 1', 'Where Is the Evidence?', 'MERRA-2 0.5° × 0.625° grid scale & coastal/Atlas context'),
        ('STEP 2', 'How Strong Is the Evidence?', 'Slopes, paired difference & OLS vs. raw HAC Uncertainty Lens'),
        ('STEP 3', 'Can I Verify the Evidence?', 'One-page Scientific Evidence Brief PDF & SHA-256 hashes'),
    ]
    cards = []
    for idx, (kicker, title, desc) in enumerate(steps, start=1):
        accent = 'border-left-color:#b55327;' if active_step == idx else ''
        cards.append(
            f'<div class="step-card" style="{accent}">'
            f'<div class="step-card-num">{kicker}</div>'
            f'<div class="step-card-q">{title}</div>'
            f'<div class="step-card-desc">{desc}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="step-ribbon">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_step_banner(step_num, question_title, headline_title, subtitle, badge=''):
    """Render an editorial numbered banner matching STEP 1 styling."""
    badge_html = f'<span class="provenance-badge">{badge}</span>' if badge else ''
    st.markdown(
        f'<div class="step-banner">'
        f'<div><div class="step-banner-kicker">STEP {step_num} · {question_title}</div>'
        f'<div class="step-title">{headline_title}</div></div>'
        f'{badge_html}'
        f'</div>'
        f'<p class="step-banner-sub">{subtitle}</p>',
        unsafe_allow_html=True,
    )


def render_uncertainty_lens_panel(
    series_rows,
    active_interval_mode,
    unit,
    rate_unit,
    lens_state_key=None,
    lens_heading='Uncertainty Lens · Conventional OLS vs. Raw Newey–West HAC vs. Cautious Safeguard',
    show_control=True,
):
    """Display interactive assumption controls and tabular SE / CI diagnostics without duplicating plots."""
    st.markdown(f'#### {lens_heading}')
    if show_control and lens_state_key:
        st.radio(
            'Active uncertainty assumption',
            list(LENS_OPTIONS),
            horizontal=True,
            key=lens_state_key,
        )

    valid_entries = []
    for label, res in series_rows:
        lens = uncertainty_lens_summary(res) if res else None
        if lens is not None:
            valid_entries.append((label, res, lens))

    if not valid_entries:
        st.info('At least 30 complete calendar years are required to compute the OLS vs. Newey–West HAC lens.')
        return

    mode_labels = {
        'cautious': 'Cautious safeguard · max(SE_OLS, SE_HAC)',
        'hac': 'Raw Newey–West HAC · SE_HAC (unfloored)',
        'conventional': 'Conventional OLS · SE_OLS (assumes independent years)',
    }
    st.caption(
        f"**Active reporting assumption:** {mode_labels.get(active_interval_mode, active_interval_mode)}. "
        "Charts above reflect this assumption automatically."
    )

    rows_html = []
    floor_notes = []
    for label, res, lens in valid_entries:
        ols_cls = 'badge-clear' if lens['ols_excludes_zero'] else 'badge-cautious'
        ols_txt = 'Excludes 0' if lens['ols_excludes_zero'] else 'Crosses 0'
        hac_cls = 'badge-clear' if lens['hac_excludes_zero'] else 'badge-cautious'
        hac_txt = 'Excludes 0' if lens['hac_excludes_zero'] else 'Crosses 0'
        cau_cls = 'badge-clear' if lens['cautious_excludes_zero'] else 'badge-cautious'
        cau_txt = 'Excludes 0' if lens['cautious_excludes_zero'] else 'Crosses 0'

        if lens['cautious_floored_by_ols']:
            safeguard_note = 'Floored at SE_OLS'
            floor_notes.append(
                f"{label}: raw SE_HAC ({lens['se_hac_decade']:.4f}) &lt; SE_OLS ({lens['se_ols_decade']:.4f}), "
                f"ratio = {lens['hac_to_ols_se_ratio']:.2f}×; cautious max(SE_OLS, SE_HAC) retains SE_OLS."
            )
        else:
            safeguard_note = f"Uses raw SE_HAC ({lens['hac_lags']} lags)"

        rows_html.append(
            f"<tr>"
            f"<td style='text-align:left;'><b>{label}</b><br><span style='font-size:0.78rem;color:#4a5f65;'>ρ₁ = {lens['residual_lag1']:+.2f} · L = {lens['hac_lags']} lags</span></td>"
            f"<td><b>{format_bound(res['slope_decade'])}</b><br><span style='font-size:0.78rem;color:#4a5f65;'>{rate_unit}</span></td>"
            f"<td>{lens['se_ols_decade']:.4f}</td>"
            f"<td><b>{lens['se_hac_decade']:.4f}</b></td>"
            f"<td><b>{lens['hac_to_ols_se_ratio']:.2f}×</b></td>"
            f"<td>{lens['se_cautious_decade']:.4f}<br><span style='font-size:0.76rem;color:#4a5f65;'>{safeguard_note}</span></td>"
            f"<td style='text-align:left;'><span style='white-space:nowrap;'>{format_interval(lens['ols_ci95'], '')}</span> <span class='{ols_cls}'>{ols_txt}</span></td>"
            f"<td style='text-align:left;'><span style='white-space:nowrap;'>{format_interval(lens['hac_ci95'], '')}</span> <span class='{hac_cls}'>{hac_txt}</span></td>"
            f"<td style='text-align:left;'><span style='white-space:nowrap;'>{format_interval(lens['cautious_ci95'], '')}</span> <span class='{cau_cls}'>{cau_txt}</span></td>"
            f"</tr>"
        )

    lens_table = (
        f'<div class="table-wrapper table-wrapper-auto" tabindex="0" role="region" aria-label="Uncertainty Lens comparing OLS, raw Newey-West HAC, and cautious max standard errors">'
        f'<table><thead><tr>'
        f'<th style="text-align:left;">Series</th>'
        f'<th>Slope</th>'
        f'<th>SE<sub>OLS</sub></th>'
        f'<th>Raw SE<sub>HAC</sub></th>'
        f'<th>SE<sub>HAC</sub> / SE<sub>OLS</sub></th>'
        f'<th>Cautious max SE</th>'
        f'<th style="text-align:left;">OLS 95% CI ({rate_unit})</th>'
        f'<th style="text-align:left;">Raw HAC 95% CI ({rate_unit})</th>'
        f'<th style="text-align:left;">Cautious 95% CI ({rate_unit})</th>'
        f'</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'
    )
    st.markdown(lens_table, unsafe_allow_html=True)

    floor_html = f"<br>• <b>Cautious floor vs. raw HAC:</b> {' | '.join(floor_notes)}" if floor_notes else ''
    st.markdown(
        f'<div class="reality-callout">'
        f'<b>How to read the Uncertainty Lens (Exploratory Scope):</b><br>'
        f'• <b>Ratio definition:</b> <code>SE_HAC / SE_OLS</code> measures only the <b>relative change in estimated standard error</b> '
        f'caused by temporal autocorrelation and heteroscedasticity across annual lags. It is <b>NOT a Type-I error probability</b> '
        f'and <b>NOT a false-positive rate</b>.<br>'
        f'• <b>Safeguard distinction:</b> Where active, the cautious rule reports <code>max(SE_OLS, SE_HAC)</code> so finite-sample '
        f'variance estimates never shrink uncertainty bounds below conventional OLS when <code>SE_HAC / SE_OLS &lt; 1.0</code>. '
        f'Switch to <i>Raw Newey–West HAC (SE_HAC, unfloored)</i> above to inspect the unfloored HAC interval directly.<br>'
        f'• <b>Small-sample caveats:</b> With ~30–35 annual observations, lag truncation and asymptotic HAC covariance estimates remain noisy, '
        f'depend on linear model specification, and are unadjusted for multiple comparisons across cities, variables, or windows.{floor_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_evidence_passport_section(
    question,
    parameter,
    start,
    end,
    loc_a,
    lat_a,
    lon_a,
    data_a,
    loc_b=None,
    lat_b=None,
    lon_b=None,
    data_b=None,
    trial=None,
    comp=None,
    single_site=None,
    interval_mode='cautious',
    key_prefix='passport',
    secondary_md=None,
    secondary_md_name=None,
    export_df=None,
    export_csv_name=None,
):
    """Render STEP 3 Evidence Brief one-click PDF export and verifiable SHA-256 provenance."""
    render_step_banner(
        3,
        'CAN I VERIFY THE EVIDENCE?',
        'One-Click Evidence Passport · Downloadable Scientific Evidence Brief (PDF)',
        'Every number in this dynamically generated one-page PDF brief matches the active selection, '
        'uncertainty assumption, NASA API endpoints, and SHA-256 source checksums.',
        badge='1-Page PDF · Reproducible State · SHA-256 Verified',
    )

    sha_a = source_sha256(loc_a, data_a)
    sha_b = source_sha256(loc_b, data_b) if (loc_b and data_b) else None
    pdf_bytes = build_scientific_evidence_brief_pdf(
        question=question,
        parameter=parameter,
        start=start,
        end=end,
        loc_a=loc_a,
        lat_a=lat_a,
        lon_a=lon_a,
        data_a=data_a,
        loc_b=loc_b,
        lat_b=lat_b,
        lon_b=lon_b,
        data_b=data_b,
        trial=trial,
        comp=comp,
        single_site=single_site,
        interval_mode=interval_mode,
    )

    slug_loc = f'{loc_a}_{loc_b}' if loc_b else loc_a
    slug_safe = ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in slug_loc)
    pdf_filename = f'earthpulse_evidence_brief_{slug_safe}_{parameter}_{start}_{end}.pdf'

    hero_left, hero_right = st.columns([1.35, 1.0])
    with hero_left:
        st.markdown(
            f'<div class="passport-hero">'
            f'<div class="step-banner-kicker">REPRODUCIBLE ONE-PAGE AUDIT BRIEF</div>'
            f'<div class="step-title" style="font-size:1.05rem;">{question}</div>'
            f'<p style="margin:0.2rem 0 0 0;font-size:0.84rem;color:#243b40;">'
            f'Contains coordinates, MERRA-2 grid resolution caveats, slopes &amp; 95% intervals under '
            f'<code>{interval_mode}</code> assumptions, limitations, full NASA URLs, and input SHA-256 checksums.'
            f'</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with hero_right:
        st.download_button(
            'Download Scientific Evidence Brief',
            data=pdf_bytes,
            file_name=pdf_filename,
            mime='application/pdf',
            type='primary',
            use_container_width=True,
            key=f'{key_prefix}_pdf_btn',
        )
        hash_lines = [f"`{loc_a}` (`{sha_a['scope']}`): `{sha_a['sha256'][:16]}…{sha_a['sha256'][-8:]}`"]
        if sha_b:
            hash_lines.append(f"`{loc_b}` (`{sha_b['scope']}`): `{sha_b['sha256'][:16]}…{sha_b['sha256'][-8:]}`")
        st.caption('SHA-256: ' + ' · '.join(hash_lines))

    dl_cols = st.columns(4)
    col_idx = 0
    if export_df is not None and export_csv_name:
        dl_cols[col_idx].download_button(
            'Annual Data · CSV',
            export_df.to_csv(index=False),
            export_csv_name,
            'text/csv',
            use_container_width=True,
            key=f'{key_prefix}_csv_btn',
        )
        col_idx += 1
    if secondary_md and secondary_md_name:
        dl_cols[col_idx].download_button(
            'Evidence Summary · MD',
            secondary_md,
            secondary_md_name,
            'text/markdown',
            use_container_width=True,
            key=f'{key_prefix}_md_btn',
        )
        col_idx += 1
    dl_cols[col_idx].download_button(
        f'{loc_a} NASA · JSON',
        json.dumps(data_a, indent=2),
        f'earthpulse_{loc_a}_NASA.json',
        'application/json',
        use_container_width=True,
        key=f'{key_prefix}_json_a_btn',
    )
    col_idx += 1
    if loc_b and data_b is not None and col_idx < 4:
        dl_cols[col_idx].download_button(
            f'{loc_b} NASA · JSON',
            json.dumps(data_b, indent=2),
            f'earthpulse_{loc_b}_NASA.json',
            'application/json',
            use_container_width=True,
            key=f'{key_prefix}_json_b_btn',
        )


def build_evidence_brief_markdown(comp, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b):
    """Create a one-page reproducible Markdown Evidence Brief for download."""
    sa, sb = comp['site_a'], comp['site_b']
    rate_unit = comp['rate_unit']
    lines = [
        f"# EarthPulse — Evidence Brief: {loc_a} vs. {loc_b}",
        "",
        f"- **Variable**: {comp['variable_name']} (`{comp['parameter']}`, `{comp['unit']}`)",
        f"- **Period**: `{comp['start']}–{comp['end']}`",
        f"- **Headline Verdict**: **{comp['headline']}**",
        f"- **Summary**: {comp['second_line']}",
        "",
    ]
    if comp['both_eligible']:
        ra, rb = sa['result'], sb['result']
        lines.extend([
            "## Quantitative Comparison",
            "",
            f"| Metric | {loc_a} ({lat_a:.4f}°N, {lon_a:.4f}°E) | {loc_b} ({lat_b:.4f}°N, {lon_b:.4f}°E) |",
            "| :--- | :--- | :--- |",
            f"| Complete Years (n) | `{ra['n']}` | `{rb['n']}` |",
            f"| Period Mean | `{ra['mean']:.2f} {comp['unit']}` | `{rb['mean']:.2f} {comp['unit']}` |",
            f"| Slope / Decade | `{format_bound(ra['slope_decade'])} {rate_unit}` (`{ra['slope_decade']:+.5f}`) | `{format_bound(rb['slope_decade'])} {rate_unit}` (`{rb['slope_decade']:+.5f}`) |",
            f"| Conventional 95% CI (OLS) | `{format_interval(ra['iid_ci95'], rate_unit)}` (p = {ra['iid_p']:.4g}) | `{format_interval(rb['iid_ci95'], rate_unit)}` (p = {rb['iid_p']:.4g}) |",
            f"| Cautious 95% CI (HAC / max SE) | `{format_interval(ra['ci95'], rate_unit)}` (p = {ra['p_value']:.4g}) | `{format_interval(rb['ci95'], rate_unit)}` (p = {rb['p_value']:.4g}) |",
            f"| Residual Lag-1 (ρ₁) | `{ra['residual_lag1']:+.3f}` | `{rb['residual_lag1']:+.3f}` |",
            f"| Cautious Status | **{sa['cautious_status']}** | **{sb['cautious_status']}** |",
            "",
            "## Methodological Notes",
            "",
            f"- **Time-Dependence Impact**: {comp['time_dependence_note']}",
            f"- **Interpretation Boundary**: {comp['overlap_note']}",
            f"- **NASA POWER Request ({loc_a})**: {data_a.get('_earthpulse', {}).get('request_url', 'Bundled MERRA-2 snapshot')}",
            f"- **NASA POWER Request ({loc_b})**: {data_b.get('_earthpulse', {}).get('request_url', 'Bundled MERRA-2 snapshot')}",
        ])
    return "\n".join(lines)


def format_trial_question(loc_a, loc_b, parameter):
    """Return the human-facing headline question for The Climate Trial."""
    if loc_a == loc_b:
        return f"Comparing {loc_a} against itself ({VARIABLES[parameter][0]})"
    if parameter == 'T2M':
        return f"Is {loc_b} warming faster than {loc_a}?"
    return f"Is {loc_b} gaining rainfall faster than {loc_a}?"


def _padded_axis_range(*arrays):
    """Compute a padded y-axis range that always includes 0.0."""
    vals = np.concatenate([np.asarray(a, dtype=float).ravel() for a in arrays] + [np.array([0.0])])
    lo, hi = float(np.min(vals)), float(np.max(vals))
    span = max(hi - lo, 0.25)
    return [lo - 0.16 * span, hi + 0.18 * span]


def build_trial_transition_figure(trial):
    """Build the animated Original-to-Paired-Difference Plotly figure for The Climate Trial."""
    merged = trial['merged']
    unit = trial['unit']
    rate_unit = trial['rate_unit']
    loc_a = trial['site_a']['location']
    loc_b = trial['site_b']['location']
    fig = go.Figure()

    if merged.empty:
        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref='paper',
            yref='paper',
            text='<b>No overlapping complete calendar years available.</b>',
            showarrow=False,
            font=dict(size=13, color=INK_COLOR),
        )
        fig.update_layout(height=340, template='plotly_white', paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
        return fig

    years = merged['year'].to_numpy(dtype=int)
    a_dev = merged['value_a'].to_numpy(dtype=float) - float(merged['value_a'].mean())
    b_dev = merged['value_b'].to_numpy(dtype=float) - float(merged['value_b'].mean())
    diff_vals = merged['diff'].to_numpy(dtype=float)
    zeros = np.zeros_like(diff_vals)

    eligible = trial['eligible']
    if eligible:
        fitted_vals = merged['fitted_diff'].to_numpy(dtype=float)
        dr = trial['diff_result']
        fit_label = f"Linear fit ({format_bound(dr['slope_decade'])} {rate_unit})"
        verdict_code = trial['verdict_code']
        fit_color = (
            SITE_B_COLOR if verdict_code == 'positive_difference'
            else SITE_A_COLOR if verdict_code == 'negative_difference'
            else '#495b5f'
        )
    else:
        fitted_vals = zeros
        fit_label = 'Linear fit withheld (<30 consecutive paired years)'
        fit_color = '#9aa5a7'

    y_range_orig = _padded_axis_range(a_dev, b_dev)
    y_range_mid = _padded_axis_range(0.45 * a_dev, 0.45 * b_dev + 0.55 * diff_vals, 0.55 * diff_vals)
    y_range_diff = _padded_axis_range(diff_vals, fitted_vals) if eligible else _padded_axis_range(diff_vals)

    # Initial traces start in Final Paired-Difference stage (step2) so metrics are immediately readable
    fig.add_trace(
        go.Scatter(
            x=years,
            y=zeros,
            mode='lines+markers',
            name=f"● {loc_a} anomaly ({unit})",
            line=dict(color=SITE_A_COLOR, width=2.0, dash='solid'),
            marker=dict(symbol='circle', size=5.5, color=SITE_A_COLOR),
            opacity=0.0,
            showlegend=False,
            hovertemplate=f"<b>{loc_a} anomaly</b> (%{{x}}): %{{y:+.2f}} {unit}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=zeros,
            mode='lines+markers',
            name=f"◆ {loc_b} anomaly ({unit})",
            line=dict(color=SITE_B_COLOR, width=2.0, dash='dot'),
            marker=dict(symbol='diamond', size=6.0, color=SITE_B_COLOR),
            opacity=0.0,
            showlegend=False,
            hovertemplate=f"<b>{loc_b} anomaly</b> (%{{x}}): %{{y:+.2f}} {unit}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=diff_vals,
            mode='lines+markers',
            name=f"D(year) = {loc_b} − {loc_a} ({unit})",
            line=dict(color=INK_COLOR, width=2.3, dash='solid'),
            marker=dict(
                symbol='circle',
                size=6.5,
                color=[SITE_B_COLOR if v >= 0 else SITE_A_COLOR for v in diff_vals],
                line=dict(width=1.0, color='#ffffff'),
            ),
            opacity=1.0,
            hovertemplate=f"<b>D(%{{x}}) = {loc_b} − {loc_a}</b>: %{{y:+.2f}} {unit}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=fitted_vals,
            mode='lines',
            name=fit_label,
            line=dict(color=fit_color, width=3.4, dash='dash' if verdict_code_or_default(trial) == 'inconclusive' else 'solid'),
            opacity=1.0 if eligible else 0.0,
            hovertemplate=f"<b>Fitted D(%{{x}})</b>: %{{y:+.2f}} {unit}<extra></extra>",
        )
    )

    fig.add_hline(
        y=0.0,
        line_width=1.8,
        line_dash='dot',
        line_color='#66767a',
    )
    fig.add_annotation(
        x=0.99,
        y=0.0,
        xref='paper',
        yref='y',
        xanchor='right',
        yshift=-11,
        text='0.0 (No gap)',
        showarrow=False,
        font=dict(size=9.8, color='#45575b'),
        bgcolor='rgba(249,247,242,0.92)',
    )

    fig.frames = [
        go.Frame(
            name='step0',
            data=[
                go.Scatter(x=years, y=a_dev, opacity=0.92),
                go.Scatter(x=years, y=b_dev, opacity=0.92),
                go.Scatter(x=years, y=zeros, opacity=0.14),
                go.Scatter(x=years, y=zeros, opacity=0.0),
            ],
            layout=go.Layout(
                yaxis=dict(title=f"Centered {trial['variable_name']} ({unit})", range=y_range_orig),
            ),
        ),
        go.Frame(
            name='step1',
            data=[
                go.Scatter(x=years, y=0.45 * a_dev, opacity=0.45),
                go.Scatter(x=years, y=0.45 * b_dev + 0.55 * diff_vals, opacity=0.45),
                go.Scatter(x=years, y=0.55 * diff_vals, opacity=0.72),
                go.Scatter(x=years, y=0.55 * fitted_vals, opacity=0.55 if eligible else 0.0),
            ],
            layout=go.Layout(
                yaxis=dict(title=f"Pairing Transition ({unit})", range=y_range_mid),
            ),
        ),
        go.Frame(
            name='step2',
            data=[
                go.Scatter(x=years, y=zeros, opacity=0.0),
                go.Scatter(x=years, y=zeros, opacity=0.0),
                go.Scatter(x=years, y=diff_vals, opacity=1.0),
                go.Scatter(x=years, y=fitted_vals, opacity=1.0 if eligible else 0.0),
            ],
            layout=go.Layout(
                yaxis=dict(title=f"Paired Difference D(year) ({unit})", range=y_range_diff),
            ),
        ),
    ]

    fig.update_layout(
        height=365,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family='Arial, sans-serif', color=INK_COLOR, size=12),
        margin=dict(l=54, r=18, t=58, b=72),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.27,
            xanchor='left',
            x=0.0,
            font=dict(size=10.8),
            bgcolor='rgba(249,247,242,0.0)',
        ),
        updatemenus=[
            dict(
                type='buttons',
                direction='left',
                x=0.0,
                xanchor='left',
                y=1.18,
                yanchor='top',
                bgcolor='#ece8de',
                bordercolor='#cbc3b2',
                borderwidth=1,
                font=dict(size=10.2, color=INK_COLOR),
                pad=dict(r=4, t=1, b=3),
                buttons=[
                    dict(
                        label='▶ Animate Morph',
                        method='animate',
                        args=[
                            ['step0', 'step1', 'step2'],
                            {
                                'frame': {'duration': 900, 'redraw': False},
                                'transition': {'duration': 650, 'easing': 'cubic-in-out'},
                                'fromcurrent': False,
                            },
                        ],
                    ),
                    dict(
                        label='1. Original A & B',
                        method='animate',
                        args=[
                            ['step0'],
                            {
                                'mode': 'immediate',
                                'frame': {'duration': 500, 'redraw': False},
                                'transition': {'duration': 450},
                            },
                        ],
                    ),
                    dict(
                        label='2. Paired D(year)',
                        method='animate',
                        args=[
                            ['step2'],
                            {
                                'mode': 'immediate',
                                'frame': {'duration': 500, 'redraw': False},
                                'transition': {'duration': 450},
                            },
                        ],
                    ),
                ],
            )
        ],
        xaxis=dict(
            title='Calendar year (aligned pairs)',
            range=[trial['start'] - 0.6, trial['end'] + 0.6],
            gridcolor='#e3ded2',
            zeroline=False,
        ),
        yaxis=dict(
            title=f"Paired Difference D(year) ({unit})",
            range=y_range_diff,
            gridcolor='#e3ded2',
            zeroline=False,
        ),
        hovermode='x unified',
    )
    return fig


def verdict_code_or_default(trial):
    return trial.get('verdict_code', 'ineligible')


def build_trial_verdict_figure(trial, lens_mode):
    """Build the Zero-Line Confidence Interval plot comparing D(year) = B - A alongside contextual solo intervals."""
    rate_unit = trial['rate_unit']
    loc_a = trial['site_a']['location']
    loc_b = trial['site_b']['location']
    fig = go.Figure()

    fig.add_vline(x=0.0, line_width=2.5, line_dash='solid', line_color=INK_COLOR)

    if not trial['eligible']:
        fig.add_annotation(
            x=0.0,
            y=0.5,
            xref='x',
            yref='paper',
            text=(
                "<b>Trial inference withheld</b><br>"
                "At least 30 consecutive complete paired years (with non-constant D)<br>"
                "are required for OLS &amp; Newey–West HAC intervals."
            ),
            showarrow=False,
            font=dict(size=12.2, color=INK_COLOR, family='Georgia, serif'),
            bgcolor='#f5e6c8',
            bordercolor='#d4b475',
            borderwidth=1,
            borderpad=10,
        )
        fig.update_layout(
            height=355,
            template='plotly_white',
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            margin=dict(l=20, r=20, t=54, b=40),
            xaxis=dict(title=f"Slope difference ({rate_unit})", range=[-1, 1], gridcolor='#e3ded2'),
            yaxis=dict(visible=False),
        )
        return fig

    dr = trial['diff_result']
    ra = trial['aligned_site_a_result']
    rb = trial['aligned_site_b_result']
    slope_d = dr['slope_decade']

    show_cautious = lens_mode in ('both', 'cautious')
    show_iid = lens_mode in ('both', 'conventional')

    verdict_color = (
        SITE_B_COLOR if trial['verdict_code'] == 'positive_difference'
        else SITE_A_COLOR if trial['verdict_code'] == 'negative_difference'
        else '#46585c'
    )

    all_bounds = [0.0, *dr['ci95'], *dr['iid_ci95']]
    if ra is not None:
        all_bounds.extend(ra['ci95'])
    if rb is not None:
        all_bounds.extend(rb['ci95'])

    span = max(all_bounds) - min(all_bounds)
    x_min = min(all_bounds) - max(span * 0.34, 0.14)
    x_max = max(all_bounds) + max(span * 0.50, 0.28)
    x_mid = 0.5 * (x_min + x_max)

    fig.add_annotation(
        x=0.0,
        y=1.18,
        xref='x',
        yref='y',
        text='<b>0.0 (No diff)</b>',
        showarrow=False,
        font=dict(size=10.4, color=INK_COLOR),
        bgcolor='#e5e0d3',
        bordercolor='#b8b09c',
        borderwidth=1,
        borderpad=3,
    )

    # Primary Track: Paired Difference D(year) = B - A
    active_mode = trial.get('interval_mode', 'cautious')
    primary_ci_name = 'Raw HAC 95% CI (SE_HAC)' if active_mode == 'hac' else 'Cautious 95% CI (HAC / max SE)'
    primary_ci_hover = 'Raw Newey–West HAC' if active_mode == 'hac' else 'Cautious HAC'
    y_d_base = 1.75
    fig.add_trace(
        go.Scatter(
            x=[slope_d],
            y=[y_d_base + (0.09 if lens_mode == 'both' else 0.0)],
            mode='markers',
            name=primary_ci_name,
            opacity=1.0 if show_cautious else 0.25,
            marker=dict(symbol='star', size=13, color=verdict_color, line=dict(width=1.4, color='#ffffff')),
            error_x=dict(
                type='data',
                symmetric=False,
                array=[dr['ci95'][1] - slope_d],
                arrayminus=[slope_d - dr['ci95'][0]],
                color=verdict_color,
                thickness=4.6,
                width=8,
            ),
            hovertemplate=(
                f"<b>Paired Difference D = {loc_b} − {loc_a} ({primary_ci_hover})</b><br>"
                f"Slope diff: {format_bound(slope_d)} {rate_unit}<br>"
                f"95% CI: {format_interval(dr['ci95'], rate_unit)}<br>"
                f"p = {dr['p_value']:.4g}<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[slope_d],
            y=[y_d_base - (0.11 if lens_mode == 'both' else 0.0)],
            mode='markers',
            name='Conventional 95% OLS',
            opacity=0.95 if show_iid else 0.22,
            marker=dict(symbol='circle-open', size=9, color='#455c61', line=dict(width=2, color='#455c61')),
            error_x=dict(
                type='data',
                symmetric=False,
                array=[dr['iid_ci95'][1] - slope_d],
                arrayminus=[slope_d - dr['iid_ci95'][0]],
                color='#52696e',
                thickness=2.2,
                width=5,
            ),
            hovertemplate=(
                f"<b>Paired Difference D = {loc_b} − {loc_a} (Conventional OLS)</b><br>"
                f"Slope diff: {format_bound(slope_d)} {rate_unit}<br>"
                f"95% CI: {format_interval(dr['iid_ci95'], rate_unit)}<br>"
                f"p = {dr['iid_p']:.4g}<extra></extra>"
            ),
        )
    )

    active_ci = trial['active_ci']
    verdict_badge = 'Excludes 0' if trial['active_excludes_zero'] else 'Crosses 0 · Inconclusive'
    fig.add_annotation(
        x=0.5,
        y=2.14,
        xref='paper',
        yref='y',
        xanchor='center',
        text=(
            f"<b>⚖ D = B − A: {format_bound(slope_d)}</b> "
            f"[{format_bound(active_ci[0])}, {format_bound(active_ci[1])} · <b>{verdict_badge}</b>]"
        ),
        showarrow=False,
        font=dict(size=10.4, color=verdict_color, family='Arial, sans-serif'),
        bgcolor='rgba(249,247,242,0.95)',
    )

    # Divider separating Paired Trial from contextual separate site intervals
    fig.add_hline(y=0.92, line_width=1.2, line_dash='dot', line_color='#cbc3b2')
    fig.add_annotation(
        x=0.5,
        y=0.98,
        xref='paper',
        yref='y',
        xanchor='center',
        text='Separate single-site fits (interval overlap does not test B − A)',
        showarrow=False,
        font=dict(size=9.8, color='#55696e'),
        bgcolor=CHART_BG,
    )

    ctx_specs = [
        (loc_b, rb, 0.45, SITE_B_COLOR, 'diamond', '◆'),
        (loc_a, ra, 0.0, SITE_A_COLOR, 'circle', '●'),
    ]
    for cname, cres, y_pos, ccolor, csym, cglyph in ctx_specs:
        if cres is None:
            continue
        cslope = cres['slope_decade']
        cci = cres['iid_ci95'] if lens_mode == 'conventional' else cres['ci95']
        fig.add_trace(
            go.Scatter(
                x=[cslope],
                y=[y_pos],
                mode='markers',
                showlegend=False,
                opacity=0.68,
                marker=dict(symbol=csym, size=8.5, color=ccolor),
                error_x=dict(
                    type='data',
                    symmetric=False,
                    array=[cci[1] - cslope],
                    arrayminus=[cslope - cci[0]],
                    color=ccolor,
                    thickness=2.4,
                    width=5,
                ),
                hovertemplate=(
                    f"<b>{cname} alone (contextual)</b><br>"
                    f"Slope: {format_bound(cslope)} {rate_unit}<br>"
                    f"95% CI: {format_interval(cci, rate_unit)}<extra></extra>"
                ),
            )
        )
        fig.add_annotation(
            x=min(max(cslope, x_min + 0.16 * (x_max - x_min)), x_max - 0.24 * (x_max - x_min)),
            y=y_pos + 0.19,
            xref='x',
            yref='y',
            xanchor='center',
            text=f"{cglyph} {cname}: {format_bound(cslope)} [{format_bound(cci[0])}, {format_bound(cci[1])}]",
            showarrow=False,
            font=dict(size=9.5, color=ccolor),
            bgcolor='rgba(249,247,242,0.92)',
        )

    fig.update_layout(
        height=365,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family='Arial, sans-serif', color=INK_COLOR, size=12),
        margin=dict(l=88, r=24, t=58, b=72),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.27,
            xanchor='left',
            x=0.0,
            font=dict(size=10.8),
            bgcolor='rgba(249,247,242,0.0)',
        ),
        xaxis=dict(
            title=f"Decadal rate ({rate_unit})",
            range=[x_min, x_max],
            gridcolor='#e3ded2',
            zeroline=False,
        ),
        yaxis=dict(
            tickmode='array',
            tickvals=[0.0, 0.45, y_d_base],
            ticktext=[f"● {loc_a}", f"◆ {loc_b}", "<b>⚖ D = B − A</b>"],
            range=[-0.35, 2.38],
            gridcolor='#ece8de',
        ),
    )
    return fig


def build_trial_provenance_payload(trial, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b):
    """Build machine-readable Evidence Passport metadata with NASA sources and trial results."""
    dr = trial['diff_result']
    ra = trial['aligned_site_a_result']
    rb = trial['aligned_site_b_result']
    return {
        'earthpulse_module': 'The Climate Trial',
        'exploratory': True,
        'claim_question': format_trial_question(loc_a, loc_b, trial['parameter']),
        'parameter': trial['parameter'],
        'variable_name': trial['variable_name'],
        'units': trial['unit'],
        'rate_units': trial['rate_unit'],
        'analysis_period': f"{trial['start']}–{trial['end']}",
        'n_paired_years': trial['n_paired'],
        'missing_paired_years': trial['missing_paired'],
        'interval_mode': trial['interval_mode'],
        'verdict_code': trial['verdict_code'],
        'verdict_label': trial['verdict_label'],
        'interpretation': trial['interpretation'],
        'slope_difference_identity_delta': trial['slope_diff_identity_delta'],
        'residual_correlation_r': trial['residual_correlation'],
        'paired_difference_stats': {k: v for k, v in dr.items() if k != 'fitted'} if dr else None,
        'locations': {
            'location_a': {
                'name': loc_a,
                'requested_coords': {'latitude': lat_a, 'longitude': lon_a},
                'returned_geometry': data_a.get('geometry'),
                'nasa_header': data_a.get('header'),
                'retrieval': data_a.get('_earthpulse', {}),
                'aligned_stats': {k: v for k, v in ra.items() if k != 'fitted'} if ra else None,
            },
            'location_b': {
                'name': loc_b,
                'requested_coords': {'latitude': lat_b, 'longitude': lon_b},
                'returned_geometry': data_b.get('geometry'),
                'nasa_header': data_b.get('header'),
                'retrieval': data_b.get('_earthpulse', {}),
                'aligned_stats': {k: v for k, v in rb.items() if k != 'fitted'} if rb else None,
            },
        },
        'methodology_guardrails': [
            'Minimum 30 consecutive complete annual values without interpolation.',
            'Paired annual difference D(year) = Variable_B(year) - Variable_A(year).',
            'Cautious screening uses max(SE_OLS, SE_HAC) with Bartlett kernel and finite-sample t correction.',
            'Inconclusive result means interval crosses zero; it does NOT imply equal trends.',
            'Exploratory trial without multiplicity adjustment across candidate city pairs or windows.',
        ],
    }


def build_evidence_passport_markdown(trial, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b):
    """Create a downloadable Markdown Evidence Passport for The Climate Trial."""
    rate_unit = trial['rate_unit']
    dr = trial['diff_result']
    ra = trial['aligned_site_a_result']
    rb = trial['aligned_site_b_result']
    lines = [
        f"# EarthPulse — Climate Trial Evidence Passport",
        "",
        f"- **Trial Question**: {format_trial_question(loc_a, loc_b, trial['parameter'])}",
        f"- **Statistical Hypothesis**: Paired annual difference `D(year) = {loc_b}(year) - {loc_a}(year)`",
        f"- **Variable**: {trial['variable_name']} (`{trial['parameter']}`, `{trial['unit']}`)",
        f"- **Analysis Dates**: `{trial['start']}–{trial['end']}` (`{trial['n_paired']}` complete paired years)",
        f"- **Inference Lens**: `{trial['interval_mode']}` (**Exploratory — unadjusted for multiplicity**)",
        f"- **Derived Verdict**: **{trial['verdict_label']}**",
        f"- **Interpretation**: {trial['interpretation']}",
        "",
    ]
    if trial['eligible'] and dr is not None:
        lines.extend([
            "## Paired Difference Inference (`D = B - A`)",
            "",
            f"| Metric | Value |",
            f"| :--- | :--- |",
            f"| Estimated Slope Difference / Decade | `{format_bound(dr['slope_decade'])} {rate_unit}` (`{dr['slope_decade']:+.6f}`) |",
            f"| Cautious 95% CI (HAC / max SE, `{dr['hac_lags']}` lags) | `{format_interval(dr['ci95'], rate_unit)}` (p = {dr['p_value']:.4g}) |",
            f"| Conventional 95% CI (OLS independent years) | `{format_interval(dr['iid_ci95'], rate_unit)}` (p = {dr['iid_p']:.4g}) |",
            f"| Paired Residual Lag-1 Autocorrelation (`ρ₁`) | `{dr['residual_lag1']:+.3f}` |",
            f"| Residual Cross-Site Correlation (`r`) | `{trial['residual_correlation']:+.3f}` |" if trial['residual_correlation'] is not None else "| Residual Cross-Site Correlation (`r`) | N/A |",
            f"| OLS Slope Difference Identity Check (`|slope(B-A) - (slope(B)-slope(A))|`) | `{trial['slope_diff_identity_delta']:.2e}` |" if trial['slope_diff_identity_delta'] is not None else "| OLS Slope Difference Identity Check | N/A |",
            "",
        ])
    if ra is not None and rb is not None:
        lines.extend([
            "## Individual Aligned Trends (Identical Years Reference)",
            "",
            f"- **{loc_a}** (`{lat_a:.4f}°N, {lon_a:.4f}°E`): `{format_bound(ra['slope_decade'])} {rate_unit}`, cautious 95% CI `{format_interval(ra['ci95'], rate_unit)}` (`ρ₁ = {ra['residual_lag1']:+.3f}`)",
            f"- **{loc_b}** (`{lat_b:.4f}°N, {lon_b:.4f}°E`): `{format_bound(rb['slope_decade'])} {rate_unit}`, cautious 95% CI `{format_interval(rb['ci95'], rate_unit)}` (`ρ₁ = {rb['residual_lag1']:+.3f}`)",
            "",
        ])
    lines.extend([
        "## NASA Source & Provenance Metadata",
        "",
        f"- **Data Origin**: `{data_a.get('_earthpulse', {}).get('data_origin', 'NASA POWER API; no synthetic measurements')}`",
        f"- **NASA Header**: `{data_a.get('header', {}).get('title', 'NASA/POWER MERRA-2')}` (`API {data_a.get('header', {}).get('api', {}).get('version', 'unknown')}`)",
        f"- **Location A Request URL**: {data_a.get('_earthpulse', {}).get('request_url', 'Bundled MERRA-2 snapshot')}",
        f"- **Location A Retrieved UTC**: `{data_a.get('_earthpulse', {}).get('retrieved_utc', 'N/A')}`",
        f"- **Location B Request URL**: {data_b.get('_earthpulse', {}).get('request_url', 'Bundled MERRA-2 snapshot')}",
        f"- **Location B Retrieved UTC**: `{data_b.get('_earthpulse', {}).get('retrieved_utc', 'N/A')}`",
        "",
        "## Methodological Guardrails",
        "",
        f"- {trial['overlap_insight']}",
        f"- {trial['time_dependence_note']}",
    ])
    return "\n".join(lines)


# --- Sidebar Controls ---
with st.sidebar:
    st.header('EarthPulse Controls')
    data_mode = st.radio(
        'Data access',
        ['Verified bundled NASA snapshot', 'Live NASA API'],
        index=0,
    )
    st.caption(
        'Bundled snapshots cover Casablanca, Rabat, Marrakech and Ouarzazate for 1991–2025. '
        'Custom coordinates and earlier years (1981–1990) query NASA POWER live.'
    )
    st.divider()
    st.caption('Built by Hafida Belayd, EarthPulse Labs. Independent NASA Space Apps prototype. No NASA endorsement.')

# --- Top Eyebrow & View Entry Points ---
st.session_state.setdefault('trial_tested', False)
st.session_state.setdefault('trial_loc_a', 'Casablanca')
st.session_state.setdefault('trial_loc_b', 'Marrakech')
st.session_state.setdefault('trial_param', 'T2M')
st.session_state.setdefault('trial_period', (1991, 2025))
st.session_state.setdefault('trial_lens', list(LENS_OPTIONS)[0])
if st.session_state.get('trial_lens') not in LENS_OPTIONS:
    st.session_state['trial_lens'] = list(LENS_OPTIONS)[0]


def _apply_trial_preset(loc_a_v, loc_b_v, param_v, period_v=(1991, 2025)):
    st.session_state['trial_loc_a'] = loc_a_v
    st.session_state['trial_loc_b'] = loc_b_v
    st.session_state['trial_param'] = param_v
    st.session_state['trial_period'] = period_v
    st.session_state['trial_tested'] = True


st.markdown(
    '<div class="eyebrow-row">'
    '<span class="eyebrow">EARTHPULSE · EXPERT ANALYSIS — PUT CLIMATE CLAIMS ON TRIAL.</span>'
    '<span class="provenance-badge">Exploratory Analysis · NASA POWER / MERRA-2 · 30-Year Rule · Newey–West HAC</span>'
    '</div>',
    unsafe_allow_html=True,
)
_exp_nav1, _exp_nav2 = st.columns(2)
with _exp_nav1:
    st.page_link('lab.py', label='← Back to 3D Earth Investigation Studio', icon='🧭')
with _exp_nav2:
    st.page_link('discover.py', label='Explore 6 NASA Variables & Seasonal Fingerprints →', icon='🛰️')

nav_choice = st.radio(
    'Investigation mode',
    options=[
        'The Climate Trial (paired test)',
        'Compare: The Trend Verdict',
        'Single Location & Custom Coordinates',
    ],
    index=0,
    horizontal=True,
    label_visibility='collapsed',
)

if nav_choice.startswith('The Climate Trial'):
    active_view = 'trial'
elif nav_choice.startswith('Compare'):
    active_view = 'compare'
else:
    active_view = 'single'

render_step_ribbon()

if active_view == 'trial':
    trial_loc_options = list(LOCATIONS.keys()) + ['Custom coordinates']

    tc1, tc2, tc3 = st.columns([1.05, 1.05, 1.3])
    with tc1:
        loc_a_choice = st.selectbox('Location A (● Baseline)', trial_loc_options, key='trial_loc_a')
        if loc_a_choice == 'Custom coordinates':
            ca1, ca2 = st.columns(2)
            lat_a = ca1.number_input('Lat A (°N)', -90.0, 90.0, 33.5731, step=0.01, format='%.4f', key='trial_lat_a')
            lon_a = ca2.number_input('Lon A (°E)', -180.0, 180.0, -7.5898, step=0.01, format='%.4f', key='trial_lon_a')
            loc_a = f"Custom A ({lat_a:.2f}°, {lon_a:.2f}°)"
        else:
            loc_a = loc_a_choice
            lat_a, lon_a = LOCATIONS[loc_a]
    with tc2:
        loc_b_choice = st.selectbox('Location B (◆ Challenger)', trial_loc_options, key='trial_loc_b')
        if loc_b_choice == 'Custom coordinates':
            cb1, cb2 = st.columns(2)
            lat_b = cb1.number_input('Lat B (°N)', -90.0, 90.0, 31.6295, step=0.01, format='%.4f', key='trial_lat_b')
            lon_b = cb2.number_input('Lon B (°E)', -180.0, 180.0, -7.9811, step=0.01, format='%.4f', key='trial_lon_b')
            loc_b = f"Custom B ({lat_b:.2f}°, {lon_b:.2f}°)"
        else:
            loc_b = loc_b_choice
            lat_b, lon_b = LOCATIONS[loc_b]
    with tc3:
        parameter = st.selectbox(
            'Common climate variable',
            list(VARIABLES.keys()),
            format_func=lambda k: f"{VARIABLES[k][0]} ({VARIABLES[k][1]})",
            key='trial_param',
        )

    start, end = st.session_state['trial_period']
    interval_mode, whisker_lens = resolve_lens(st.session_state['trial_lens'])

    try:
        with st.spinner('Retrieving NASA POWER records for paired trial…'):
            data_a, bundled_a = load_location_data(loc_a_choice, lat_a, lon_a, start, end, data_mode)
            data_b, bundled_b = load_location_data(loc_b_choice, lat_b, lon_b, start, end, data_mode)

        trial = climate_trial(
            loc_a,
            data_a,
            loc_b,
            data_b,
            parameter=parameter,
            start=start,
            end=end,
            interval_mode=interval_mode,
        )
        v2_comp = compare_locations(
            loc_a,
            data_a,
            loc_b,
            data_b,
            parameter=parameter,
            start=start,
            end=end,
            interval_mode=interval_mode,
        )

        # Hero Question
        st.markdown(
            f'<p class="trial-tagline">THE CLIMATE TRIAL · “PUT CLIMATE CLAIMS ON TRIAL.”</p>'
            f'<div class="editorial-headline">{format_trial_question(loc_a, loc_b, parameter)}</div>'
            f'<p class="trial-subq"><b>Are the two trends significantly different from each other?</b> '
            f'Aligned paired series <code>D(year) = {loc_b}(year) − {loc_a}(year)</code> across {start}–{end} '
            f'<span class="provenance-badge">Exploratory · {trial["n_paired"]} paired yr</span></p>',
            unsafe_allow_html=True,
        )

        # Two-City Face-Off Cards + Central TEST THE DIFFERENCE Action
        sa, sb = trial['site_a'], trial['site_b']
        rate_unit = trial['rate_unit']

        def _site_card_html(site_info, coords, role_label, extra_cls, accent_color):
            lat_v, lon_v = coords
            if site_info['eligible']:
                sr = site_info['result']
                ex = site_info['active_excludes_zero']
                ci_active = site_info['active_ci']
                bcls = 'badge-clear' if ex else 'badge-cautious'
                btxt = 'Excludes 0' if ex else 'Crosses 0'
                body = (
                    f'<div class="city-card-rate" style="color:{accent_color};">'
                    f'{format_bound(sr["slope_decade"])} <span style="font-size:0.88rem;font-weight:500;">{rate_unit}</span></div>'
                    f'<div class="city-card-meta">'
                    f'95% CI: <b>{format_interval(ci_active, "")}</b> <span class="{bcls}">{btxt}</span><br>'
                    f'Mean: {sr["mean"]:.2f} {trial["unit"]} · Lag-1 ρ₁ = {sr["residual_lag1"]:+.2f}'
                    f'</div>'
                )
            else:
                body = (
                    f'<div class="city-card-rate" style="color:#6e4b0c;font-size:1.15rem;">Inference withheld</div>'
                    f'<div class="city-card-meta">{site_info["n_complete"]} complete annual values in {start}–{end}. '
                    f'At least 30 consecutive complete years required.</div>'
                )
            return (
                f'<div class="city-card {extra_cls}">'
                f'<div class="city-card-kicker">{role_label} · {lat_v:.2f}°N, {lon_v:.2f}°E</div>'
                f'<div class="city-card-name">{site_info["location"]}</div>'
                f'{body}'
                f'</div>'
            )

        face_a, face_vs, face_b = st.columns([1.15, 0.95, 1.15], gap='medium')
        with face_a:
            st.markdown(_site_card_html(sa, (lat_a, lon_a), '● Location A (Baseline)', 'city-card-a', SITE_A_COLOR), unsafe_allow_html=True)
        with face_vs:
            overlap_hint = (
                "Separate 95% intervals overlap—overlap alone cannot resolve whether slopes differ."
                if trial['separate_intervals_overlap']
                else "Never infer slope differences from separate intervals alone—test D(year) directly."
            )
            vs_badge = 'TRIAL ACTIVE · B − A' if st.session_state['trial_tested'] else 'VS · H₀: SLOPE(B) − SLOPE(A) = 0'
            st.markdown(
                f'<div class="vs-card">'
                f'<div class="vs-pill">{vs_badge}</div>'
                f'<div class="vs-prompt">{overlap_hint}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            btn_label = '⚖ TEST THE DIFFERENCE' if not st.session_state['trial_tested'] else '↻ RE-RUN TRIAL'
            if st.button(btn_label, type='primary', use_container_width=True, key='trial_run_btn'):
                st.session_state['trial_tested'] = True
        with face_b:
            st.markdown(_site_card_html(sb, (lat_b, lon_b), '◆ Location B (Challenger)', 'city-card-b', SITE_B_COLOR), unsafe_allow_html=True)

        if trial['years_a_only'] or trial['years_b_only']:
            st.warning(
                f"Unpaired incomplete years dropped without interpolation: "
                f"missing paired years {', '.join(map(str, trial['missing_paired']))}."
            )

        if st.session_state['trial_tested']:
            # Post-Trial State Hero Reveal
            vcode = trial['verdict_code']
            if vcode == 'positive_difference':
                v_banner_cls, v_pill_cls = 'verdict-positive', 'verdict-pill-pos'
            elif vcode == 'negative_difference':
                v_banner_cls, v_pill_cls = 'verdict-negative', 'verdict-pill-neg'
            elif vcode == 'inconclusive':
                v_banner_cls, v_pill_cls = 'verdict-inconclusive', 'verdict-pill-inc'
            else:
                v_banner_cls, v_pill_cls = 'verdict-ineligible', 'verdict-pill-warn'

            if trial['eligible']:
                dr = trial['diff_result']
                corr_txt = f"{trial['residual_correlation']:+.2f}" if trial['residual_correlation'] is not None else 'N/A'
                id_txt = f"{trial['slope_diff_identity_delta']:.1e}" if trial['slope_diff_identity_delta'] is not None else 'N/A'
                metrics_html = (
                    f'<div class="trial-metrics-grid">'
                    f'<div class="trial-metric-box"><div class="trial-metric-label">Slope Difference (B − A)</div>'
                    f'<div class="trial-metric-value">{format_bound(dr["slope_decade"])} {rate_unit}</div>'
                    f'<div class="trial-metric-sub">Exact: {dr["slope_decade"]:+.5f} {rate_unit}</div></div>'
                    f'<div class="trial-metric-box"><div class="trial-metric-label">95% CI &amp; Exploratory p</div>'
                    f'<div class="trial-metric-value">{format_interval(trial["active_ci"], "")}</div>'
                    f'<div class="trial-metric-sub">p = {trial["active_p"]:.4g} ({interval_mode})</div></div>'
                    f'<div class="trial-metric-box"><div class="trial-metric-label">Noise Cancellation</div>'
                    f'<div class="trial-metric-value">r = {corr_txt}</div>'
                    f'<div class="trial-metric-sub">Paired lag-1 ρ₁ = {dr["residual_lag1"]:+.2f}</div></div>'
                    f'<div class="trial-metric-box"><div class="trial-metric-label">OLS Identity Check</div>'
                    f'<div class="trial-metric-value">Δ = {id_txt}</div>'
                    f'<div class="trial-metric-sub">slope(B−A) == slope(B) − slope(A)</div></div>'
                    f'</div>'
                )
            else:
                metrics_html = ''

            verdict_html = (
                f'<div class="trial-reveal-panel">'
                f'<div class="verdict-banner {v_banner_cls}">'
                f'<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:0.4rem;">'
                f'<span class="{v_pill_cls}">{trial["verdict_label"]}</span>'
                f'<span class="provenance-badge">Exploratory · D(year) = {loc_b} − {loc_a} ({start}–{end})</span>'
                f'</div>'
                f'{metrics_html}'
                f'<p style="margin:0.45rem 0 0.25rem 0;font-size:0.96rem;color:#14282d;line-height:1.48;">{trial["interpretation"]}</p>'
                f'<p style="margin:0.2rem 0 0 0;font-size:0.84rem;color:#3c5358;line-height:1.42;">{trial["overlap_insight"]}</p>'
                f'</div>'
                f'</div>'
            )
            st.markdown(verdict_html, unsafe_allow_html=True)

        # --- STEP 1: WHERE IS THE EVIDENCE? ---
        render_grid_reality_section(
            loc_a,
            data_a,
            lat_a,
            lon_a,
            loc_b,
            data_b,
            lat_b,
            lon_b,
            parameter,
            start,
            end,
            interval_mode=interval_mode,
        )

        # --- STEP 2: HOW STRONG IS THE EVIDENCE? ---
        step2_active_desc = {
            'cautious': 'Cautious max(SE_OLS, SE_HAC) vs. Conventional OLS',
            'hac': 'Raw Newey–West HAC (SE_HAC) vs. Conventional OLS',
            'conventional': 'Conventional OLS (independent years)',
        }.get(interval_mode, interval_mode)
        render_step_banner(
            2,
            'HOW STRONG IS THE EVIDENCE?',
            'Climate Trends, Paired Difference Trial & Uncertainty Lens',
            'Inspect aligned trends, challenge the period or uncertainty assumptions, and compare SE_OLS, raw SE_HAC, and cautious max(SE_OLS, SE_HAC).',
            badge=f'{trial["n_paired"]} paired yr · Exploratory',
        )

        if not st.session_state['trial_tested']:
            p_left, p_right = st.columns([1.12, 1.0])
            with p_left:
                st.markdown(
                    f'<div class="chart-header-box">'
                    f'<div class="chart-header-title">Original Aligned Series &amp; Separate Fits ({trial["unit"]})</div>'
                    f'<div class="chart-header-sub">Click TEST THE DIFFERENCE above to animate the paired transformation D(year) = {loc_b} − {loc_a}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(build_comparison_series_figure(v2_comp), use_container_width=True)
            with p_right:
                st.markdown(
                    f'<div class="chart-header-box">'
                    f'<div class="chart-header-title">Separate Single-Site Intervals ({rate_unit})</div>'
                    f'<div class="chart-header-sub">Each interval tests one site vs. 0.0 ({step2_active_desc})</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(build_whisker_figure(v2_comp, whisker_lens), use_container_width=True)

            render_uncertainty_lens_panel(
                [(loc_a, sa['result']), (loc_b, sb['result'])],
                interval_mode,
                trial['unit'],
                rate_unit,
                lens_state_key='trial_lens',
                show_control=True,
            )
            st.caption('Click **⚖ TEST THE DIFFERENCE** above to compute the paired `D(year) = B − A` trial row and animated transition.')
        else:
            t_left, t_right = st.columns([1.15, 1.0])
            with t_left:
                st.markdown(
                    f'<div class="chart-header-box">'
                    f'<div class="chart-header-title">Paired Difference Series D(year) = {loc_b} − {loc_a} ({trial["unit"]})</div>'
                    f'<div class="chart-header-sub">Use ▶ Animate above the plot to watch centered A &amp; B collapse into paired D(year)</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(build_trial_transition_figure(trial), use_container_width=True)
            with t_right:
                st.markdown(
                    f'<div class="chart-header-box">'
                    f'<div class="chart-header-title">Trial Zero-Line Verdict Interval ({rate_unit})</div>'
                    f'<div class="chart-header-sub">Zero reference line (0.0 = no slope difference) · {step2_active_desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(build_trial_verdict_figure(trial, whisker_lens), use_container_width=True)

            # --- Compact Challenge the Verdict Investigation Panel ---
            with st.container(border=True):
                st.markdown(
                    '<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:0.4rem;">'
                    '<h3 style="margin:0;font-size:1.18rem;">Challenge the Verdict · Exploratory Sensitivity Panel</h3>'
                    '<span class="provenance-badge">Exploratory · Unadjusted across windows &amp; pairs</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                ch1, ch2 = st.columns([1.05, 1.25])
                with ch1:
                    st.slider(
                        'Analysis period (minimum 30 consecutive complete years)',
                        1981,
                        2025,
                        key='trial_period',
                    )
                with ch2:
                    st.radio(
                        'Uncertainty assumption (OLS vs. raw HAC vs. cautious max)',
                        list(LENS_OPTIONS),
                        horizontal=True,
                        key='trial_lens',
                    )

                st.caption('Try another claim on trial (computes live from NASA snapshots):')
                q1, q2, q3, q4 = st.columns(4)
                q1.button(
                    'Marrakech − Casa · T2M',
                    on_click=_apply_trial_preset,
                    args=('Casablanca', 'Marrakech', 'T2M'),
                    use_container_width=True,
                    key='preset_pos',
                )
                q2.button(
                    'Casa − Marrakech · T2M',
                    on_click=_apply_trial_preset,
                    args=('Marrakech', 'Casablanca', 'T2M'),
                    use_container_width=True,
                    key='preset_neg',
                )
                q3.button(
                    'Rabat − Casa · T2M',
                    on_click=_apply_trial_preset,
                    args=('Casablanca', 'Rabat', 'T2M'),
                    use_container_width=True,
                    key='preset_inc_t2m',
                )
                q4.button(
                    'Marrakech − Casa · Rain',
                    on_click=_apply_trial_preset,
                    args=('Casablanca', 'Marrakech', 'PRECTOTCORR'),
                    use_container_width=True,
                    key='preset_inc_rain',
                )

                ch_tab_sens, ch_tab_series = st.tabs([
                    'OLS vs. HAC Lens & Identity Proof',
                    f'Year-to-Year Paired Series D(year) ({trial["n_paired"]} yr)',
                ])
                with ch_tab_sens:
                    if trial['eligible']:
                        dr = trial['diff_result']
                        ra = trial['aligned_site_a_result']
                        rb = trial['aligned_site_b_result']
                        render_uncertainty_lens_panel(
                            [
                                (f'Paired D = {loc_b} − {loc_a}', dr),
                                (f'{loc_b} (aligned)', rb),
                                (f'{loc_a} (aligned)', ra),
                            ],
                            interval_mode,
                            trial['unit'],
                            rate_unit,
                            show_control=False,
                        )
                        st.caption(
                            f"**OLS Identity Proof:** `slope(B − A) = {dr['slope_decade']:+.6f}` vs. "
                            f"`({rb['slope_decade']:+.6f}) − ({ra['slope_decade']:+.6f}) = "
                            f"{rb['slope_decade'] - ra['slope_decade']:+.6f}` "
                            f"(`|Δ| = {trial['slope_diff_identity_delta']:.1e}`)."
                        )
                    else:
                        st.warning(trial['interpretation'])

                with ch_tab_series:
                    mdf = trial['merged']
                    if not mdf.empty:
                        rows_html = []
                        for _, row in mdf.iterrows():
                            fit_td = f"{row['fitted_diff']:+.3f}" if 'fitted_diff' in mdf.columns else '—'
                            res_td = f"{row['residual_diff']:+.3f}" if 'residual_diff' in mdf.columns else '—'
                            rows_html.append(
                                f"<tr><td>{int(row['year'])}</td>"
                                f"<td>{row['value_a']:.2f}</td>"
                                f"<td>{row['value_b']:.2f}</td>"
                                f"<td><b>{row['diff']:+.3f}</b></td>"
                                f"<td>{fit_td}</td>"
                                f"<td>{res_td}</td></tr>"
                            )
                        table_series_html = (
                            f'<div class="table-wrapper" tabindex="0" role="region" aria-label="Year-by-year paired difference series">'
                            f'<table><thead><tr>'
                            f'<th>Year</th>'
                            f'<th>{loc_a} ({trial["unit"]})</th>'
                            f'<th>{loc_b} ({trial["unit"]})</th>'
                            f'<th>D(year) = B − A</th>'
                            f'<th>Linear Fit</th>'
                            f'<th>Residual</th>'
                            f'</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'
                        )
                        st.markdown(table_series_html, unsafe_allow_html=True)
                    else:
                        st.info('No paired annual values available in this window.')

        # --- STEP 3: CAN I VERIFY THE EVIDENCE? (Available both pre- and post-trial) ---
        passport_md = build_evidence_passport_markdown(trial, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b)
        provenance_obj = build_trial_provenance_payload(trial, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b)
        export_trial_df = trial['merged'].copy()
        export_trial_df['location_a'] = loc_a
        export_trial_df['location_b'] = loc_b
        export_trial_df['parameter'] = parameter
        export_trial_df['units'] = trial['unit']
        export_trial_df['source'] = 'NASA POWER / MERRA-2'

        render_evidence_passport_section(
            question=format_trial_question(loc_a, loc_b, parameter),
            parameter=parameter,
            start=start,
            end=end,
            loc_a=loc_a,
            lat_a=lat_a,
            lon_a=lon_a,
            data_a=data_a,
            loc_b=loc_b,
            lat_b=lat_b,
            lon_b=lon_b,
            data_b=data_b,
            trial=trial,
            comp=v2_comp,
            interval_mode=interval_mode,
            key_prefix='trial_passport',
            secondary_md=passport_md,
            secondary_md_name=f'earthpulse_trial_passport_{loc_a}_{loc_b}_{parameter}_{start}_{end}.md',
            export_df=export_trial_df,
            export_csv_name=f'earthpulse_trial_series_{loc_a}_{loc_b}_{parameter}_{start}_{end}.csv',
        )

        with st.expander('NASA POWER source metadata, trial provenance JSON & exact API request links'):
            st.download_button(
                'Download Trial Provenance · JSON',
                json.dumps(provenance_obj, indent=2),
                f'earthpulse_trial_provenance_{loc_a}_{loc_b}_{parameter}_{start}_{end}.json',
                'application/json',
                key='trial_prov_json_btn',
            )
            st.json(provenance_obj)
            l1, l2 = st.columns(2)
            if data_a.get('_earthpulse', {}).get('request_url'):
                l1.link_button(f'Open exact NASA request · {loc_a}', data_a['_earthpulse']['request_url'])
            if data_b.get('_earthpulse', {}).get('request_url'):
                l2.link_button(f'Open exact NASA request · {loc_b}', data_b['_earthpulse']['request_url'])

    except Exception as error:
        st.error(f'Unable to complete Climate Trial: {error}')
        st.info('Use the verified bundled NASA snapshots for 1991–2025, or switch to Compare: The Trend Verdict.')

elif active_view == 'compare':
    loc_names = list(LOCATIONS.keys())

    headline_container = st.container()

    c1, c2, c3, c4 = st.columns([1.0, 1.0, 1.35, 1.45])
    with c1:
        loc_a = st.selectbox('Location A (● Teal)', loc_names, index=0, key='comp_loc_a')
    with c2:
        loc_b = st.selectbox('Location B (◆ Ochre)', loc_names, index=2, key='comp_loc_b')
    with c3:
        parameter = st.selectbox(
            'Climate variable',
            list(VARIABLES.keys()),
            format_func=lambda k: f"{VARIABLES[k][0]} ({VARIABLES[k][1]})",
            index=0,
            key='comp_param',
        )
    with c4:
        period = st.slider(
            'Completed calendar years',
            1981,
            2025,
            (1991, 2025),
            key='comp_period',
        )

    st.session_state.setdefault('comp_lens', list(LENS_OPTIONS)[0])
    if st.session_state.get('comp_lens') not in LENS_OPTIONS:
        st.session_state['comp_lens'] = list(LENS_OPTIONS)[0]
    lens_label = st.radio(
        'What changes when we account for time dependence? · Switch uncertainty assumption',
        list(LENS_OPTIONS),
        horizontal=True,
        key='comp_lens',
    )

    interval_mode, whisker_lens = resolve_lens(lens_label)
    start, end = period

    try:
        lat_a, lon_a = LOCATIONS[loc_a]
        lat_b, lon_b = LOCATIONS[loc_b]
        with st.spinner('Loading NASA POWER gridded climate estimates…'):
            data_a, bundled_a = load_location_data(loc_a, lat_a, lon_a, start, end, data_mode)
            data_b, bundled_b = load_location_data(loc_b, lat_b, lon_b, start, end, data_mode)

        comp = compare_locations(
            loc_a,
            data_a,
            loc_b,
            data_b,
            parameter=parameter,
            start=start,
            end=end,
            interval_mode=interval_mode,
        )

        source_tag = (
            'Verified bundled NASA POWER / MERRA-2 snapshots'
            if (bundled_a and bundled_b)
            else 'Live NASA POWER / MERRA-2 API response (cached 24h)'
        )

        with headline_container:
            st.markdown(
                f'<div class="editorial-headline">{comp["headline"]}</div>'
                f'<p class="verdict-lead">{comp["second_line"]}</p>',
                unsafe_allow_html=True,
            )

        for s in (comp['site_a'], comp['site_b']):
            if s['omitted']:
                st.warning(
                    f"{s['location']}: incomplete years excluded ({', '.join(map(str, s['omitted']))}). "
                    "No values have been interpolated."
                )

        if not comp['both_eligible']:
            st.warning(f"Ineligible for linear trend inference: {comp['second_line']}")

        # --- STEP 1: WHERE IS THE EVIDENCE? ---
        render_grid_reality_section(
            loc_a,
            data_a,
            lat_a,
            lon_a,
            loc_b,
            data_b,
            lat_b,
            lon_b,
            parameter,
            start,
            end,
            interval_mode=interval_mode,
        )

        # --- STEP 2: HOW STRONG IS THE EVIDENCE? ---
        active_lens_sub = {
            'cautious': 'Cautious max(SE_OLS, SE_HAC) vs. Conventional OLS',
            'hac': 'Raw Newey–West HAC (SE_HAC) vs. Conventional OLS',
            'conventional': 'Conventional OLS (independent years)',
        }.get(interval_mode, interval_mode)
        render_step_banner(
            2,
            'HOW STRONG IS THE EVIDENCE?',
            'Trend Verdict Charts, Uncertainty Lens & Stability Checks',
            'Evaluate time-series slopes alongside OLS vs. raw Newey–West HAC vs. cautious max(SE_OLS, SE_HAC) intervals.',
            badge=f'{start}–{end} · {interval_mode.upper()}',
        )

        # --- Side-by-Side Visual Reveal ---
        chart_left, chart_right = st.columns([1.12, 1.0])
        with chart_left:
            st.markdown(
                f'<div class="chart-header-box">'
                f'<div class="chart-header-title">Aligned Annual Series &amp; Linear Fits ({comp["unit"]})</div>'
                f'<div class="chart-header-sub">{comp["variable_name"]} · Shared calendar year axis ({start}–{end}) &amp; shared scale</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(build_comparison_series_figure(comp), use_container_width=True)
        with chart_right:
            st.markdown(
                f'<div class="chart-header-box">'
                f'<div class="chart-header-title">Slope Verdict &amp; Exploratory 95% Uncertainty Bars ({comp["rate_unit"]})</div>'
                f'<div class="chart-header-sub">Zero reference line (0.0) · {active_lens_sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(build_whisker_figure(comp, whisker_lens), use_container_width=True)

        # --- Uncertainty Lens Table (replaces old summary table without duplicating charts) ---
        sa, sb = comp['site_a'], comp['site_b']
        rate_unit = comp['rate_unit']
        if comp['both_eligible']:
            ra, rb = sa['result'], sb['result']
            render_uncertainty_lens_panel(
                [(loc_a, ra), (loc_b, rb)],
                interval_mode,
                comp['unit'],
                rate_unit,
                show_control=False,
            )
            st.caption(f"**Interpretation boundary:** {comp['overlap_note']} Source: {source_tag}.")
        else:
            ineligible_html = (
                f'<div class="evidence-panel">'
                f'<h4>What changes when we account for time dependence?</h4>'
                f'<p>{comp["time_dependence_note"]}</p>'
                f'<p><span class="badge-ineligible">Ineligible window ({start}–{end})</span> '
                f'Select at least 30 consecutive complete years (for example, 1991–2025 or 1996–2025) '
                f'to compute OLS and Newey–West HAC trend intervals.</p>'
                f'</div>'
            )
            st.markdown(ineligible_html, unsafe_allow_html=True)

        # --- Interactive Scientific Diagnostics (Deep-Dive Tabs; Grid Map already rendered in STEP 1) ---
        tab_resid, tab_matrix, tab_window = st.tabs([
            '1. Residual Persistence (ρ₁)',
            '2. Four Moroccan Regimes',
            '3. Window Stability (30+ yr)',
        ])

        with tab_resid:
            if comp['both_eligible']:
                r_col1, r_col2 = st.columns([1.15, 1.0])
                with r_col1:
                    st.markdown(
                        f'<div class="chart-header-box">'
                        f'<div class="chart-header-title">Lag-1 Residual Persistence (eₜ₋₁ vs. eₜ)</div>'
                        f'<div class="chart-header-sub">Positive autocorrelation clusters multi-year anomalies and widens Newey–West HAC intervals</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(build_residual_persistence_figure(comp), use_container_width=True)
                with r_col2:
                    st.markdown('#### Why residual memory matters for trend detection')
                    st.write(
                        f"Ordinary regression treats every calendar year as an independent coin toss. "
                        f"When detrended residuals exhibit positive year-to-year memory (as in **{loc_a}**, "
                        f"where lag-1 autocorrelation is **ρ₁ = {sa['result']['residual_lag1']:+.2f}**), "
                        f"warm years tend to cluster together, reducing the effective degrees of freedom."
                    )
                    st.write(
                        f"Newey–West HAC standard errors ({sa['result']['hac_lags']} annual Bartlett lags with finite-sample correction) "
                        f"account for this short-range serial correlation. In **{loc_b}** (**ρ₁ = {sb['result']['residual_lag1']:+.2f}**), "
                        f"residual persistence is weaker and the warming signal is steeper, so its 95% interval remains "
                        f"{'above' if sb['cautious_excludes_zero'] else 'across'} zero under both methods."
                    )
            else:
                st.info('Select an uninterrupted period of at least 30 complete years to inspect detrended OLS residuals.')

        with tab_matrix:
            st.markdown(
                f"#### Four Moroccan Reference Grid Cells ({VARIABLES[parameter][0]}, 1991–2025 Bundled Baseline)"
            )
            matrix_rows = []
            for city, (clat, clon) in LOCATIONS.items():
                snap_path = Path(__file__).parent / 'data' / f'{city.lower()}.json'
                if snap_path.exists():
                    cdata = json.loads(snap_path.read_text())
                    cev = evaluate_site(city, cdata, parameter, 1991, 2025)
                    if cev['eligible']:
                        cr = cev['result']
                        matrix_rows.append({
                            'Location (MERRA-2 Grid)': f"{city} ({clat:.2f}°N, {clon:.2f}°E)",
                            f"Mean ({comp['unit']})": f"{cr['mean']:.2f}",
                            f"Slope / Decade ({rate_unit})": f"{format_bound(cr['slope_decade'])} ({cr['slope_decade']:+.5f})",
                            'Conventional 95% CI (OLS)': format_interval(cr['iid_ci95'], rate_unit),
                            'Cautious 95% CI (HAC / max SE)': format_interval(cr['ci95'], rate_unit),
                            'Residual ρ₁': f"{cr['residual_lag1']:+.2f}",
                            'Cautious Verdict': cev['cautious_status'],
                        })
            if matrix_rows:
                st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)
                st.caption(
                    'Exploratory screening across four Moroccan climate regimes (Atlantic coast to High Atlas rain shadow). '
                    'No adjustment for multiple comparisons is applied; overlapping intervals between sites do not test whether slopes differ.'
                )

        with tab_window:
            if bundled_a and bundled_b:
                w_col1, w_col2 = st.columns([1.2, 1.0])
                with w_col1:
                    st.markdown(
                        f'<div class="chart-header-box">'
                        f'<div class="chart-header-title">Sensitivity Across Consecutive 30+ Year Sub-Windows</div>'
                        f'<div class="chart-header-sub">Comparing {loc_a} and {loc_b} cautious 95% intervals across 30–35 year spans</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(build_window_sensitivity_figure(loc_a, data_a, loc_b, data_b, parameter), use_container_width=True)
                with w_col2:
                    st.markdown('#### Guarding against endpoint cherry-picking')
                    st.write(
                        'Linear trend slopes can shift when start or end years coincide with multi-year anomalies '
                        '(such as the 1991–1993 post-Pinatubo cool period or the 2022–2025 warm spell). '
                        'Inspecting all consecutive 30-to-35-year windows inside the 1991–2025 record shows whether '
                        'a site’s zero-crossing verdict is stable or sensitive to window choice.'
                    )
                    st.caption(
                        'Note: Evaluating multiple overlapping time windows is an exploratory sensitivity check, '
                        'not a family-wise hypothesis test.'
                    )
            else:
                st.info('Switch Data access to "Verified bundled NASA snapshot" (1991–2025) to compare rolling 30+ year windows.')

        # --- Methodological Chain of Evidence & Limits ---
        col_ev, col_lim = st.columns([1.15, 1.0])
        with col_ev:
            st.subheader('A transparent chain of evidence')
            st.write(
                'NASA POWER supplies MERRA-2 gridded reanalysis estimates representing regional grid cells rather than '
                'point weather stations. Temperature is the day-weighted annual mean at 2 metres (°C). Annual precipitation '
                'sums each monthly mean daily rate multiplied by the calendar days in that month (mm/year). '
                'All 12 valid months are required; NASA’s month-13 summary and fill values (-999) are rejected.'
            )
            st.write(
                'Annual aggregation removes the regular seasonal cycle. Ordinary least squares (OLS) estimates the linear '
                'change per decade, while our cautious screening rule uses the larger standard error from ordinary OLS and '
                'Newey–West HAC regression (Bartlett kernel, finite-sample correction, floor(4(n/100)^(2/9)) annual lags).'
            )
        with col_lim:
            st.subheader('Read the limits & exploratory scope')
            st.write(
                'Gridded reanalysis smooths over sharp coastal and mountain microclimates (such as the Atlantic coast at '
                'Casablanca versus the Haouz plain and High Atlas foothills near Marrakech). Statistical significance describes '
                'how consistently a linear slope differs from zero within the selected window; it does not establish physical '
                'causation or guarantee future trajectory.'
            )
            st.write(
                'All p-values and 95% intervals are exploratory. Inspecting multiple city pairs, variables, or sub-periods '
                'increases the chance of false-positive findings; no multiplicity adjustment is applied across repeated comparisons.'
            )

        with st.expander('Source metadata, full-precision statistics and reproducibility'):
            st.json(
                {
                    'comparison_summary': {
                        'headline': comp['headline'],
                        'parameter': parameter,
                        'units': comp['unit'],
                        'period': f'{start}–{end}',
                        'interval_mode': interval_mode,
                        'intervals_overlap': comp['intervals_overlap'],
                    },
                    loc_a: {
                        'NASA_header': data_a['header'],
                        'returned_point': data_a['geometry'],
                        'retrieval': data_a.get('_earthpulse', {}),
                        'analysis': {k: v for k, v in (sa['result'] or {}).items() if k != 'fitted'},
                    },
                    loc_b: {
                        'NASA_header': data_b['header'],
                        'returned_point': data_b['geometry'],
                        'retrieval': data_b.get('_earthpulse', {}),
                        'analysis': {k: v for k, v in (sb['result'] or {}).items() if k != 'fitted'},
                    },
                }
            )
            st.markdown(
                '[NASA POWER monthly API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) · '
                '[MERRA-2 reanalysis](https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/)'
            )
            link_col1, link_col2 = st.columns(2)
            if data_a.get('_earthpulse', {}).get('request_url'):
                link_col1.link_button(f'Open exact NASA request · {loc_a}', data_a['_earthpulse']['request_url'])
            if data_b.get('_earthpulse', {}).get('request_url'):
                link_col2.link_button(f'Open exact NASA request · {loc_b}', data_b['_earthpulse']['request_url'])

        export_df = pd.concat(
            [
                sa['frame'].assign(
                    location=loc_a,
                    parameter=parameter,
                    units=comp['unit'],
                    latitude=lat_a,
                    longitude=lon_a,
                    source='NASA POWER / MERRA-2',
                ),
                sb['frame'].assign(
                    location=loc_b,
                    parameter=parameter,
                    units=comp['unit'],
                    latitude=lat_b,
                    longitude=lon_b,
                    source='NASA POWER / MERRA-2',
                ),
            ],
            ignore_index=True,
        )
        brief_md = build_evidence_brief_markdown(comp, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b)
        render_evidence_passport_section(
            question=f"How do {VARIABLES[parameter][0].lower()} trends compare between {loc_a} and {loc_b} ({start}–{end})?",
            parameter=parameter,
            start=start,
            end=end,
            loc_a=loc_a,
            lat_a=lat_a,
            lon_a=lon_a,
            data_a=data_a,
            loc_b=loc_b,
            lat_b=lat_b,
            lon_b=lon_b,
            data_b=data_b,
            comp=comp,
            interval_mode=interval_mode,
            key_prefix='compare_passport',
            secondary_md=brief_md,
            secondary_md_name=f'earthpulse_brief_{loc_a}_{loc_b}_{parameter}_{start}_{end}.md',
            export_df=export_df,
            export_csv_name=f'earthpulse_compare_{loc_a}_{loc_b}_{parameter}_{start}_{end}.csv',
        )

    except Exception as error:
        st.error(f'Unable to complete this comparison: {error}')
        st.info('Use the verified bundled NASA snapshots for 1991–2025, or retry the live NASA API later. No synthetic data will be substituted.')

else:
    # --- Single Location & Custom Coordinates Explorer ---
    st.markdown(
        '<div class="editorial-headline">Single-location &amp; custom-coordinate investigation</div>'
        '<p class="verdict-lead">Inspect a single Moroccan reference grid cell or enter any global latitude and longitude '
        'to fetch live NASA POWER / MERRA-2 monthly records and run the 30-year cautious trend screen.</p>',
        unsafe_allow_html=True,
    )

    s_col1, s_col2, s_col3 = st.columns([1.2, 1.2, 1.3])
    with s_col1:
        location = st.selectbox('Location', list(LOCATIONS) + ['Custom coordinates'], key='single_loc')
    lat, lon = LOCATIONS.get(location, (33.5731, -7.5898))
    if location == 'Custom coordinates':
        coord1, coord2 = st.columns(2)
        with coord1:
            lat = st.number_input('Latitude (°N)', -90.0, 90.0, lat, step=0.01, format='%.4f', key='single_lat')
        with coord2:
            lon = st.number_input('Longitude (°E)', -180.0, 180.0, lon, step=0.01, format='%.4f', key='single_lon')
    with s_col2:
        parameter = st.selectbox(
            'Variable',
            list(VARIABLES),
            format_func=lambda k: f"{VARIABLES[k][0]} ({VARIABLES[k][1]})",
            key='single_param',
        )
    with s_col3:
        period = st.slider('Completed calendar years', 1981, 2025, (1991, 2025), key='single_period')

    st.session_state.setdefault('single_lens', list(LENS_OPTIONS)[0])
    if st.session_state.get('single_lens') not in LENS_OPTIONS:
        st.session_state['single_lens'] = list(LENS_OPTIONS)[0]
    single_lens_label = st.radio(
        'Uncertainty assumption (OLS vs. raw HAC vs. cautious max)',
        list(LENS_OPTIONS),
        horizontal=True,
        key='single_lens',
    )
    interval_mode, _ = resolve_lens(single_lens_label)

    start, end = period
    try:
        with st.spinner('Retrieving NASA POWER climate estimates…'):
            data, bundled = load_location_data(location, lat, lon, start, end, data_mode)

        site_eval = evaluate_site(location, data, parameter, start, end, interval_mode=interval_mode)
        frame, omitted, result = site_eval['frame'], site_eval['omitted'], site_eval['result']
        name, unit = VARIABLES[parameter]
        rate_unit = f"{unit}/decade"
        st.caption(
            f"{location} ({lat:.4f}°, {lon:.4f}°)  /  {name} ({unit})  /  {start}–{end}  /  "
            f"{'Bundled real NASA response' if bundled else 'Live NASA API response (cached for up to 24 hours)'}"
        )
        if omitted:
            st.warning('Incomplete years excluded: ' + ', '.join(map(str, omitted)) + '. No values have been interpolated.')
        if not site_eval['eligible'] and site_eval['error']:
            st.warning(site_eval['error'])

        # --- STEP 1: WHERE IS THE EVIDENCE? ---
        render_grid_reality_section(
            location,
            data,
            lat,
            lon,
            None,
            None,
            None,
            None,
            parameter,
            start,
            end,
            interval_mode=interval_mode,
        )

        # --- STEP 2: HOW STRONG IS THE EVIDENCE? ---
        active_ci_label = {
            'cautious': 'Cautious 95% CI (max SE)',
            'hac': 'Raw HAC 95% CI (SE_HAC)',
            'conventional': 'Conventional 95% CI (OLS)',
        }.get(interval_mode, '95% CI')
        render_step_banner(
            2,
            'HOW STRONG IS THE EVIDENCE?',
            'Single-Location Trend Trajectory & Uncertainty Lens',
            'Inspect the annual series, linear slope, and OLS vs. raw HAC vs. cautious max(SE_OLS, SE_HAC) intervals.',
            badge=f'{start}–{end} · {interval_mode.upper()}',
        )

        if result:
            active_ci = result['ci95'] if interval_mode != 'conventional' else result['iid_ci95']
            c1, c2, c3, c4 = st.columns([1, 1.35, 1.35, 0.8])
            c1.metric('Estimated slope / decade', f"{format_bound(result['slope_decade'])} {unit}")
            c2.metric(active_ci_label, format_interval(active_ci, unit))
            c3.metric('Conventional 95% CI (OLS)', format_interval(result['iid_ci95'], unit))
            c4.metric('Complete years', str(result['n']))

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=frame.year,
                y=frame.value,
                mode='lines+markers',
                name='Annual estimate',
                line=dict(color=SITE_A_COLOR, width=2.2),
                marker=dict(size=6, symbol='circle'),
                hovertemplate='%{x}: %{y:.2f} ' + unit + '<extra></extra>',
            )
        )
        if result:
            fig.add_trace(
                go.Scatter(
                    x=frame.year,
                    y=result['fitted'],
                    name='Linear fit',
                    line=dict(color=SITE_B_COLOR, width=3.2, dash='dash'),
                )
            )
        fig.update_layout(
            height=380,
            template='plotly_white',
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=dict(family='Arial, sans-serif', color=INK_COLOR, size=13),
            margin=dict(l=48, r=20, t=36, b=36),
            legend=dict(orientation='h', y=1.08, x=0.0),
            xaxis_title='Calendar year',
            yaxis_title=f'{name} ({unit})',
            hovermode='x unified',
        )
        st.plotly_chart(fig, use_container_width=True)

        if result:
            sig = site_eval['active_excludes_zero']
            direction = 'increase' if result['slope_decade'] > 0 else 'decrease'
            st.subheader('What the evidence says')
            st.write(
                f"For the NASA MERRA-2 grid representation of this location, the fitted {name.lower()} shows an estimated "
                f"{direction} of {abs(result['slope_decade']):.2f} {unit} per decade ({result['slope_decade']:+.5f} {rate_unit}) "
                f"during {result['start']}–{result['end']} ({result['n']} complete years). "
                + (
                    f"Under the `{interval_mode}` assumption, the exploratory 95% interval ({format_interval(active_ci, rate_unit)}) excludes zero."
                    if sig
                    else f"Under the `{interval_mode}` assumption, the exploratory 95% interval ({format_interval(active_ci, rate_unit)}) includes zero: "
                    "this analysis does not establish a consistent linear trend."
                )
            )
            render_uncertainty_lens_panel(
                [(location, result)],
                interval_mode,
                unit,
                rate_unit,
                show_control=False,
            )

        left, right = st.columns([1.2, 1])
        with left:
            st.subheader('A transparent chain of evidence')
            st.write(
                'NASA POWER supplies MERRA-2 gridded reanalysis estimates. Temperature is the day-weighted annual mean at 2 metres. '
                'Annual precipitation sums each monthly mean daily rate multiplied by the number of calendar days. '
                'All 12 valid months are required.'
            )
            st.write(
                'Annual aggregation removes the regular within-year seasonal cycle. Linear regression describes the selected period. '
                'HAC uncertainty allows short-range residual autocorrelation and unequal variance. '
                'Neither the model nor statistical significance establishes causation.'
            )
        with right:
            st.subheader('Read the limits')
            st.write(
                'These are grid estimates, not direct city weather-station measurements. Coastal and mountainous terrain can differ '
                'within a grid cell. Trends depend on period, model quality and linearity. Long-memory dependence, changing observing '
                'systems and repeated exploratory tests may affect inference. No correction for searching many locations is applied.'
            )

        with st.expander('Source metadata, statistics and reproducibility'):
            st.json(
                {
                    'NASA_header': data['header'],
                    'NASA_parameters': data['parameters'],
                    'returned_point': data['geometry'],
                    'retrieval': data.get('_earthpulse', {}),
                    'analysis': {k: v for k, v in (result or {}).items() if k != 'fitted'},
                }
            )
            st.markdown(
                '[NASA POWER monthly API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) · '
                '[MERRA-2](https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/)'
            )
            if data.get('_earthpulse', {}).get('request_url'):
                st.link_button('Open the exact NASA request', data['_earthpulse']['request_url'])

        export = frame.assign(
            parameter=parameter,
            units=unit,
            latitude=lat,
            longitude=lon,
            source='NASA POWER / MERRA-2',
        )
        render_evidence_passport_section(
            question=f"Is {name.lower()} changing at {location} ({start}–{end})?",
            parameter=parameter,
            start=start,
            end=end,
            loc_a=location,
            lat_a=lat,
            lon_a=lon,
            data_a=data,
            single_site=site_eval,
            interval_mode=interval_mode,
            key_prefix='single_passport',
            export_df=export,
            export_csv_name=f'earthpulse_{location}_{parameter}_{start}_{end}.csv',
        )
    except Exception as error:
        st.error(f'Unable to complete this investigation: {error}')
        st.info('Try a bundled example for 1991–2025, or retry the live API later. No synthetic data will be substituted.')
