"""Shared Earth Investigation Studio UI chrome, Plotly figures, and 4-level scientific cards."""
from __future__ import annotations

from html import escape
import plotly.graph_objects as go
import streamlit as st

import analysis


STUDIO_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,600;6..72,700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

:root {
  --ep-ink: #0f2027;
  --ep-muted: #3d525c;
  --ep-paper: #faf8f4;
  --ep-card: #ffffff;
  --ep-border: #d5cfc2;
  --ep-teal: #0d7a72;
  --ep-teal-soft: #e6f4f2;
  --ep-amber: #b45309;
  --ep-amber-soft: #fef3c7;
  --ep-slate: #475569;
  --ep-slate-soft: #f1f5f9;
}

.stApp {
  background-color: var(--ep-paper);
  color: var(--ep-ink);
  font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

.ep-masthead {
  background: linear-gradient(120deg, #0b1824 0%, #102a3a 65%, #123c45 100%);
  color: #f8fafc;
  border-radius: 14px;
  padding: 1.35rem 1.65rem;
  border-bottom: 4px solid #d97706;
  margin-bottom: 1rem;
}

.ep-kicker {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #5eead4;
  margin: 0 0 0.35rem 0;
}

.ep-h1 {
  font-family: 'Newsreader', Georgia, serif;
  font-size: clamp(1.65rem, 3.2vw, 2.35rem);
  line-height: 1.15;
  font-weight: 700;
  margin: 0 0 0.4rem 0;
  color: #ffffff;
  text-wrap: balance;
}

.ep-tagline {
  font-size: clamp(0.95rem, 1.5vw, 1.08rem);
  color: #cbd5e1;
  max-inline-size: 74ch;
  margin: 0;
  text-wrap: pretty;
}

.ep-journey {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: 0.6rem 0 1.15rem 0;
}

.ep-step-pill {
  background: var(--ep-card);
  border: 1px solid var(--ep-border);
  border-radius: 999px;
  padding: 0.3rem 0.75rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--ep-muted);
}

.ep-step-pill.is-active {
  background: #0b1824;
  color: #5eead4;
  border-color: #0d9488;
}

.ep-sec-kicker {
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ep-teal);
  margin: 1.1rem 0 0.25rem 0;
}

.ep-h2 {
  font-family: 'Newsreader', Georgia, serif;
  font-size: clamp(1.25rem, 2.2vw, 1.65rem);
  font-weight: 700;
  color: var(--ep-ink);
  margin: 0 0 0.45rem 0;
  text-wrap: balance;
}

.ep-prose {
  max-inline-size: 76ch;
  font-size: 0.96rem;
  line-height: 1.6;
  color: var(--ep-muted);
  text-wrap: pretty;
}

.ep-verdict-box {
  background: var(--ep-card);
  border: 1px solid var(--ep-border);
  border-left: 5px solid var(--ep-teal);
  border-radius: 10px;
  padding: 1rem 1.2rem;
  margin: 0.75rem 0;
  min-block-size: 4rem;
}

.ep-verdict-box.is-amber {
  border-left-color: var(--ep-amber);
  background: #fffdf7;
}

.ep-verdict-box.is-slate {
  border-left-color: var(--ep-slate);
  background: #f8fafc;
}

.ep-badge {
  display: inline-block;
  font-size: 0.74rem;
  font-weight: 700;
  padding: 0.16rem 0.55rem;
  border-radius: 6px;
  margin-bottom: 0.4rem;
}

