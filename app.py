"""EarthPulse V2 interface."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from analysis import (
    LOCATIONS,
    VARIABLES,
    annual_series,
    compare_locations,
    evaluate_site,
    excludes_zero,
    fetch_power,
    format_bound,
    format_interval,
    trend,
)

st.set_page_config(
    page_title='EarthPulse · Climate Trend Detective',
    page_icon='◉',
    layout='wide',
    initial_sidebar_state='collapsed',
)

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
    padding-top: 2.6rem !important;
    padding-bottom: 2.5rem !important;
}
h1, h2, h3, .editorial-headline {
    font-family: Georgia, "Times New Roman", serif !important;
    color: #14282d;
    letter-spacing: -0.025em;
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
    font-size: clamp(1.75rem, 2.45vw, 2.35rem);
    line-height: 1.12;
    font-weight: 700;
    margin: 0.1rem 0 0.3rem 0;
    color: #14282d;
}
.verdict-lead {
    font-size: 1.02rem;
    line-height: 1.48;
    color: #243b40;
    max-width: 1180px;
    margin: 0 0 0.65rem 0;
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
    border: 0;
}
a {
    color: #15616d;
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
                name='Cautious 95% CI (HAC / max SE)',
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
                    f"<b>{s['location']} · Cautious 95% CI (HAC / max SE)</b><br>"
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


def build_morocco_grid_map(parameter, start=1991, end=2025):
    """Build a spatial overview map of the four Moroccan MERRA-2 grid representations and their decadal slopes."""
    unit = VARIABLES[parameter][1]
    rate_unit = f"{unit}/decade"
    lats, lons, names, texts, colors_list, symbols = [], [], [], [], [], []
    regime_notes = {
        'Casablanca': 'Atlantic Coastal Plain',
        'Rabat': 'Northern Atlantic Coast',
        'Marrakech': 'Haouz Plain / Atlas Foothills',
        'Ouarzazate': 'Pre-Saharan High Atlas Rain Shadow',
    }
    for city, (clat, clon) in LOCATIONS.items():
        snap = Path(__file__).parent / 'data' / f'{city.lower()}.json'
        if not snap.exists():
            continue
        cdata = json.loads(snap.read_text())
        ev = evaluate_site(city, cdata, parameter, start, end)
        lats.append(clat)
        lons.append(clon)
        if ev['eligible']:
            r = ev['result']
            sl_short = f"{format_bound(r['slope_decade'])} {unit}/dec"
            sl_str = f"{format_bound(r['slope_decade'])} {rate_unit}"
            ci_str = format_interval(r['ci95'], rate_unit)
            status = ev['cautious_status']
            col = SITE_B_COLOR if ev['cautious_excludes_zero'] else SITE_A_COLOR
            sym = 'diamond' if ev['cautious_excludes_zero'] else 'circle'
        else:
            sl_short = 'Ineligible'
            sl_str = 'Ineligible (<30 yr)'
            ci_str = 'N/A'
            status = 'Ineligible'
            col = '#6e4b0c'
            sym = 'circle-open'
        names.append(f"<b>{city}</b><br>{sl_short}")
        texts.append(
            f"<b>{city}</b> · {regime_notes.get(city, '')}<br>"
            f"MERRA-2 center: {clat:.2f}°N, {clon:.2f}°E<br>"
            f"Slope: {sl_str}<br>"
            f"Cautious 95% CI: {ci_str}<br>"
            f"Verdict: {status}"
        )
        colors_list.append(col)
        symbols.append(sym)

    fig = go.Figure(
        go.Scattergeo(
            lat=lats,
            lon=lons,
            text=names,
            customdata=texts,
            mode='markers+text',
            textposition=['middle left', 'top right', 'middle left', 'bottom right'],
            textfont=dict(family='Arial, sans-serif', size=11.5, color=INK_COLOR),
            marker=dict(
                size=14,
                color=colors_list,
                symbol=symbols,
                line=dict(width=2, color='#ffffff'),
            ),
            hovertemplate='%{customdata}<extra></extra>',
        )
    )
    fig.update_geos(
        scope='africa',
        center=dict(lat=32.4, lon=-7.4),
        lataxis_range=[28.6, 36.2],
        lonaxis_range=[-13.2, -1.8],
        showland=True,
        landcolor='#efeadd',
        showocean=True,
        oceancolor='#dcebed',
        showcountries=True,
        countrycolor='#b8b09c',
        showcoastlines=True,
        coastlinecolor='#7a9a9f',
        projection_type='mercator',
    )
    fig.update_layout(
        height=320,
        paper_bgcolor=CHART_BG,
        margin=dict(l=4, r=4, t=8, b=8),
        showlegend=False,
    )
    return fig


def build_evidence_brief_markdown(comp, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b):
    """Create a one-page reproducible Markdown Evidence Brief for download."""
    sa, sb = comp['site_a'], comp['site_b']
    rate_unit = comp['rate_unit']
    lines = [
        f"# EarthPulse V2 — Evidence Brief: {loc_a} vs. {loc_b}",
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
st.markdown(
    '<div class="eyebrow-row">'
    '<span class="eyebrow">EARTHPULSE LABS · MERRA-2 GRIDDED CLIMATE TREND DETECTIVE</span>'
    '<span class="provenance-badge">NASA POWER / MERRA-2 · 30-Year Consecutive Rule · Newey–West HAC Screen</span>'
    '</div>',
    unsafe_allow_html=True,
)

nav_choice = st.radio(
    'Investigation mode',
    options=['Compare: The Trend Verdict', 'Single Location & Custom Coordinates'],
    index=0,
    horizontal=True,
    label_visibility='collapsed',
)

active_view = 'compare' if nav_choice.startswith('Compare') else 'single'

if active_view == 'compare':
    loc_names = list(LOCATIONS.keys())
    lens_map = {
        'Show both: Cautious (HAC) + Conventional (OLS)': ('cautious', 'both'),
        'Cautious 95% screen (accounts for time dependence)': ('cautious', 'cautious'),
        'Conventional 95% OLS (assumes independent years)': ('conventional', 'conventional'),
    }

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

    lens_label = st.radio(
        'What changes when we account for time dependence?',
        [
            'Show both: Cautious (HAC) + Conventional (OLS)',
            'Cautious 95% screen (accounts for time dependence)',
            'Conventional 95% OLS (assumes independent years)',
        ],
        index=0,
        horizontal=True,
        key='comp_lens',
    )

    interval_mode, whisker_lens = lens_map[lens_label]
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
                f'<div class="chart-header-sub">Zero reference line (0.0) · Cautious HAC screen vs. Conventional OLS</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(build_whisker_figure(comp, whisker_lens), use_container_width=True)

        # --- Compact Evidence Panel: "What changes when we account for time dependence?" ---
        sa, sb = comp['site_a'], comp['site_b']
        rate_unit = comp['rate_unit']
        if comp['both_eligible']:
            ra, rb = sa['result'], sb['result']

            def _badge(excludes):
                cls = 'badge-clear' if excludes else 'badge-cautious'
                txt = 'Excludes 0' if excludes else 'Crosses 0'
                return f'<span class="{cls}">{txt}</span>'

            table_html = (
                f'<div class="evidence-panel">'
                f'<h4>What changes when we account for time dependence? · Exploratory 95% Interval Comparison ({start}–{end}, n = {ra["n"]} complete years)</h4>'
                f'<p>{comp["time_dependence_note"]}</p>'
                f'<table class="verdict-table" aria-label="Comparison of conventional OLS and cautious HAC-adjusted trend intervals">'
                f'<thead><tr>'
                f'<th>Grid Representation (MERRA-2)</th>'
                f'<th>Slope / Decade ({rate_unit})</th>'
                f'<th>Conventional 95% CI (OLS, independent years)</th>'
                f'<th>Cautious 95% Screen (Larger of OLS &amp; HAC, {ra["hac_lags"]} lags)</th>'
                f'<th>Residual Lag-1 (ρ₁) &amp; R²</th>'
                f'</tr></thead>'
                f'<tbody>'
                f'<tr>'
                f'<td><b>● {loc_a}</b> ({lat_a:.2f}°N, {lon_a:.2f}°E)</td>'
                f'<td><b>{format_bound(ra["slope_decade"])}</b> <span style="color:#52656b;font-size:0.81rem;">({ra["slope_decade"]:+.5f})</span></td>'
                f'<td>{format_interval(ra["iid_ci95"], rate_unit)} (p = {ra["iid_p"]:.4g}) {_badge(sa["iid_excludes_zero"])}</td>'
                f'<td><b>{format_interval(ra["ci95"], rate_unit)}</b> <span style="color:#52656b;font-size:0.81rem;">[{ra["ci95"][0]:+.5f}, {ra["ci95"][1]:+.5f}]</span> (p = {ra["p_value"]:.4g}) {_badge(sa["cautious_excludes_zero"])}</td>'
                f'<td>ρ₁ = {ra["residual_lag1"]:+.2f} · R² = {ra["r_squared"]:.2f}</td>'
                f'</tr>'
                f'<tr>'
                f'<td><b>◆ {loc_b}</b> ({lat_b:.2f}°N, {lon_b:.2f}°E)</td>'
                f'<td><b>{format_bound(rb["slope_decade"])}</b> <span style="color:#52656b;font-size:0.81rem;">({rb["slope_decade"]:+.5f})</span></td>'
                f'<td>{format_interval(rb["iid_ci95"], rate_unit)} (p = {rb["iid_p"]:.4g}) {_badge(sb["iid_excludes_zero"])}</td>'
                f'<td><b>{format_interval(rb["ci95"], rate_unit)}</b> <span style="color:#52656b;font-size:0.81rem;">[{rb["ci95"][0]:+.5f}, {rb["ci95"][1]:+.5f}]</span> (p = {rb["p_value"]:.4g}) {_badge(sb["cautious_excludes_zero"])}</td>'
                f'<td>ρ₁ = {rb["residual_lag1"]:+.2f} · R² = {rb["r_squared"]:.2f}</td>'
                f'</tr>'
                f'</tbody></table>'
                f'<div class="caveat-strip">'
                f'<b>Interpretation boundary:</b> {comp["overlap_note"]} Source: {source_tag}.'
                f'</div>'
                f'</div>'
            )
            st.markdown(table_html, unsafe_allow_html=True)
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

        # --- Interactive Scientific Diagnostics (Deep-Dive Tabs) ---
        tab_resid, tab_matrix, tab_window, tab_map = st.tabs([
            '1. Residual Persistence (ρ₁)',
            '2. Four Moroccan Regimes',
            '3. Window Stability (30+ yr)',
            '4. Morocco Grid Map & HAC',
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

        with tab_map:
            map_start, map_end = max(1991, start), min(2025, end)
            m_col1, m_col2 = st.columns([1.15, 1.0])
            with m_col1:
                st.markdown(
                    f'<div class="chart-header-box">'
                    f'<div class="chart-header-title">MERRA-2 Grid-Cell Locations Across Morocco (Bundled {map_start}–{map_end})</div>'
                    f'<div class="chart-header-sub">Teal circles (●) cross zero; ochre diamonds (◆) exclude zero under cautious HAC screen</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(build_morocco_grid_map(parameter, map_start, map_end), use_container_width=True)
            with m_col2:
                st.markdown('#### Standard Error Inflation Factor (HAC vs. OLS)')
                if comp['both_eligible']:
                    ra, rb = sa['result'], sb['result']
                    w_iid_a = ra['iid_ci95'][1] - ra['iid_ci95'][0]
                    w_hac_a = ra['ci95'][1] - ra['ci95'][0]
                    inf_a = (w_hac_a / w_iid_a) if w_iid_a > 0 else 1.0

                    w_iid_b = rb['iid_ci95'][1] - rb['iid_ci95'][0]
                    w_hac_b = rb['ci95'][1] - rb['ci95'][0]
                    inf_b = (w_hac_b / w_iid_b) if w_iid_b > 0 else 1.0

                    st.write(
                        f"- **{loc_a}**: Cautious interval width is **{inf_a:.2f}×** the conventional OLS width "
                        f"(`{w_hac_a:.3f}` vs. `{w_iid_a:.3f} {rate_unit}`, driven by lag-1 autocorrelation "
                        f"**ρ₁ = {ra['residual_lag1']:+.2f}**)."
                    )
                    st.write(
                        f"- **{loc_b}**: Cautious interval width is **{inf_b:.2f}×** the conventional OLS width "
                        f"(`{w_hac_b:.3f}` vs. `{w_iid_b:.3f} {rate_unit}`, **ρ₁ = {rb['residual_lag1']:+.2f}**)."
                    )
                    st.caption(
                        'Each NASA POWER point query returns the MERRA-2 reanalysis value for its ~0.5° × 0.625° '
                        'regional grid cell, smoothing local coastal breezes and mountain elevation gradients.'
                    )
                else:
                    st.info('Select a 30+ year consecutive window to compute HAC/OLS uncertainty inflation factors.')

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

        dl1, dl2, dl3, dl4 = st.columns(4)
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
        dl1.download_button(
            f'Download annual data · CSV ({loc_a} & {loc_b})',
            export_df.to_csv(index=False),
            f'earthpulse_compare_{loc_a}_{loc_b}_{parameter}_{start}_{end}.csv',
            'text/csv',
        )
        dl2.download_button(
            'Download Evidence Brief · MD',
            brief_md,
            f'earthpulse_brief_{loc_a}_{loc_b}_{parameter}_{start}_{end}.md',
            'text/markdown',
        )
        dl3.download_button(
            f'Download {loc_a} NASA · JSON',
            json.dumps(data_a, indent=2),
            f'earthpulse_{loc_a}_NASA.json',
            'application/json',
        )
        dl4.download_button(
            f'Download {loc_b} NASA · JSON',
            json.dumps(data_b, indent=2),
            f'earthpulse_{loc_b}_NASA.json',
            'application/json',
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

    start, end = period
    try:
        with st.spinner('Retrieving NASA POWER climate estimates…'):
            data, bundled = load_location_data(location, lat, lon, start, end, data_mode)

        frame, omitted = annual_series(data, parameter, start, end)
        name, unit = VARIABLES[parameter]
        rate_unit = f"{unit}/decade"
        st.caption(
            f"{location} ({lat:.4f}°, {lon:.4f}°)  /  {name} ({unit})  /  {start}–{end}  /  "
            f"{'Bundled real NASA response' if bundled else 'Live NASA API response (cached for up to 24 hours)'}"
        )
        if omitted:
            st.warning('Incomplete years excluded: ' + ', '.join(map(str, omitted)) + '. No values have been interpolated.')

        result = None
        try:
            result = trend(frame)
        except ValueError as error:
            st.warning(str(error))

        if result:
            c1, c2, c3, c4 = st.columns([1, 1.35, 1.35, 0.8])
            c1.metric('Estimated slope / decade', f"{format_bound(result['slope_decade'])} {unit}")
            c2.metric('Cautious 95% CI (HAC / max SE)', format_interval(result['ci95'], unit))
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
            sig = excludes_zero(result['ci95'])
            direction = 'increase' if result['slope_decade'] > 0 else 'decrease'
            st.subheader('What the evidence says')
            st.write(
                f"For the NASA MERRA-2 grid representation of this location, the fitted {name.lower()} shows an estimated "
                f"{direction} of {abs(result['slope_decade']):.2f} {unit} per decade ({result['slope_decade']:+.5f} {rate_unit}) "
                f"during {result['start']}–{result['end']} ({result['n']} complete years). "
                + (
                    f"The cautious exploratory 95% interval ({format_interval(result['ci95'], rate_unit)}) excludes zero."
                    if sig
                    else f"The cautious exploratory 95% interval ({format_interval(result['ci95'], rate_unit)}) includes zero: "
                    "this analysis does not establish a consistent linear trend."
                )
            )
            st.caption(
                f"Exploratory two-sided cautious p = {result['p_value']:.4g} (conventional OLS 95% CI: "
                f"{format_interval(result['iid_ci95'], rate_unit)}, OLS p = {result['iid_p']:.4g}, "
                f"residual lag-1 ρ₁ = {result['residual_lag1']:+.2f}). "
                f"We use the larger standard error from ordinary and Newey–West HAC regression ({result['hac_lags']} annual lags)."
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

        a, b = st.columns(2)
        export = frame.assign(
            parameter=parameter,
            units=unit,
            latitude=lat,
            longitude=lon,
            source='NASA POWER / MERRA-2',
        )
        a.download_button(
            'Download annual data · CSV',
            export.to_csv(index=False),
            f'earthpulse_{location}_{parameter}_{start}_{end}.csv',
            'text/csv',
        )
        b.download_button(
            'Download source response · JSON',
            json.dumps(data, indent=2),
            f'earthpulse_{location}_NASA.json',
            'application/json',
        )
    except Exception as error:
        st.error(f'Unable to complete this investigation: {error}')
        st.info('Try a bundled example for 1991–2025, or retry the live API later. No synthetic data will be substituted.')