.ep-badge.is-amber { background: var(--ep-amber-soft); color: #78350f; border: 1px solid #f59e0b; }
.ep-badge.is-teal { background: var(--ep-teal-soft); color: #0f4c46; border: 1px solid #0d9488; }
.ep-badge.is-slate { background: var(--ep-slate-soft); color: #1e293b; border: 1px solid #94a3b8; }

.ep-level-card {
  background: var(--ep-card);
  border: 1px solid var(--ep-border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  min-block-size: 100%;
}

@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; }
}
</style>
"""


def inject_studio_styles() -> None:
    st.markdown(STUDIO_STYLES, unsafe_allow_html=True)


def render_masthead(
    title: str = 'The climate tells a story. Can you prove it?',
    subtitle: str = 'From the planet to the proof. Explore NASA terrain and regional grid footprints in 3D, challenge statistical verdicts, and download a one-page SHA-256 verifiable Evidence Passport.',
) -> None:
    st.markdown(
        f"""
        <header class="ep-masthead" role="banner">
          <p class="ep-kicker">EARTHPULSE · EARTH INVESTIGATION STUDIO · NASA SPACE APPS 2026</p>
          <h1 class="ep-h1">{escape(title)}</h1>
          <p class="ep-tagline">{escape(subtitle)}</p>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_journey_bar(active_step: int = 1) -> None:
    steps = [
        (1, '1 · Explore 3D Earth'),
        (2, '2 · Question'),
        (3, '3 · Predict'),
        (4, '4 · Test Data'),
        (5, '5 · Challenge Assumptions'),
        (6, '6 · Verify Passport'),
    ]
    pills = []
    for num, label in steps:
        cls = 'ep-step-pill is-active' if num == active_step else 'ep-step-pill'
        pills.append(f'<span class="{cls}">{escape(label)}</span>')
    st.markdown(f'<nav class="ep-journey" aria-label="Investigation steps">{"".join(pills)}</nav>', unsafe_allow_html=True)


def render_four_level_summary(
    plain_answer: str,
    key_numbers: str,
    statistical_method: str,
    provenance_text: str,
) -> None:
    """Render the 4-level scientific communication hierarchy without truncating text height."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""
            <div class="ep-level-card">
              <div class="ep-sec-kicker" style="margin-top:0;">LEVEL 1 · PLAIN-LANGUAGE ANSWER</div>
              <p class="ep-prose" style="margin:0;">{escape(plain_answer)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="ep-level-card">
              <div class="ep-sec-kicker" style="margin-top:0;">LEVEL 2 · KEY NUMBERS & INTERVALS</div>
              <p class="ep-prose" style="margin:0;">{escape(key_numbers)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(
            f"""
            <div class="ep-level-card" style="margin-top:0.6rem;">
              <div class="ep-sec-kicker" style="margin-top:0;">LEVEL 3 · STATISTICAL METHOD</div>
              <p class="ep-prose" style="margin:0;">{escape(statistical_method)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="ep-level-card" style="margin-top:0.6rem;">
              <div class="ep-sec-kicker" style="margin-top:0;">LEVEL 4 · NASA SOURCE & INTEGRITY</div>
              <p class="ep-prose" style="margin:0;">{escape(provenance_text)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_seasonal_whisker_fig(fingerprints: dict) -> go.Figure:
    """Build 4-season (DJF, MAM, JJA, SON) + Annual dot-and-whisker 95% CI plot against 0."""
    fig = go.Figure()
    rate_unit = fingerprints['rate_unit']
    rows = []
    for code in ('DJF', 'MAM', 'JJA', 'SON'):
        s = fingerprints['seasons'].get(code, {})
        if s.get('eligible'):
            rows.append((
                f"{s['label']} (n={s['n']})",
                float(s['slope_decade']),
                float(s['active_ci'][0]),
                float(s['active_ci'][1]),
                bool(s['excludes_zero']),
                'diamond' if s['excludes_zero'] else 'circle',
            ))
    ann = fingerprints.get('annual') or {}
    if ann.get('eligible'):
        ar = ann['result']
        rows.append((
            f"Annual baseline (n={ar['n']})",
            float(ar['slope_decade']),
            float(ann['active_ci'][0]),
            float(ann['active_ci'][1]),
            bool(ann['active_excludes_zero']),
            'square',
        ))

    rows_rev = list(reversed(rows))
    for idx, (label, est, lo, hi, ex0, sym) in enumerate(rows_rev):
        color = '#b45309' if (ex0 and est > 0) else ('#0d7a72' if ex0 else '#475569')
        status = 'Excludes zero' if ex0 else 'Crosses zero (inconclusive)'
        fig.add_trace(go.Scatter(
            x=[lo, hi],
            y=[label, label],
            mode='lines+markers',
            line=dict(color=color, width=3.5),
            marker=dict(symbol='line-ns-open', size=11, color=color, line=dict(width=2, color=color)),
            hoverinfo='skip',
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[est],
            y=[label],
            mode='markers+text',
            marker=dict(symbol=sym, size=12, color=color, line=dict(color='#ffffff', width=1.4)),
            text=[f"{analysis.format_bound(est)} ({'Excl. 0' if ex0 else 'Crosses 0'})"],
            textposition='top center',
            textfont=dict(size=11, color='#0f2027'),
            hovertemplate=f"<b>{label}</b><br>Slope: {analysis.format_bound(est)} {rate_unit}<br>95% CI: [{lo:+.3f}, {hi:+.3f}]<br>{status}<extra></extra>",
            showlegend=False,
        ))

    fig.add_vline(x=0.0, line_dash='dash', line_color='#64748b', line_width=1.6, annotation_text='Zero trend', annotation_position='top')
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='#ffffff',
        plot_bgcolor='#faf8f4',
        height=310,
        margin=dict(l=20, r=24, t=34, b=42),
        xaxis_title=f"Estimated Decadal Slope ({rate_unit}) — Exploratory 95% Interval",
        yaxis_title='',
    )
    return fig


def build_diff_trial_fig(trial: dict, loc_a: str, loc_b: str, rate_unit: str, unit: str) -> go.Figure:
    """Plot paired annual difference D(year) = B(year) - A(year) with OLS trend line."""
    fig = go.Figure()
    df = trial['diff_frame']
    dr = trial['diff_result']
    ex0 = trial['active_excludes_zero']
    line_col = '#b45309' if (ex0 and dr['slope_decade'] > 0) else ('#0d7a72' if ex0 else '#475569')

    fig.add_hline(y=0.0, line_dash='dot', line_color='#64748b', line_width=1.5)
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['value'],
        mode='lines+markers',
        name=f"D(year) = {loc_b} - {loc_a}",
        line=dict(color='#94a3b8', width=1.8),
        marker=dict(size=6, color=line_col, symbol='diamond' if ex0 else 'circle'),
        hovertemplate='Year %{x}: D = %{y:+.2f} ' + unit + '<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=dr['fitted'],
        mode='lines',
        name=f"OLS trend ({analysis.format_bound(dr['slope_decade'])} {rate_unit})",
        line=dict(color=line_col, width=3.0, dash='dash'),
    ))
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='#ffffff',
        plot_bgcolor='#faf8f4',
        height=300,
        margin=dict(l=46, r=20, t=32, b=36),
        xaxis_title='Year (paired shared complete years)',
        yaxis_title=f"Annual difference D ({unit})",
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0),
    )
    return fig


def build_dual_city_fig(site_a: dict, site_b: dict, parameter: str) -> go.Figure:
    """Plot two annual climate series side-by-side in one clear chart."""
    _, unit = analysis.ALL_VARIABLES[parameter]
    fig = go.Figure()
    for site, col, sym in ((site_a, '#0d7a72', 'circle'), (site_b, '#b45309', 'diamond')):
        df = site['frame']
        loc = site['location']
        fig.add_trace(go.Scatter(
            x=df['year'],
            y=df['value'],
            mode='lines+markers',
            name=f"{loc} observed",
            line=dict(color=col, width=1.8),
            marker=dict(size=5, symbol=sym, color=col),
        ))
        if site.get('eligible'):
            fig.add_trace(go.Scatter(
                x=df['year'],
                y=site['result']['fitted'],
                mode='lines',
                name=f"{loc} trend ({analysis.format_bound(site['result']['slope_decade'])} {unit}/dec)",
                line=dict(color=col, width=2.8, dash='dash'),
            ))
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='#ffffff',
        plot_bgcolor='#faf8f4',
        height=310,
        margin=dict(l=48, r=20, t=32, b=36),
        xaxis_title='Calendar year',
        yaxis_title=f"{analysis.ALL_VARIABLES[parameter][0]} ({unit})",
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0),
    )
    return fig
