"""EarthPulse — The Climate Trial interactive Arabic RTL scientific interface."""
import html
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
    climate_trial,
    compare_locations,
    evaluate_site,
    extract_grid_metadata,
    fetch_power,
    format_bound,
    format_interval,
    source_sha256,
    uncertainty_lens_summary,
)
from brief_pdf import build_scientific_evidence_brief_pdf

st.set_page_config(
    page_title='نبض الأرض · EarthPulse — محاكمة المناخ',
    page_icon='◉',
    layout='wide',
    initial_sidebar_state='collapsed',
)

# --- Editorial & Scientific RTL Styling ---
st.markdown(
    """<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Tajawal:wght@400;500;700&display=swap');

:root {
    --ep-paper: #f5f2eb;
    --ep-card: #ece8de;
    --ep-surface: #faf8f3;
    --ep-border: #d0c9b8;
    --ep-ink: #14282d;
    --ep-muted: #2f474d;
    --ep-teal: #15616d;
    --ep-ochre: #b55327;
}

html, body, .stApp {
    background-color: var(--ep-paper);
    color: var(--ep-ink);
    max-width: 100%;
    overflow-x: clip !important;
    font-family: 'Cairo', 'Tajawal', 'Geeza Pro', 'Tahoma', 'Arial', sans-serif !important;
}

/* Keep top flex layout LTR so Streamlit sidebar collapse mechanics never leak vertically */
[data-testid="stAppViewContainer"] {
    background-color: var(--ep-paper);
    direction: ltr;
    max-width: 100%;
    overflow-x: clip !important;
}

section[data-testid="stMain"] .block-container,
[data-testid="stSidebarContent"] {
    direction: rtl;
    text-align: right;
    font-family: 'Cairo', 'Tajawal', 'Geeza Pro', 'Tahoma', 'Arial', sans-serif !important;
}

[data-testid="stRadio"] div[role="radiogroup"] {
    gap: 0.9rem 1.25rem;
    flex-wrap: wrap;
}

[data-baseweb="slider"],
[data-testid="stSliderTickBar"],
[data-testid="stSlider"] > div:last-child {
    direction: ltr !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
    height: 2.2rem !important;
    direction: ltr;
}

.block-container {
    max-width: 1380px;
    padding-top: 2.95rem !important;
    padding-bottom: 2.5rem !important;
}

p, li, div, span, label, caption, td, th, button {
    font-family: 'Cairo', 'Tajawal', 'Geeza Pro', 'Tahoma', 'Arial', sans-serif;
}

h1, h2, h3, .editorial-headline, .step-title {
    font-family: 'Cairo', 'Tajawal', 'Geeza Pro', 'Tahoma', 'Arial', sans-serif !important;
    color: var(--ep-ink);
    text-wrap: balance;
    line-height: 1.32;
}

.ltr-num {
    direction: ltr;
    unicode-bidi: isolate;
    display: inline-block;
    font-variant-numeric: tabular-nums;
}

code, pre, [data-testid="stJson"] {
    direction: ltr;
    unicode-bidi: isolate;
    text-align: left;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
}

div[data-testid="stPlotlyChart"] {
    direction: ltr;
    background: #f9f7f2;
    border: 1px solid #d6d0c2;
    border-radius: 0 0 6px 6px;
    padding: 0.15rem 0.25rem 0.1rem 0.25rem;
    margin-bottom: 0.45rem;
}

.eyebrow-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    border-bottom: 1px solid #d6d0c2;
    padding-bottom: 0.4rem;
    margin-bottom: 0.55rem;
}

.eyebrow {
    font-size: 0.84rem;
    color: var(--ep-teal);
    font-weight: 800;
}

.provenance-badge {
    font-size: 0.8rem;
    color: var(--ep-muted);
    background: #e7e2d5;
    padding: 0.18rem 0.7rem;
    border-radius: 999px;
    border: 1px solid #d0c9b8;
    font-weight: 600;
}

.editorial-headline {
    font-size: clamp(1.55rem, 1.15rem + 1.8vw, 2.3rem);
    font-weight: 800;
    margin: 0.15rem 0 0.35rem 0;
    color: var(--ep-ink);
}

.verdict-lead, .trial-subq, .evidence-panel p, .step-banner-sub {
    line-height: 1.68;
    color: #243b40;
    max-width: 75ch;
    text-wrap: pretty;
    overflow-wrap: break-word;
    text-align: start;
}

.verdict-lead {
    font-size: 1.02rem;
    margin: 0 0 0.65rem 0;
}

.trial-tagline {
    font-size: 0.96rem;
    color: var(--ep-teal);
    font-weight: 700;
    margin: 0 0 0.22rem 0;
}

.trial-subq {
    font-size: 1.02rem;
    margin: 0 0 0.75rem 0;
}

.step-ribbon {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.65rem;
    margin: 0.4rem 0 0.85rem 0;
}

.step-card {
    background: var(--ep-card);
    border: 1px solid var(--ep-border);
    border-inline-start: 4px solid var(--ep-teal);
    border-radius: 6px;
    padding: 0.55rem 0.8rem;
}

.step-card-num {
    font-size: 0.76rem;
    font-weight: 800;
    color: var(--ep-teal);
}

.step-card-q {
    font-size: 0.98rem;
    font-weight: 700;
    color: var(--ep-ink);
    margin: 0.1rem 0;
}

.step-card-desc {
    font-size: 0.84rem;
    color: var(--ep-muted);
    line-height: 1.5;
}

.step-banner {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.45rem;
    border-top: 2px solid var(--ep-border);
    padding-top: 0.75rem;
    margin: 1rem 0 0.45rem 0;
}

.step-banner-kicker {
    font-size: 0.8rem;
    font-weight: 800;
    color: var(--ep-ochre);
}

.step-title {
    font-size: 1.28rem;
    font-weight: 800;
    margin: 0.08rem 0 0.15rem 0;
}

.step-banner-sub {
    font-size: 0.94rem;
    margin: 0 0 0.5rem 0;
}

.reality-callout {
    background: #f9f7f2;
    border: 1px solid #d6d0c2;
    border-inline-start: 4px solid var(--ep-ochre);
    border-radius: 6px;
    padding: 0.75rem 0.95rem;
    margin: 0.4rem 0 0.55rem 0;
    font-size: 0.88rem;
    color: #243b40;
    line-height: 1.65;
    overflow-wrap: break-word;
}

.passport-hero {
    background: var(--ep-card);
    border: 1px solid #cbc3b2;
    border-inline-start: 5px solid var(--ep-ink);
    border-radius: 8px;
    padding: 0.95rem 1.1rem;
    margin: 0.45rem 0 0.65rem 0;
}

.chart-header-box {
    background: var(--ep-card);
    border: 1px solid #d6d0c2;
    border-bottom: 0;
    border-radius: 6px 6px 0 0;
    padding: 0.55rem 0.9rem;
    margin-top: 0.15rem;
}

.chart-header-title {
    font-size: 1.02rem;
    font-weight: 700;
    color: var(--ep-ink);
    margin: 0;
}

.chart-header-sub {
    font-size: 0.84rem;
    color: #42595f;
    margin: 0.12rem 0 0 0;
    line-height: 1.48;
}

.evidence-panel {
    background: var(--ep-card);
    border: 1px solid #d6d0c2;
    border-inline-start: 4px solid var(--ep-teal);
    border-radius: 6px;
    padding: 0.85rem 1rem;
    margin-top: 0.25rem;
    margin-bottom: 0.75rem;
}

.city-card {
    background: var(--ep-surface);
    border: 1px solid #d6d0c2;
    border-radius: 8px;
    padding: 0.9rem 1rem;
    min-height: 100%;
}

.city-card-a {
    border-top: 4px solid var(--ep-teal);
}

.city-card-b {
    border-top: 4px solid var(--ep-ochre);
}

.city-card-kicker {
    font-size: 0.78rem;
    font-weight: 700;
    color: #485e64;
    margin-bottom: 0.15rem;
}

.city-card-name {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--ep-ink);
    margin-bottom: 0.25rem;
}

.city-card-rate {
    font-size: 1.5rem;
    font-weight: 800;
    margin: 0.2rem 0 0.35rem 0;
}

.city-card-meta {
    font-size: 0.86rem;
    color: #334a50;
    line-height: 1.56;
}

.vs-card {
    background: var(--ep-card);
    border: 1px solid #cbc3b2;
    border-radius: 8px;
    padding: 0.85rem 0.9rem;
    text-align: center;
}

.vs-pill {
    display: inline-block;
    background: var(--ep-ink);
    color: #f5f2eb;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    margin-bottom: 0.4rem;
    white-space: nowrap;
}

.vs-prompt {
    font-size: 0.86rem;
    color: #243b40;
    line-height: 1.52;
    margin: 0.2rem 0 0.45rem 0;
}

.verdict-banner {
    background: var(--ep-surface);
    border: 1px solid #cbc3b2;
    border-radius: 8px;
    padding: 1rem 1.15rem;
    margin: 0.6rem 0 0.8rem 0;
}

.verdict-positive {
    border-inline-start: 6px solid var(--ep-ochre);
}

.verdict-negative {
    border-inline-start: 6px solid var(--ep-teal);
}

.verdict-inconclusive {
    border-inline-start: 6px solid #6b7274;
}

.verdict-ineligible {
    border-inline-start: 6px solid #b88b2e;
}

.verdict-pill-pos {
    display: inline-block;
    background: #f6e3d8;
    color: #8a350f;
    border: 1px solid #d99b7e;
    font-weight: 800;
    font-size: 0.84rem;
    padding: 0.18rem 0.7rem;
    border-radius: 4px;
}

.verdict-pill-neg {
    display: inline-block;
    background: #dcebed;
    color: #124e57;
    border: 1px solid #8eb8be;
    font-weight: 800;
    font-size: 0.84rem;
    padding: 0.18rem 0.7rem;
    border-radius: 4px;
}

.verdict-pill-inc {
    display: inline-block;
    background: #e7e5df;
    color: #38494c;
    border: 1px solid #b5b0a4;
    font-weight: 800;
    font-size: 0.84rem;
    padding: 0.18rem 0.7rem;
    border-radius: 4px;
}

.verdict-pill-warn {
    display: inline-block;
    background: #f5e6c8;
    color: #6e4b0c;
    border: 1px solid #d4b475;
    font-weight: 800;
    font-size: 0.84rem;
    padding: 0.18rem 0.7rem;
    border-radius: 4px;
}

.trial-metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.65rem;
    margin: 0.65rem 0 0.6rem 0;
}

.trial-metric-box {
    background: #f1eee5;
    border: 1px solid #d8d1c2;
    border-radius: 6px;
    padding: 0.55rem 0.75rem;
}

.trial-metric-label {
    font-size: 0.78rem;
    color: #465c62;
    font-weight: 700;
}

.trial-metric-value {
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--ep-ink);
    margin-top: 0.12rem;
}

.trial-metric-sub {
    font-size: 0.78rem;
    color: #4e6368;
    margin-top: 0.08rem;
}

.table-wrapper {
    overflow: auto;
    max-inline-size: 100%;
    max-block-size: 340px;
    border: 1px solid #d6d0c2;
    border-radius: 6px;
    background: var(--ep-surface);
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
    font-size: 0.85rem;
    direction: rtl;
}

.table-wrapper thead th {
    position: sticky;
    inset-block-start: 0;
    z-index: 2;
    background: #e4dfd1;
    color: var(--ep-ink);
    padding: 0.5rem 0.65rem;
    text-align: start;
    border-bottom: 1px solid #cbc3b2;
    text-wrap: balance;
}

.table-wrapper tbody td {
    padding: 0.42rem 0.65rem;
    text-align: start;
    border-bottom: 1px solid #ebe6da;
    color: #1e353a;
    font-variant-numeric: tabular-nums;
    vertical-align: middle;
}

.badge-clear {
    display: inline-block;
    background: #f6e3d8;
    color: #8a350f;
    border: 1px solid #d99b7e;
    font-weight: 700;
    font-size: 0.76rem;
    padding: 0.08rem 0.48rem;
    border-radius: 4px;
    margin-inline-start: 0.25rem;
}

.badge-cautious {
    display: inline-block;
    background: #dcebed;
    color: #124e57;
    border: 1px solid #8eb8be;
    font-weight: 700;
    font-size: 0.76rem;
    padding: 0.08rem 0.48rem;
    border-radius: 4px;
    margin-inline-start: 0.25rem;
}

.badge-ineligible {
    display: inline-block;
    background: #f5e6c8;
    color: #6e4b0c;
    border: 1px solid #d4b475;
    font-weight: 700;
    font-size: 0.76rem;
    padding: 0.08rem 0.48rem;
    border-radius: 4px;
}

@keyframes trialReveal {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (prefers-reduced-motion: no-preference) {
    .trial-reveal-panel {
        animation: trialReveal 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
}

section[data-testid="stSidebar"] {
    background-color: #e8e4d8;
}

section[data-testid="stSidebar"][aria-expanded="false"] {
    overflow: hidden !important;
    min-width: 0 !important;
    max-width: 0 !important;
}

section[data-testid="stSidebar"][aria-expanded="false"] > div {
    visibility: hidden !important;
    pointer-events: none !important;
}

[data-testid="stMetricValue"] {
    color: var(--ep-teal);
    font-size: 1.75rem;
    direction: ltr;
    unicode-bidi: isolate;
}

.stButton > button, .stDownloadButton > button {
    background-color: var(--ep-teal);
    color: #ffffff;
    border: 1px solid transparent;
    min-height: 2.55rem;
    font-weight: 700;
}

.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    background-color: var(--ep-ochre);
    color: #ffffff;
    font-weight: 800;
    padding: 0.55rem 1.1rem;
    border-radius: 6px;
}

.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
    background-color: #96411c;
    color: #ffffff;
}

a {
    color: var(--ep-teal);
}

@media (forced-colors: active) {
    .city-card, .verdict-banner, .evidence-panel, .step-card, .reality-callout, .passport-hero,
    .stButton > button, .stDownloadButton > button {
        border: 1px solid ButtonText !important;
    }
}

@media (max-width: 768px) {
    html, body, .stApp, [data-testid="stAppViewContainer"], section[data-testid="stMain"], .block-container {
        max-width: 100vw !important;
        overflow-x: clip !important;
    }
    section[data-testid="stMain"] .block-container {
        padding-top: 2.2rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
    .editorial-headline {
        font-size: 1.42rem;
    }
    .verdict-lead {
        font-size: 0.94rem;
    }
    .trial-metrics-grid, .step-ribbon {
        grid-template-columns: minmax(0, 1fr);
    }
    .table-wrapper, .verdict-table {
        max-width: 100%;
        overflow-x: auto;
    }
}
</style>""",
    unsafe_allow_html=True,
)

SITE_A_COLOR = '#15616d'
SITE_B_COLOR = '#b55327'
INK_COLOR = '#14282d'
CHART_BG = '#f9f7f2'
ARABIC_PLOT_FONT = 'Cairo, Tajawal, Tahoma, Arial, sans-serif'

CITY_AR = {
    'Casablanca': 'الدار البيضاء',
    'Rabat': 'الرباط',
    'Marrakech': 'مراكش',
    'Ouarzazate': 'ورزازات',
    'Custom coordinates': 'إحداثيات عالمية مخصصة',
}

VARIABLES_AR = {
    'T2M': ('متوسط الحرارة السطحية على ارتفاع 2 م', '°C', '°C/عقد'),
    'PRECTOTCORR': ('الهطول المطري السنوي', 'مم/سنة', 'مم/سنة/عقد'),
}

MOROCCO_PHYSIOGRAPHY_AR = {
    'Casablanca': (
        'الهامش الساحلي الأطلسي',
        'موقع على الساحل الأطلسي؛ تقوم شبكة MERRA-2 الإقليمية بمجانسة التبريد البحري المحاذي للشريط الساحلي.',
    ),
    'Rabat': (
        'السهل الساحلي الأطلسي',
        'موقع ساحلي منخفض؛ تمثّل خلية MERRA-2 متوسطاً إقليمياً على نطاق ~56 كم × ~59 كم بدلاً من قراءة محطة رصد محلية.',
    ),
    'Marrakech': (
        'سهل الحوز القاري قرب سفوح الأطلس الكبير',
        'السهل القاري؛ خلية الشبكة (~0.5° × ~0.625°) لا تُمثّل التدرجات الطبوغرافية الحادة للأطلس الكبير بدقة محلية.',
    ),
    'Ouarzazate': (
        'حوض شبه صحراوي في ظل المطر جنوب شرق الأطلس الكبير',
        'ظل المطر الجبلي؛ يُدمج متوسط الشبكة بين السفوح الجبلية والحوض شبه الصحراوي داخل خلية واحدة.',
    ),
}

LENS_KEYS = ['cautious_both', 'cautious_only', 'hac_both', 'conventional_only']
LENS_CONFIG = {
    'cautious_both': (
        'cautious',
        'both',
        'مقارنة: الوقائي max(SE_OLS, SE_HAC) + الاعتيادي OLS',
    ),
    'cautious_only': (
        'cautious',
        'cautious',
        'الاحترازي الوقائي: max(SE_OLS, SE_HAC)',
    ),
    'hac_both': (
        'hac',
        'both',
        'خطأ Newey–West HAC الخام (SE_HAC دون حد أدنى)',
    ),
    'conventional_only': (
        'conventional',
        'conventional',
        'الانحدار الاعتيادي OLS (افتراض استقلالية السنوات)',
    ),
}


def ltr(text):
    """Isolate LTR numbers, formulas, intervals, and coordinates inside RTL prose."""
    return f'<span dir="ltr" class="ltr-num">{html.escape(str(text))}</span>'


def ar_loc(name):
    """Return Arabic display label for reference Moroccan cities or custom coordinate strings."""
    if not name:
        return ''
    if name in CITY_AR:
        return CITY_AR[name]
    if name.startswith('Custom A ('):
        return name.replace('Custom A', 'نقطة مخصصة أ', 1)
    if name.startswith('Custom B ('):
        return name.replace('Custom B', 'نقطة مخصصة ب', 1)
    return name


def ar_var(parameter):
    """Return (Arabic variable name, unit symbol, decadal rate unit)."""
    return VARIABLES_AR.get(parameter, (VARIABLES[parameter][0], VARIABLES[parameter][1], f"{VARIABLES[parameter][1]}/عقد"))


def ar_region_info(meta):
    """Translate grid metadata region name and physical-scale note cleanly into Arabic."""
    loc = meta['location']
    if loc in MOROCCO_PHYSIOGRAPHY_AR:
        return MOROCCO_PHYSIOGRAPHY_AR[loc]
    return (
        'إحداثيات عالمية مخصصة',
        'تمثّل بيانات MERRA-2 متوسطاً إقليمياً لخلية شبكية (~0.5° × ~0.625°) وليس رصداً موضعياً لمحطة أرضية.',
    )


def ar_sha_scope(scope_str):
    """Translate source_sha256 scope label into Arabic while preserving the filename."""
    if scope_str.startswith('Unaltered bundled snapshot ('):
        fname = scope_str[len('Unaltered bundled snapshot ('):-1]
        return f'لقطة NASA الموثقة غير المعدّلة · \u2066{fname}\u2069'
    return 'حمولة NASA API الحية · \u2066JSON\u2069 معياري'


def ar_mode_badge(interval_mode):
    return {
        'cautious': 'احترازي max(SE_OLS, SE_HAC)',
        'hac': 'Newey–West HAC خام',
        'conventional': 'انحدار OLS اعتيادي',
    }.get(interval_mode, interval_mode)


def ar_site_status(excludes_zero_flag, slope_decade, eligible=True):
    """Render Arabic site status matching the mathematical verdict."""
    if not eligible:
        return 'غير مؤهل للاستدلال (<30 سنة)'
    if excludes_zero_flag:
        return 'يستبعد الصفر (اتجاه موجب)' if slope_decade > 0 else 'يستبعد الصفر (اتجاه سالب)'
    return 'يعبر الصفر (غير حاسم)'


def ar_trial_verdict_label(verdict_code):
    return {
        'positive_difference': 'دليل على فرق اتجاهي موجب (B أسرع زيادة أو أبطأ تراجعاً من A)',
        'negative_difference': 'دليل على فرق اتجاهي سالب (B أبطأ زيادة أو أسرع تراجعاً من A)',
        'inconclusive': 'نتيجة غير حاسمة (يعبر الصفر — لا تثبت تساوي الاتجاهين)',
        'identical_series': 'لا يمكن اختبار الفرق (سلسلتان متطابقتان)',
        'ineligible': 'الاستدلال معلّق (أقل من 30 سنة متصلة مكتملة)',
    }.get(verdict_code, verdict_code)


def ar_trial_interpretation(trial, loc_a_display, loc_b_display):
    """Build faithful, dynamic Arabic interpretation directly from computed trial metrics."""
    _, _, rate_unit = ar_var(trial['parameter'])
    if not trial['eligible']:
        if trial['verdict_code'] == 'identical_series':
            return (
                f"المدخلان المختاران متطابقان في كل سنة ({loc_a_display} مقابل {loc_b_display})، "
                "وبالتالي فإن سلسلة الفرق D(سنة) = 0 بانحراف معدوم ولا يُعرَّف لها اختبار إحصائي. اختر موقعين مختلفين."
            )
        if trial['n_paired'] == 0:
            span_txt = f"{trial['start']}–{trial['end']}"
            return (
                f"لا توجد سنوات تقويمية مكتملة مشتركة بين {loc_a_display} و{loc_b_display} "
                f"في الفترة {ltr(span_txt)}؛ لذا يتعذر حساب اتجاه الفرق دون استكمال اصطناعي."
            )
        missing_txt = (
            f" السنوات المفقودة: {ltr(', '.join(map(str, trial['missing_paired'])))}."
            if trial['missing_paired']
            else ''
        )
        span_txt = f"{trial['start']}–{trial['end']}"
        return (
            f"الاستدلال الإحصائي غير متاح لسلسلة الفرق المقترنة بين {loc_b_display} و{loc_a_display} "
            f"في الفترة {ltr(span_txt)} ({ltr(trial['n_paired'])} سنة مشتركة؛ يشترط توفر 30 سنة متصلة مكتملة على الأقل).{missing_txt}"
        )

    dr = trial['diff_result']
    slope_str = ltr(f"{format_bound(dr['slope_decade'])} {rate_unit}")
    ci_str = ltr(f"{format_interval(trial['active_ci'], '')} {rate_unit}")
    p_str = ltr(f"p = {trial['active_p']:.4g}")
    span_str = ltr(f"{dr['start']}–{dr['end']}")
    n_str = ltr(dr['n'])

    if trial['verdict_code'] == 'positive_difference':
        return (
            f"<b>خلاصة المحاكمة الاستكشافية</b> ({span_str}، {n_str} سنة مقترنة): "
            f"يسجّل موقع <b>{loc_b_display}</b> ميلاً عقدياً أعلى من <b>{loc_a_display}</b> بمقدار مقدَّر {slope_str}، "
            f"وبمجال ثقة 95% قدره {ci_str} ({p_str}) يقع بالكامل أعلى من الصفر."
        )
    if trial['verdict_code'] == 'negative_difference':
        return (
            f"<b>خلاصة المحاكمة الاستكشافية</b> ({span_str}، {n_str} سنة مقترنة): "
            f"يسجّل موقع <b>{loc_b_display}</b> ميلاً عقدياً أدنى من <b>{loc_a_display}</b> بمقدار مقدَّر {slope_str}، "
            f"وبمجال ثقة 95% قدره {ci_str} ({p_str}) يقع بالكامل دون الصفر."
        )
    return (
        f"<b>نتيجة استكشافية غير حاسمة</b> ({span_str}، {n_str} سنة مقترنة): "
        f"قُدِّر ميل الفرق بنحو {slope_str}، غير أن مجال الثقة 95% ({ci_str}، {p_str}) <b>يعبر الصفر</b>. "
        f"هذا <b>لا يعني تساوي الاتجاهين</b> بين {loc_a_display} و{loc_b_display}، بل يشير فقط إلى أن السلسلة المقترنة لا تحسم فارقاً اتجاهياً عند مستوى 95%."
    )


def ar_overlap_insight(trial, loc_a_display, loc_b_display):
    """Translate the statistical non-overlap vs paired-trial rule accurately."""
    if not trial['eligible']:
        return (
            "قاعدة منهجية: لا يجوز أبداً استنتاج وجود فرق إحصائي بين اتجاهين بمجرد مقارنة مجالي ثقة منفصلين؛ "
            "بل يتطلب الحكم نمذجة سلسلة الفروق السنوية المقترنة D(سنة) = B(سنة) − A(سنة)."
        )
    _, _, rate_unit = ar_var(trial['parameter'])
    ci_str = ltr(f"{format_interval(trial['active_ci'], '')} {rate_unit}")
    p_str = ltr(f"p = {trial['active_p']:.4g}")
    if trial['separate_intervals_overlap'] and trial['active_excludes_zero']:
        return (
            f"لماذا تخدعنا المجالات المنفردة؟ رغم تداخل مجالي الثقة 95% لكل من {loc_a_display} و{loc_b_display} عند فحصهما بشكل مستقل، "
            f"يستبعد اختبار الفروق المقترنة الصفر بوضوح ({p_str}) لأن الاقتران السنوي يزيل التقلبات الإقليمية المشتركة بينهما."
        )
    if trial['separate_intervals_overlap'] is False and not trial['active_excludes_zero']:
        return (
            f"حتى عندما تبدو المجالات المنفردة متباعدة، لا يصح الحكم باختلاف الاتجاهين دون اختبار سلسلة D(سنة)؛ "
            f"فهنا يعبر مجال الفرق المقترن الصفر ({ci_str}) وتبقى النتيجة غير حاسمة."
        )
    return (
        "قاعدة استدلال أساسية: تداخل مجالي الثقة المنفردين أو تباعدهما لا يختبر تساوي الميلين؛ "
        "الاختبار المباشر للسلسلة المقترنة D(سنة) = المتغير_B(سنة) − المتغير_A(سنة) هو المرجع الإحصائي السليم."
    )


@st.cache_data(ttl=86400, show_spinner=False)
def load_live(lat, lon, start, end):
    return fetch_power(lat, lon, start=start, end=end)


def load_location_data(location, lat, lon, start, end, mode):
    snap_name = location.lower()
    snapshot = Path(__file__).parent / 'data' / f'{snap_name}.json'
    if (
        mode == 'bundled'
        and location in LOCATIONS
        and 1991 <= start <= end <= 2025
        and snapshot.exists()
    ):
        return json.loads(snapshot.read_text()), True
    return load_live(lat, lon, start, end), False


def format_trial_question_ar(loc_a, loc_b, parameter):
    """Headline question in Arabic for the opening Climate Trial."""
    a_ar, b_ar = ar_loc(loc_a), ar_loc(loc_b)
    if loc_a == loc_b:
        return f"مقارنة {a_ar} بنفسه ({ar_var(parameter)[0]})"
    if parameter == 'T2M':
        return f"هل ترتفع حرارة {b_ar} أسرع من {a_ar}؟"
    return f"هل يتغيّر هطول الأمطار في {b_ar} أسرع من {a_ar}؟"


def format_trial_question(loc_a, loc_b, parameter):
    """English canonical question used for machine-readable / PDF evidence passport."""
    if loc_a == loc_b:
        return f"Comparing {loc_a} against itself ({VARIABLES[parameter][0]})"
    if parameter == 'T2M':
        return f"Is {loc_b} warming faster than {loc_a}?"
    return f"Is {loc_b} gaining rainfall faster than {loc_a}?"


def _padded_axis_range(*arrays):
    vals = np.concatenate([np.asarray(a, dtype=float).ravel() for a in arrays] + [np.array([0.0])])
    lo, hi = float(np.min(vals)), float(np.max(vals))
    span = max(hi - lo, 0.25)
    return [lo - 0.16 * span, hi + 0.18 * span]


def build_comparison_series_figure(comp):
    """Build aligned annual series chart with Arabic labels & shared scale."""
    site_a, site_b = comp['site_a'], comp['site_b']
    loc_a_ar, loc_b_ar = ar_loc(site_a['location']), ar_loc(site_b['location'])
    var_ar, unit_ar, rate_unit_ar = ar_var(comp['parameter'])
    fa, fb = site_a['frame'], site_b['frame']
    ra, rb = site_a['result'], site_b['result']

    fig = go.Figure()
    if not fa.empty:
        fig.add_trace(
            go.Scatter(
                x=fa['year'],
                y=fa['value'],
                mode='lines+markers',
                name=f"● {loc_a_ar} (سنوي · {len(fa)} سنة)",
                line=dict(color=SITE_A_COLOR, width=2.0, dash='solid'),
                marker=dict(symbol='circle', size=5.5, color=SITE_A_COLOR),
                hovertemplate=f"<b>{loc_a_ar}</b> (%{{x}}): %{{y:.2f}} {unit_ar}<extra></extra>",
            )
        )
    if ra is not None:
        fig.add_trace(
            go.Scatter(
                x=fa['year'],
                y=ra['fitted'],
                mode='lines',
                name=f"● ميل {loc_a_ar} ({format_bound(ra['slope_decade'])} {rate_unit_ar})",
                line=dict(color=SITE_A_COLOR, width=3.2, dash='solid'),
                hovertemplate=f"<b>الميل الخطي · {loc_a_ar}</b> (%{{x}}): %{{y:.2f}} {unit_ar}<extra></extra>",
            )
        )
    if not fb.empty:
        fig.add_trace(
            go.Scatter(
                x=fb['year'],
                y=fb['value'],
                mode='lines+markers',
                name=f"◆ {loc_b_ar} (سنوي · {len(fb)} سنة)",
                line=dict(color=SITE_B_COLOR, width=2.0, dash='dot'),
                marker=dict(symbol='diamond', size=6.0, color=SITE_B_COLOR),
                hovertemplate=f"<b>{loc_b_ar}</b> (%{{x}}): %{{y:.2f}} {unit_ar}<extra></extra>",
            )
        )
    if rb is not None:
        fig.add_trace(
            go.Scatter(
                x=fb['year'],
                y=rb['fitted'],
                mode='lines',
                name=f"◆ ميل {loc_b_ar} ({format_bound(rb['slope_decade'])} {rate_unit_ar})",
                line=dict(color=SITE_B_COLOR, width=3.2, dash='dash'),
                hovertemplate=f"<b>الميل الخطي · {loc_b_ar}</b> (%{{x}}): %{{y:.2f}} {unit_ar}<extra></extra>",
            )
        )

    fig.update_layout(
        height=315,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family=ARABIC_PLOT_FONT, color=INK_COLOR, size=12),
        margin=dict(l=52, r=18, t=48, b=38),
        legend=dict(orientation='h', yanchor='bottom', y=1.03, xanchor='left', x=0.0, font=dict(size=10.8), bgcolor='rgba(249,247,242,0.0)'),
        xaxis=dict(title='السنة التقويمية (محور مشترك)', range=[comp['start'] - 0.6, comp['end'] + 0.6], gridcolor='#e3ded2', zeroline=False),
        yaxis=dict(title=f"{var_ar} ({unit_ar})", gridcolor='#e3ded2', zeroline=False),
        hovermode='x unified',
    )
    return fig


def build_whisker_figure(comp, lens_mode):
    """Build dot-and-whisker uncertainty comparison for individual sites with zero reference line."""
    site_a, site_b = comp['site_a'], comp['site_b']
    loc_a_ar, loc_b_ar = ar_loc(site_a['location']), ar_loc(site_b['location'])
    _, _, rate_unit_ar = ar_var(comp['parameter'])
    fig = go.Figure()
    fig.add_vline(x=0.0, line_width=2.5, line_dash='solid', line_color=INK_COLOR)

    if not comp['both_eligible']:
        fig.add_annotation(
            x=0.0,
            y=0.5,
            xref='x',
            yref='paper',
            text='<b>تم تعليق الاستدلال الإحصائي</b><br>يلزم توفر 30 سنة متصلة مكتملة على الأقل<br>لعرض الميل العقدي ومجالات الثقة 95%.',
            showarrow=False,
            font=dict(size=12, color=INK_COLOR, family=ARABIC_PLOT_FONT),
            bgcolor='#f5e6c8',
            bordercolor='#d4b475',
            borderwidth=1,
            borderpad=10,
        )
        fig.update_layout(
            height=315,
            template='plotly_white',
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=dict(family=ARABIC_PLOT_FONT, color=INK_COLOR, size=12),
            margin=dict(l=20, r=20, t=42, b=38),
            xaxis=dict(title=f"الميل الخطي المقدّر ({rate_unit_ar})", range=[-1, 1], gridcolor='#e3ded2'),
            yaxis=dict(visible=False),
        )
        return fig

    sites = [(site_a, loc_a_ar, 1.0, SITE_A_COLOR, 'circle', '●'), (site_b, loc_b_ar, 0.0, SITE_B_COLOR, 'diamond', '◆')]
    show_cautious = lens_mode in ('both', 'cautious')
    show_iid = lens_mode in ('both', 'conventional')

    all_bounds = [0.0]
    for s, _, _, _, _, _ in sites:
        r = s['result']
        all_bounds.extend(r['ci95'])
        all_bounds.extend(r['iid_ci95'])

    span = max(all_bounds) - min(all_bounds)
    x_min = min(all_bounds) - max(span * 0.28, 0.10)
    x_max = max(all_bounds) + max(span * 0.36, 0.14)
    x_mid = 0.5 * (x_min + x_max)

    fig.add_annotation(
        x=0.0,
        y=0.48,
        xref='x',
        yref='y',
        text='<b>0.0 (خط الانعدام)</b>',
        showarrow=False,
        font=dict(size=10.8, color=INK_COLOR, family=ARABIC_PLOT_FONT),
        bgcolor='#e5e0d3',
        bordercolor='#b8b09c',
        borderwidth=1,
        borderpad=3,
    )

    active_mode = comp.get('interval_mode', 'cautious')
    primary_trace_name = 'Newey–West HAC خام 95% (SE_HAC)' if active_mode == 'hac' else 'المجال الوقائي 95% (HAC / max SE)'
    primary_hover = 'HAC خام 95%' if active_mode == 'hac' else 'المجال الوقائي 95%'

    for idx, (s, s_ar, y_base, color, symbol, glyph) in enumerate(sites):
        r = s['result']
        slope = r['slope_decade']
        cautious_ci = r['ci95']
        iid_ci = r['iid_ci95']

        y_caut = y_base + (0.10 if lens_mode == 'both' else 0.0)
        fig.add_trace(
            go.Scatter(
                x=[slope],
                y=[y_caut],
                mode='markers',
                name=primary_trace_name,
                legendgroup='cautious',
                showlegend=(idx == 0),
                opacity=1.0 if show_cautious else 0.25,
                marker=dict(symbol=symbol, size=11, color=color, line=dict(width=1.5, color='#ffffff')),
                error_x=dict(type='data', symmetric=False, array=[cautious_ci[1] - slope], arrayminus=[slope - cautious_ci[0]], color=color, thickness=4.0, width=7),
                hovertemplate=(
                    f"<b>{s_ar} · {primary_hover}</b><br>"
                    f"الميل: {format_bound(slope)} {rate_unit_ar}<br>"
                    f"المجال: {format_interval(cautious_ci, '')}<br>"
                    f"الحالة: {ar_site_status(s['cautious_excludes_zero'], slope)}<extra></extra>"
                ),
            )
        )

        y_iid = y_base - (0.12 if lens_mode == 'both' else 0.0)
        fig.add_trace(
            go.Scatter(
                x=[slope],
                y=[y_iid],
                mode='markers',
                name='OLS اعتيادي 95% (افتراض استقلالية السنوات)',
                legendgroup='iid',
                showlegend=(idx == 0),
                opacity=0.95 if show_iid else 0.22,
                marker=dict(symbol=f"{symbol}-open", size=8.5, color='#455c61', line=dict(width=2, color='#455c61')),
                error_x=dict(type='data', symmetric=False, array=[iid_ci[1] - slope], arrayminus=[slope - iid_ci[0]], color='#52696e', thickness=2.0, width=5),
                hovertemplate=(
                    f"<b>{s_ar} · OLS اعتيادي 95%</b><br>"
                    f"الميل: {format_bound(slope)} {rate_unit_ar}<br>"
                    f"المجال: {format_interval(iid_ci, '')}<br>"
                    f"الحالة: {ar_site_status(s['iid_excludes_zero'], slope)}<extra></extra>"
                ),
            )
        )

        active_ci = iid_ci if lens_mode == 'conventional' else cautious_ci
        active_ex = s['iid_excludes_zero'] if lens_mode == 'conventional' else s['cautious_excludes_zero']
        verdict_tag = 'يستبعد 0' if active_ex else 'يعبر 0'
        label_x = 0.45 * (0.5 * (active_ci[0] + active_ci[1])) + 0.55 * x_mid
        fig.add_annotation(
            x=label_x,
            y=y_base + 0.31,
            xref='x',
            yref='y',
            text=f"<b>{glyph} {s_ar}: {format_bound(slope)}</b> [{format_bound(active_ci[0])}, {format_bound(active_ci[1])} · <b>{verdict_tag}</b>]",
            showarrow=False,
            font=dict(size=10.5, color=color, family=ARABIC_PLOT_FONT),
            bgcolor='rgba(249,247,242,0.94)',
        )

    fig.update_layout(
        height=315,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family=ARABIC_PLOT_FONT, color=INK_COLOR, size=12),
        margin=dict(l=98, r=18, t=48, b=38),
        legend=dict(orientation='h', yanchor='bottom', y=1.03, xanchor='left', x=0.0, font=dict(size=10.6), bgcolor='rgba(249,247,242,0.0)'),
        xaxis=dict(title=f"الميل الخطي المقدّر ({rate_unit_ar})", range=[x_min, x_max], gridcolor='#e3ded2', zeroline=False),
        yaxis=dict(tickmode='array', tickvals=[0.0, 1.0], ticktext=[f"<b>◆ {loc_b_ar}</b>", f"<b>● {loc_a_ar}</b>"], range=[-0.38, 1.50], gridcolor='#ece8de'),
    )
    return fig


def build_residual_persistence_figure(comp):
    """Build lag-1 residual persistence scatter (e_{t-1} vs e_t) in Arabic."""
    sa, sb = comp['site_a'], comp['site_b']
    _, unit_ar, _ = ar_var(comp['parameter'])
    fig = go.Figure()
    for s, color, symbol, glyph in [(sa, SITE_A_COLOR, 'circle', '●'), (sb, SITE_B_COLOR, 'diamond', '◆')]:
        if not s['eligible']:
            continue
        frame, res = s['frame'], s['result']
        s_ar = ar_loc(s['location'])
        residuals = frame['value'].to_numpy(dtype=float) - np.array(res['fitted'], dtype=float)
        if len(residuals) < 3:
            continue
        r_prev, r_curr = residuals[:-1], residuals[1:]
        years_curr = frame['year'].to_numpy()[1:]
        fig.add_trace(
            go.Scatter(
                x=r_prev,
                y=r_curr,
                mode='markers',
                name=f"{glyph} {s_ar} (ρ₁ = {res['residual_lag1']:+.2f})",
                marker=dict(symbol=symbol, size=8, color=color, opacity=0.85),
                text=years_curr,
                hovertemplate=(
                    f"<b>{s_ar}</b> (سنة %{{text}})<br>"
                    f"بواقي السنة السابقة eₜ₋₁: %{{x:+.2f}} {unit_ar}<br>"
                    f"بواقي السنة الحالية eₜ: %{{y:+.2f}} {unit_ar}<extra></extra>"
                ),
            )
        )
        if np.std(r_prev) > 1e-9:
            xs = np.linspace(float(r_prev.min()), float(r_prev.max()), 20)
            slope_ar1 = float(np.polyfit(r_prev, r_curr, 1)[0])
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=slope_ar1 * xs,
                    mode='lines',
                    line=dict(color=color, width=2.2, dash='solid' if glyph == '●' else 'dash'),
                    showlegend=False,
                )
            )
    fig.add_hline(y=0, line_width=1, line_dash='dot', line_color='#8c8576')
    fig.add_vline(x=0, line_width=1, line_dash='dot', line_color='#8c8576')
    fig.update_layout(
        height=295,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family=ARABIC_PLOT_FONT, color=INK_COLOR, size=12),
        margin=dict(l=52, r=18, t=38, b=38),
        legend=dict(orientation='h', y=1.06, x=0.0),
        xaxis=dict(title=f"انحراف السنة السابقة eₜ₋₁ ({unit_ar})", gridcolor='#e3ded2', zeroline=False),
        yaxis=dict(title=f"انحراف السنة الحالية eₜ ({unit_ar})", gridcolor='#e3ded2', zeroline=False),
    )
    return fig


def build_window_sensitivity_figure(loc_a, data_a, loc_b, data_b, parameter):
    """Evaluate consecutive 30+ year windows within bundled 1991-2025 snapshots."""
    _, _, rate_unit_ar = ar_var(parameter)
    windows = [(1991, 2020), (1991, 2022), (1991, 2025), (1993, 2025), (1995, 2025), (1996, 2025)]
    labels = [f"{s}–{e} ({e - s + 1})" for s, e in windows]
    fig = go.Figure()
    fig.add_hline(y=0.0, line_width=2.2, line_color=INK_COLOR)

    for loc, data, color, symbol, glyph in [
        (loc_a, data_a, SITE_A_COLOR, 'circle', '●'),
        (loc_b, data_b, SITE_B_COLOR, 'diamond', '◆'),
    ]:
        l_ar = ar_loc(loc)
        slopes, err_plus, err_minus, valid_labels = [], [], [], []
        for (s_yr, e_yr), lbl in zip(windows, labels):
            ev = evaluate_site(loc, data, parameter, s_yr, e_yr)
            if ev['eligible']:
                r = ev['result']
                sl, ci = r['slope_decade'], r['ci95']
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
                    name=f"{glyph} {l_ar} (95% وقائي)",
                    line=dict(color=color, width=2.2, dash='solid' if glyph == '●' else 'dash'),
                    marker=dict(symbol=symbol, size=9, color=color),
                    error_y=dict(type='data', symmetric=False, array=err_plus, arrayminus=err_minus, color=color, thickness=2.5, width=5),
                    hovertemplate=f"<b>{l_ar}</b> (%{{x}}): %{{y:+.2f}} {rate_unit_ar}<extra></extra>",
                )
            )
    fig.update_layout(
        height=295,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family=ARABIC_PLOT_FONT, color=INK_COLOR, size=12),
        margin=dict(l=52, r=18, t=38, b=38),
        legend=dict(orientation='h', y=1.06, x=0.0),
        xaxis=dict(title='نافذة 30+ سنة متصلة داخل السجل الموثّق', gridcolor='#e3ded2'),
        yaxis=dict(title=f"الميل ({rate_unit_ar})", gridcolor='#e3ded2', zeroline=False),
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
    """Build interactive geographic Grid-Cell Reality Map in Arabic with approx MERRA-2 scale boxes."""
    _, unit_ar, rate_unit_ar = ar_var(parameter)
    fig = go.Figure()

    active_pts = []
    if lat_a is not None and lon_a is not None:
        active_pts.append((float(lat_a), float(lon_a)))
    if lat_b is not None and lon_b is not None:
        active_pts.append((float(lat_b), float(lon_b)))
    in_morocco = all(27.0 <= p_lat <= 37.5 and -14.5 <= p_lon <= -0.5 for p_lat, p_lon in active_pts)

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
            name='سلسلة الأطلس (سياق تضاريسي تخطيطي)',
            hovertemplate=(
                '<b>حاجز جبال الأطلس</b><br>'
                'سياق تخطيطي للأطلس الكبير والمتوسط (وليس نموذج ارتفاع رقمي).<br>'
                'يفصل السهل الأطلسي الرطب عن سهول الحوز والأحواض شبه الصحراوية.<extra></extra>'
            ),
        )
    )
    fig.add_trace(
        go.Scattergeo(
            lat=[32.95, 31.32],
            lon=[-10.45, -6.10],
            mode='text',
            text=['<i>المحيط الأطلسي<br>(تلطيف بحري)</i>', '<i>الأطلس الكبير<br>(سياق تخطيطي)</i>'],
            textfont=dict(family=ARABIC_PLOT_FONT, size=10.5, color='#455c61'),
            showlegend=False,
            hoverinfo='skip',
        )
    )

    ref_records = []
    pos_map = {'Casablanca': 'top left', 'Rabat': 'top right', 'Marrakech': 'middle left', 'Ouarzazate': 'bottom right'}
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

    custom_records = []
    for r_loc, r_data, r_lat, r_lon in [(loc_a, data_a, lat_a, lon_a), (loc_b, data_b, lat_b, lon_b)]:
        if r_loc and r_loc not in LOCATIONS and r_data is not None and r_lat is not None and r_lon is not None:
            meta = extract_grid_metadata(r_loc, r_data, r_lat, r_lon)
            ev = evaluate_site(r_loc, r_data, parameter, start, end, interval_mode=interval_mode)
            custom_records.append((r_loc, r_data, meta, ev))

    all_records = ref_records + custom_records

    for cname, _, meta, _ in all_records:
        fp = meta['footprint']
        c_ar = ar_loc(cname)
        is_a, is_b = (cname == loc_a), (cname == loc_b)
        if is_a:
            fill_rgba, line_col, line_w = 'rgba(21, 97, 109, 0.16)', SITE_A_COLOR, 2.0
            trace_name, show_leg = f"نطاق خلية تقريبي ~0.5°×0.625° · ● {c_ar}", True
        elif is_b:
            fill_rgba, line_col, line_w = 'rgba(181, 83, 39, 0.16)', SITE_B_COLOR, 2.0
            trace_name, show_leg = f"نطاق خلية تقريبي ~0.5°×0.625° · ◆ {c_ar}", True
        else:
            fill_rgba, line_col, line_w = 'rgba(80, 96, 100, 0.05)', 'rgba(80, 96, 100, 0.48)', 1.2
            trace_name, show_leg = 'نطاق مرجعي ~0.5°×0.625°', False

        elev_txt = f"{meta['grid_elevation_m']:.1f} م (بيانات الشبكة)" if meta['grid_elevation_m'] is not None else 'غير متاح'
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
                    f"<b>{c_ar} · دقة MERRA-2 التقريبية</b><br>"
                    f"الامتداد التقريبي: {MERRA2_LAT_RES_DEG}° × {MERRA2_LON_RES_DEG}° (~{fp['lat_km']:.0f} × ~{fp['lon_km']:.0f} كم)<br>"
                    f"نقطة JSON المعادة من ناسا: {meta['returned_lat']:.3f}°N, {meta['returned_lon']:.3f}°E<br>"
                    f"ارتفاع الخلية المرجعي: {elev_txt}<br>"
                    "<i>ملف JSON النقطي لا ينشر حدود المضلع الدقيقة؛ الصندوق تمثيل تقريبي للدقة المكانية.</i><extra></extra>"
                ),
            )
        )

    for cname, _, meta, ev in all_records:
        c_ar = ar_loc(cname)
        reg_ar, _ = ar_region_info(meta)
        is_a, is_b = (cname == loc_a), (cname == loc_b)
        plat, plon = meta['requested_lat'], meta['requested_lon']
        elev_txt = f"{meta['grid_elevation_m']:.0f} م" if meta['grid_elevation_m'] is not None else 'عالمي'
        if ev['eligible']:
            r = ev['result']
            sl_short = f"{format_bound(r['slope_decade'])} {rate_unit_ar}"
            ci_str = format_interval(ev['active_ci'], '')
            v_txt = ar_site_status(ev['active_excludes_zero'], r['slope_decade'])
        else:
            sl_short, ci_str, v_txt = 'غير مؤهل (<30 سنة)', '—', 'غير مؤهل'

        if is_a:
            m_col, m_sym, m_size, role_tag = SITE_A_COLOR, 'circle', 13, '● الموقع أ'
        elif is_b:
            m_col, m_sym, m_size, role_tag = SITE_B_COLOR, 'diamond', 14, '◆ الموقع ب'
        else:
            m_col, m_sym, m_size, role_tag = '#53686d', 'circle-open', 10, '○ مرجع'

        fig.add_trace(
            go.Scattergeo(
                lat=[plat],
                lon=[plon],
                mode='markers+text',
                text=[f"<b>{c_ar}</b><br>{sl_short}"],
                textposition=pos_map.get(cname, 'top center'),
                textfont=dict(family=ARABIC_PLOT_FONT, size=11, color=INK_COLOR),
                name=f"{role_tag}: {c_ar}",
                showlegend=(is_a or is_b),
                marker=dict(size=m_size, color=m_col, symbol=m_sym, line=dict(width=2, color='#ffffff')),
                hovertemplate=(
                    f"<b>{c_ar}</b> ({role_tag}) · {reg_ar}<br>"
                    f"الإحداثيات المختارة: {meta['requested_lat']:.4f}°N, {meta['requested_lon']:.4f}°E<br>"
                    f"نقطة ناسا المعادة: {meta['returned_lat']:.3f}°N, {meta['returned_lon']:.3f}°E ({elev_txt})<br>"
                    f"الميل: {sl_short}<br>"
                    f"مجال الثقة النشط 95%: {ci_str} ({v_txt})<extra></extra>"
                ),
            )
        )

    geo_cfg = (
        dict(scope='africa', center=dict(lat=32.35, lon=-7.2), lataxis_range=[28.8, 35.8], lonaxis_range=[-12.5, -1.8])
        if (in_morocco or not active_pts)
        else dict(
            scope='world',
            lataxis_range=[max(-85.0, min(p[0] for p in active_pts) - 4.0), min(85.0, max(p[0] for p in active_pts) + 4.0)],
            lonaxis_range=[max(-179.0, min(p[1] for p in active_pts) - 5.0), min(179.0, max(p[1] for p in active_pts) + 5.0)],
        )
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
        height=395,
        paper_bgcolor=CHART_BG,
        font=dict(family=ARABIC_PLOT_FONT, color=INK_COLOR, size=11),
        margin=dict(l=4, r=4, t=8, b=58),
        legend=dict(orientation='h', yanchor='top', y=-0.03, xanchor='left', x=0.0, font=dict(size=10.2, color=INK_COLOR), bgcolor='rgba(249,247,242,0.0)'),
    )
    return fig


def build_morocco_grid_map(parameter, start=1991, end=2025):
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
    """Render STEP 1 · Grid-Cell Reality Map and metadata-verified point-vs-grid honesty note in Arabic."""
    meta_a = extract_grid_metadata(loc_a, data_a, lat_a, lon_a)
    has_b = bool(loc_b and data_b is not None and lat_b is not None and lon_b is not None)
    meta_b = extract_grid_metadata(loc_b, data_b, lat_b, lon_b) if has_b else None

    st.markdown(
        '<div class="step-banner">'
        '<div><div class="step-banner-kicker">الخطوة 1 · أين يقع الدليل المكاني؟</div>'
        '<div class="step-title">خريطة الواقع الشبكي · إحداثيات المدن مقابل دقة شبكة MERRA-2</div></div>'
        f'<span class="provenance-badge">مقياس شبكي تقريبي {ltr("0.5° × 0.625° MERRA-2")} · حدود الخلايا الدقيقة غير منشورة في Point JSON</span>'
        '</div>'
        '<p class="step-banner-sub">قارن الإحداثيات النقطية للمدن بمقياس إعادة التحليل الإقليمي لـ NASA POWER '
        'على طول الساحل الأطلسي وحاجز جبال الأطلس التخطيطي.</p>',
        unsafe_allow_html=True,
    )

    m_col1, m_col2 = st.columns([1.22, 1.0], gap='medium')
    with m_col1:
        st.markdown(
            '<div class="chart-header-box">'
            '<div class="chart-header-title">السياق الجغرافي للمغرب وخلايا MERRA-2 التقريبية (0.5° × 0.625°)</div>'
            '<div class="chart-header-sub">تمثّل المربعات المتقطعة المقياس الأفقي التقريبي للشبكة (~56 كم × ~59 كم عند خط عرض 31°–34° شمالاً)؛ وتشير العلامات الصلبة لنقاط الاستعلام المختارة</div>'
            '</div>',
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
        paired_metas = [('● أ', meta_a)] + ([('◆ ب', meta_b)] if meta_b is not None else [])
        for glyph, m in paired_metas:
            reg_ar, _ = ar_region_info(m)
            elev_str = f"{m['grid_elevation_m']:.2f} م" if m['grid_elevation_m'] is not None else 'غير متاح'
            scale_km = f"~{m['footprint']['lat_km']:.0f} × ~{m['footprint']['lon_km']:.0f} كم"
            q_coord = f"{m['requested_lat']:.4f}°N, {m['requested_lon']:.4f}°E"
            r_coord = f"{m['returned_lat']:.3f}°N, {m['returned_lon']:.3f}°E"
            rows_html.append(
                f"<tr>"
                f"<td><b>{glyph}: {ar_loc(m['location'])}</b><br><span style='font-size:0.78rem;color:#4a5f65;'>{reg_ar}</span></td>"
                f"<td>الاستعلام: {ltr(q_coord)}<br>"
                f"<span style='font-size:0.78rem;color:#4a5f65;'>نقطة NASA: {ltr(r_coord)}</span></td>"
                f"<td><b>{ltr(elev_str)}</b><br><span style='font-size:0.78rem;color:#4a5f65;'>{ltr(scale_km)}</span></td>"
                f"</tr>"
            )
        meta_table = (
            f'<div class="table-wrapper table-wrapper-auto" tabindex="0" role="region" aria-label="مقارنة إحداثيات المدن ببيانات شبكة MERRA-2">'
            f'<table><thead><tr>'
            f'<th>الموقع والبيئة الجغرافية</th>'
            f'<th>الإحداثيات المختارة مقابل المعادة</th>'
            f'<th>ارتفاع الشبكة والمقياس</th>'
            f'</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'
        )
        st.markdown(meta_table, unsafe_allow_html=True)

        elev_a_str = ltr(f"{meta_a['grid_elevation_m']:.1f} م") if meta_a['grid_elevation_m'] is not None else 'غير متاح'
        _, note_a_ar = ar_region_info(meta_a)
        if meta_b is not None:
            elev_b_str = ltr(f"{meta_b['grid_elevation_m']:.1f} م") if meta_b['grid_elevation_m'] is not None else 'غير متاح'
            _, note_b_ar = ar_region_info(meta_b)
            elev_phrase = f"{elev_a_str} لمدينة {ar_loc(loc_a)} و{elev_b_str} لمدينة {ar_loc(loc_b)}"
            phys_phrase = f"{note_a_ar} {note_b_ar}"
        else:
            elev_phrase = f"{elev_a_str} لموقع {ar_loc(loc_a)}"
            phys_phrase = note_a_ar

        hdr_title_pill = ltr(meta_a['header_title'])
        geom_code = ltr(f"type: {meta_a['geometry_type']}")
        st.markdown(
            f'<div class="reality-callout">'
            f'<b>تقديرات الخلايا الشبكية مقابل محطات الرصد الأرضية:</b><br>'
            f'• <b>التحقق من البيانات الوصفية — {hdr_title_pill}:</b> يُبلغ ملف JSON عن هندسة نقطية <code>{geom_code}</code> '
            f'بارتفاع شبكي تقريبي ({elev_phrase}) ويغفل إحداثيات زوايا المضلع الدقيقة؛ لذا تُعرض مربعات مقياس تقريبية بنحو <code>0.5° × 0.625°</code> دون اختلاق حدود غير موثقة.<br>'
            f'• <b>الأثر الفيزيائي للمقياس:</b> {phys_phrase}<br>'
            f'• <b>قاعدة الأمانة العلمية:</b> يعكس الارتفاع تمثيل التضاريس الإجمالي في نموذج إعادة التحليل؛ ولا يُطبَّق أي تصحيح ارتفاعي محلي أو معايرة لمحطات الرصد الأرضية.'
            f'</div>',
            unsafe_allow_html=True,
        )


def resolve_lens(lens_key):
    """Map canonical lens selector key to (interval_mode, whisker_lens)."""
    pair = LENS_CONFIG.get(lens_key, LENS_CONFIG['cautious_both'])
    return pair[0], pair[1]


def render_step_ribbon(active_step=None):
    """Render concise 3-step Arabic narrative header connecting map, inference, and passport."""
    steps = [
        ('الخطوة 1', 'أين يقع الدليل؟', 'المقياس الشبكي MERRA-2 0.5°×0.625° والسياق الساحلي والأطلسي'),
        ('الخطوة 2', 'ما مدى قوة الدليل؟', 'الميول السنوية، اختبار الفروق المقترنة، وعدسة OLS مقابل HAC الخام'),
        ('الخطوة 3', 'هل يمكنني التحقق منه؟', 'موجز أدلة PDF من صفحة واحدة (بالإنجليزية) وبصمات SHA-256'),
    ]
    cards = []
    for idx, (kicker, title, desc) in enumerate(steps, start=1):
        accent = 'border-inline-start-color:#b55327;' if active_step == idx else ''
        cards.append(
            f'<div class="step-card" style="{accent}">'
            f'<div class="step-card-num">{kicker}</div>'
            f'<div class="step-card-q">{title}</div>'
            f'<div class="step-card-desc">{desc}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="step-ribbon">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_step_banner(step_num, question_title, headline_title, subtitle, badge=''):
    badge_html = f'<span class="provenance-badge">{badge}</span>' if badge else ''
    st.markdown(
        f'<div class="step-banner">'
        f'<div><div class="step-banner-kicker">الخطوة {step_num} · {question_title}</div>'
        f'<div class="step-title">{headline_title}</div></div>'
        f'{badge_html}'
        f'</div>'
        f'<p class="step-banner-sub">{subtitle}</p>',
        unsafe_allow_html=True,
    )


def render_uncertainty_lens_panel(
    series_rows,
    active_interval_mode,
    unit_ar,
    rate_unit_ar,
    lens_state_key=None,
    lens_heading='عدسة عدم اليقين · مقارنة الخطأ المعياري بين OLS وNewey–West HAC الخام والمعيار الوقائي',
    show_control=True,
):
    """Display interactive assumption controls and tabular SE / CI diagnostics in Arabic."""
    st.markdown(f'#### {lens_heading}')
    if show_control and lens_state_key:
        st.radio(
            'افتراض عدم اليقين النشط',
            LENS_KEYS,
            format_func=lambda k: LENS_CONFIG[k][2],
            horizontal=True,
            key=lens_state_key,
        )

    valid_entries = []
    for label, res in series_rows:
        lens = uncertainty_lens_summary(res) if res else None
        if lens is not None:
            valid_entries.append((label, res, lens))

    if not valid_entries:
        st.info('يلزم توفر 30 سنة تقويمية مكتملة على الأقل لحساب عدسة المقارنة بين OLS وNewey–West HAC.')
        return

    mode_desc_ar = {
        'cautious': 'الاحترازي الوقائي · max(SE_OLS, SE_HAC)',
        'hac': 'خطأ Newey–West HAC الخام · SE_HAC (دون سقف أدنى)',
        'conventional': 'الانحدار الخطي الاعتيادي · SE_OLS (افتراض استقلالية السنوات)',
    }
    st.caption(
        f"**افتراض الاحتساب النشط:** {mode_desc_ar.get(active_interval_mode, active_interval_mode)}. "
        "تنعكس اختياراتك تلقائياً على الرسوم البيانية والحُكم أعلاه."
    )

    rows_html = []
    floor_notes = []
    for label, res, lens in valid_entries:
        ols_cls = 'badge-clear' if lens['ols_excludes_zero'] else 'badge-cautious'
        ols_txt = 'يستبعد 0' if lens['ols_excludes_zero'] else 'يعبر 0'
        hac_cls = 'badge-clear' if lens['hac_excludes_zero'] else 'badge-cautious'
        hac_txt = 'يستبعد 0' if lens['hac_excludes_zero'] else 'يعبر 0'
        cau_cls = 'badge-clear' if lens['cautious_excludes_zero'] else 'badge-cautious'
        cau_txt = 'يستبعد 0' if lens['cautious_excludes_zero'] else 'يعبر 0'

        se_ols_s = f"{lens['se_ols_decade']:.4f}"
        se_hac_s = f"{lens['se_hac_decade']:.4f}"
        se_cau_s = f"{lens['se_cautious_decade']:.4f}"
        ratio_s = f"{lens['hac_to_ols_se_ratio']:.2f}x"
        lag_s = f"ρ₁ = {lens['residual_lag1']:+.2f} · L = {lens['hac_lags']}"

        if lens['cautious_floored_by_ols']:
            safeguard_note = 'محفوظ عند SE_OLS'
            floor_notes.append(
                f"{label}: قيمة SE_HAC الخام ({ltr(se_hac_s)}) أقل من SE_OLS ({ltr(se_ols_s)})، "
                f"والنسبة = {ltr(ratio_s)}؛ لذا يعتمد المعيار الوقائي max(SE_OLS, SE_HAC) قيمة SE_OLS."
            )
        else:
            safeguard_note = f"يعتمد SE_HAC الخام ({lens['hac_lags']} فجوات)"

        rows_html.append(
            f"<tr>"
            f"<td><b>{label}</b><br><span style='font-size:0.78rem;color:#4a5f65;'>{ltr(lag_s)}</span></td>"
            f"<td><b>{ltr(format_bound(res['slope_decade']))}</b><br><span style='font-size:0.78rem;color:#4a5f65;'>{rate_unit_ar}</span></td>"
            f"<td>{ltr(se_ols_s)}</td>"
            f"<td><b>{ltr(se_hac_s)}</b></td>"
            f"<td><b>{ltr(ratio_s)}</b></td>"
            f"<td>{ltr(se_cau_s)}<br><span style='font-size:0.76rem;color:#4a5f65;'>{safeguard_note}</span></td>"
            f"<td>{ltr(format_interval(lens['ols_ci95'], ''))} <span class='{ols_cls}'>{ols_txt}</span></td>"
            f"<td>{ltr(format_interval(lens['hac_ci95'], ''))} <span class='{hac_cls}'>{hac_txt}</span></td>"
            f"<td>{ltr(format_interval(lens['cautious_ci95'], ''))} <span class='{cau_cls}'>{cau_txt}</span></td>"
            f"</tr>"
        )

    lens_table = (
        f'<div class="table-wrapper table-wrapper-auto" tabindex="0" role="region" aria-label="عدسة عدم اليقين ومقارنة الأخطاء المعيارية">'
        f'<table><thead><tr>'
        f'<th>السلسلة</th>'
        f'<th>الميل العقدي</th>'
        f'<th>{ltr("SE_OLS")}</th>'
        f'<th>{ltr("SE_HAC")} الخام</th>'
        f'<th>النسبة {ltr("SE_HAC / SE_OLS")}</th>'
        f'<th>{ltr("max SE")} الوقائي</th>'
        f'<th>مجال OLS 95% ({rate_unit_ar})</th>'
        f'<th>مجال HAC الخام 95% ({rate_unit_ar})</th>'
        f'<th>المجال الوقائي 95% ({rate_unit_ar})</th>'
        f'</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'
    )
    st.markdown(lens_table, unsafe_allow_html=True)

    floor_html = f"<br>• <b>الحد الأدنى الوقائي مقابل HAC الخام:</b> {' | '.join(floor_notes)}" if floor_notes else ''
    st.markdown(
        f'<div class="reality-callout">'
        f'<b>كيف تقرأ عدسة عدم اليقين (تحليل استكشافي):</b><br>'
        f'• <b>تعريف النسبة:</b> تقيس النسبة <code>SE_HAC / SE_OLS</code> فقط <b>التغير النسبي في الخطأ المعياري المُقدَّر</b> '
        f'الناتج عن الارتباط الذاتي الزمني وعدم تجانس التباين عبر الفجوات السنوية؛ وهي <b>ليست احتمال خطأ من النوع الأول (Type-I error probability)</b> '
        f'ولا <b>معدل إيجابية كاذبة (false-positive rate)</b>.<br>'
        f'• <b>التمييز بين الخام والوقائي:</b> عند تفعيل المعيار الوقائي <code>max(SE_OLS, SE_HAC)</code>، لا تتقلص حدود عدم اليقين دون مستوى OLS الاعتيادي متى كانت '
        f'<code>SE_HAC / SE_OLS &lt; 1.0</code>. يمكنك التبديل أعلاه إلى <i>خطأ Newey–West HAC الخام</i> لمعاينة القيمة غير المقيدة مباشرة.<br>'
        f'• <b>تحفظات العينات القصيرة:</b> مع ~30–35 سنة مكتملة، تبقى تقديرات تباين HAC خاضعة لتذبذب العينة، وحساسة لشكل النموذج الخطي، وغير مصححة لتعدد المقارنات عبر المدن أو الفترات.{floor_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_evidence_passport_section(
    question_ar,
    question_en,
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
    """Render STEP 3 · Evidence Passport with English 1-page verifiable PDF & SHA-256 checksums."""
    render_step_banner(
        3,
        'هل يمكنني التحقق من الدليل؟',
        'بطاقة الأدلة بنقرة واحدة · تحميل موجز الأدلة العلمي (PDF)',
        'كل رقم في هذا الموجز العلمي (PDF من صفحة واحدة بصيغة أرشيفية بالإنجليزية) مطابق مباشرةً لاختيارك النشط وافتراض عدم اليقين وروابط NASA POWER وبصمات SHA-256.',
        badge='صفحة واحدة PDF · حالة قابلة للاستنساخ · SHA-256',
    )

    sha_a = source_sha256(loc_a, data_a)
    sha_b = source_sha256(loc_b, data_b) if (loc_b and data_b) else None
    pdf_bytes = build_scientific_evidence_brief_pdf(
        question=question_en,
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
            f'<div class="step-banner-kicker">موجز تدقيق علمي موثق · صفحة واحدة A4</div>'
            f'<div class="step-title" style="font-size:1.08rem;">{question_ar}</div>'
            f'<p style="margin:0.25rem 0 0 0;font-size:0.86rem;color:#243b40;line-height:1.6;">'
            f'يتضمن ملف PDF (بالإنجليزيّة القياسية للتوثيق العلمي) الإحداثيات، تحفظات دقة MERRA-2، الميول ومجالات 95% وفق افتراض '
            f'<code>{interval_mode}</code>، الحدود المنهجية، روابط NASA الدقيقة، وبصمات SHA-256 للملفات المصدرية.'
            f'</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with hero_right:
        st.download_button(
            'تحميل موجز الأدلة العلمي (PDF)',
            data=pdf_bytes,
            file_name=pdf_filename,
            mime='application/pdf',
            type='primary',
            use_container_width=True,
            key=f'{key_prefix}_pdf_btn',
        )
        hash_lines = [f"**{ar_loc(loc_a)}** ({ar_sha_scope(sha_a['scope'])}): `{sha_a['sha256'][:16]}…{sha_a['sha256'][-8:]}`"]
        if sha_b:
            hash_lines.append(f"**{ar_loc(loc_b)}** ({ar_sha_scope(sha_b['scope'])}): `{sha_b['sha256'][:16]}…{sha_b['sha256'][-8:]}`")
        st.caption('بصمات SHA-256: ' + ' · '.join(hash_lines))

    dl_cols = st.columns(4)
    col_idx = 0
    if export_df is not None and export_csv_name:
        dl_cols[col_idx].download_button(
            'البيانات السنوية · CSV',
            export_df.to_csv(index=False),
            export_csv_name,
            'text/csv',
            use_container_width=True,
            key=f'{key_prefix}_csv_btn',
        )
        col_idx += 1
    if secondary_md and secondary_md_name:
        dl_cols[col_idx].download_button(
            'ملخص الأدلة · MD',
            secondary_md,
            secondary_md_name,
            'text/markdown',
            use_container_width=True,
            key=f'{key_prefix}_md_btn',
        )
        col_idx += 1
    dl_cols[col_idx].download_button(
        f'بيانات {ar_loc(loc_a)} · JSON',
        json.dumps(data_a, indent=2),
        f'earthpulse_{loc_a}_NASA.json',
        'application/json',
        use_container_width=True,
        key=f'{key_prefix}_json_a_btn',
    )
    col_idx += 1
    if loc_b and data_b is not None and col_idx < 4:
        dl_cols[col_idx].download_button(
            f'بيانات {ar_loc(loc_b)} · JSON',
            json.dumps(data_b, indent=2),
            f'earthpulse_{loc_b}_NASA.json',
            'application/json',
            use_container_width=True,
            key=f'{key_prefix}_json_b_btn',
        )


def build_trial_transition_figure(trial):
    """Build animated Original-to-Paired-Difference Plotly morph figure in Arabic."""
    merged = trial['merged']
    _, unit_ar, rate_unit_ar = ar_var(trial['parameter'])
    loc_a_ar = ar_loc(trial['site_a']['location'])
    loc_b_ar = ar_loc(trial['site_b']['location'])
    fig = go.Figure()

    if merged.empty:
        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref='paper',
            yref='paper',
            text='<b>لا توجد سنوات تقويمية مكتملة مشتركة في هذه الفترة.</b>',
            showarrow=False,
            font=dict(size=13, color=INK_COLOR, family=ARABIC_PLOT_FONT),
        )
        fig.update_layout(height=345, template='plotly_white', paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG)
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
        fit_label = f"الميل الخطي ({format_bound(dr['slope_decade'])} {rate_unit_ar})"
        vcode = trial['verdict_code']
        fit_color = SITE_B_COLOR if vcode == 'positive_difference' else (SITE_A_COLOR if vcode == 'negative_difference' else '#495b5f')
    else:
        fitted_vals = zeros
        fit_label = 'الميل الخطي معلّق (<30 سنة متصلة)'
        fit_color = '#9aa5a7'

    y_range_orig = _padded_axis_range(a_dev, b_dev)
    y_range_mid = _padded_axis_range(0.45 * a_dev, 0.45 * b_dev + 0.55 * diff_vals, 0.55 * diff_vals)
    y_range_diff = _padded_axis_range(diff_vals, fitted_vals) if eligible else _padded_axis_range(diff_vals)

    fig.add_trace(
        go.Scatter(
            x=years,
            y=zeros,
            mode='lines+markers',
            name=f"● شذوذ {loc_a_ar} ({unit_ar})",
            line=dict(color=SITE_A_COLOR, width=2.0, dash='solid'),
            marker=dict(symbol='circle', size=5.5, color=SITE_A_COLOR),
            opacity=0.0,
            showlegend=False,
            hovertemplate=f"<b>شذوذ {loc_a_ar}</b> (%{{x}}): %{{y:+.2f}} {unit_ar}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=zeros,
            mode='lines+markers',
            name=f"◆ شذوذ {loc_b_ar} ({unit_ar})",
            line=dict(color=SITE_B_COLOR, width=2.0, dash='dot'),
            marker=dict(symbol='diamond', size=6.0, color=SITE_B_COLOR),
            opacity=0.0,
            showlegend=False,
            hovertemplate=f"<b>شذوذ {loc_b_ar}</b> (%{{x}}): %{{y:+.2f}} {unit_ar}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=diff_vals,
            mode='lines+markers',
            name=f"D(سنة) = {loc_b_ar} − {loc_a_ar} ({unit_ar})",
            line=dict(color=INK_COLOR, width=2.3, dash='solid'),
            marker=dict(
                symbol='circle',
                size=6.5,
                color=[SITE_B_COLOR if v >= 0 else SITE_A_COLOR for v in diff_vals],
                line=dict(width=1.0, color='#ffffff'),
            ),
            opacity=1.0,
            hovertemplate=f"<b>D(%{{x}}) = {loc_b_ar} − {loc_a_ar}</b>: %{{y:+.2f}} {unit_ar}<extra></extra>",
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
            hovertemplate=f"<b>القيمة المقدّرة D(%{{x}})</b>: %{{y:+.2f}} {unit_ar}<extra></extra>",
        )
    )

    fig.add_hline(y=0.0, line_width=1.8, line_dash='dot', line_color='#66767a')
    fig.add_annotation(
        x=0.99,
        y=0.0,
        xref='paper',
        yref='y',
        xanchor='right',
        yshift=-11,
        text='0.0 (انعدام الفارق)',
        showarrow=False,
        font=dict(size=9.8, color='#45575b', family=ARABIC_PLOT_FONT),
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
            layout=go.Layout(yaxis=dict(title=f"الشذوذ الممركز ({unit_ar})", range=y_range_orig)),
        ),
        go.Frame(
            name='step1',
            data=[
                go.Scatter(x=years, y=0.45 * a_dev, opacity=0.45),
                go.Scatter(x=years, y=0.45 * b_dev + 0.55 * diff_vals, opacity=0.45),
                go.Scatter(x=years, y=0.55 * diff_vals, opacity=0.72),
                go.Scatter(x=years, y=0.55 * fitted_vals, opacity=0.55 if eligible else 0.0),
            ],
            layout=go.Layout(yaxis=dict(title=f"التحول نحو الاقتران ({unit_ar})", range=y_range_mid)),
        ),
        go.Frame(
            name='step2',
            data=[
                go.Scatter(x=years, y=zeros, opacity=0.0),
                go.Scatter(x=years, y=zeros, opacity=0.0),
                go.Scatter(x=years, y=diff_vals, opacity=1.0),
                go.Scatter(x=years, y=fitted_vals, opacity=1.0 if eligible else 0.0),
            ],
            layout=go.Layout(yaxis=dict(title=f"الفرق السنوي المقترن D ({unit_ar})", range=y_range_diff)),
        ),
    ]

    fig.update_layout(
        height=370,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family=ARABIC_PLOT_FONT, color=INK_COLOR, size=12),
        margin=dict(l=54, r=18, t=58, b=74),
        legend=dict(orientation='h', yanchor='top', y=-0.27, xanchor='left', x=0.0, font=dict(size=10.6), bgcolor='rgba(249,247,242,0.0)'),
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
                font=dict(size=10.2, color=INK_COLOR, family=ARABIC_PLOT_FONT),
                pad=dict(r=4, t=1, b=3),
                buttons=[
                    dict(
                        label='▶ تحريك التحول',
                        method='animate',
                        args=[['step0', 'step1', 'step2'], {'frame': {'duration': 900, 'redraw': False}, 'transition': {'duration': 650, 'easing': 'cubic-in-out'}, 'fromcurrent': False}],
                    ),
                    dict(
                        label='1. السلسلتان أ و ب',
                        method='animate',
                        args=[['step0'], {'mode': 'immediate', 'frame': {'duration': 500, 'redraw': False}, 'transition': {'duration': 450}}],
                    ),
                    dict(
                        label='2. الفرق المقترن D',
                        method='animate',
                        args=[['step2'], {'mode': 'immediate', 'frame': {'duration': 500, 'redraw': False}, 'transition': {'duration': 450}}],
                    ),
                ],
            )
        ],
        xaxis=dict(title='السنة التقويمية (أزواج متطابقة)', range=[trial['start'] - 0.6, trial['end'] + 0.6], gridcolor='#e3ded2', zeroline=False),
        yaxis=dict(title=f"الفرق السنوي المقترن D ({unit_ar})", range=y_range_diff, gridcolor='#e3ded2', zeroline=False),
        hovermode='x unified',
    )
    return fig


def verdict_code_or_default(trial):
    return trial.get('verdict_code', 'ineligible')


def build_trial_verdict_figure(trial, lens_mode):
    """Build Zero-Line Confidence Interval plot comparing D(year) = B - A against contextual solo intervals."""
    _, _, rate_unit_ar = ar_var(trial['parameter'])
    loc_a_ar = ar_loc(trial['site_a']['location'])
    loc_b_ar = ar_loc(trial['site_b']['location'])
    fig = go.Figure()
    fig.add_vline(x=0.0, line_width=2.5, line_dash='solid', line_color=INK_COLOR)

    if not trial['eligible']:
        fig.add_annotation(
            x=0.0,
            y=0.5,
            xref='x',
            yref='paper',
            text='<b>حُكم المحاكمة معلّق</b><br>يلزم توفر 30 سنة متصلة مكتملة ومشتركة<br>(مع تباين غير معدوم) لحساب مجالات OLS وHAC.',
            showarrow=False,
            font=dict(size=12, color=INK_COLOR, family=ARABIC_PLOT_FONT),
            bgcolor='#f5e6c8',
            bordercolor='#d4b475',
            borderwidth=1,
            borderpad=10,
        )
        fig.update_layout(
            height=370,
            template='plotly_white',
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=dict(family=ARABIC_PLOT_FONT, color=INK_COLOR, size=12),
            margin=dict(l=20, r=20, t=54, b=40),
            xaxis=dict(title=f"فرق الميل العقدي ({rate_unit_ar})", range=[-1, 1], gridcolor='#e3ded2'),
            yaxis=dict(visible=False),
        )
        return fig

    dr = trial['diff_result']
    ra = trial['aligned_site_a_result']
    rb = trial['aligned_site_b_result']
    slope_d = dr['slope_decade']

    show_cautious = lens_mode in ('both', 'cautious')
    show_iid = lens_mode in ('both', 'conventional')
    verdict_color = SITE_B_COLOR if trial['verdict_code'] == 'positive_difference' else (SITE_A_COLOR if trial['verdict_code'] == 'negative_difference' else '#46585c')

    all_bounds = [0.0, *dr['ci95'], *dr['iid_ci95']]
    if ra is not None:
        all_bounds.extend(ra['ci95'])
    if rb is not None:
        all_bounds.extend(rb['ci95'])

    span = max(all_bounds) - min(all_bounds)
    x_min = min(all_bounds) - max(span * 0.34, 0.14)
    x_max = max(all_bounds) + max(span * 0.50, 0.28)

    fig.add_annotation(
        x=0.0,
        y=1.18,
        xref='x',
        yref='y',
        text='<b>0.0 (انعدام الفرق)</b>',
        showarrow=False,
        font=dict(size=10.4, color=INK_COLOR, family=ARABIC_PLOT_FONT),
        bgcolor='#e5e0d3',
        bordercolor='#b8b09c',
        borderwidth=1,
        borderpad=3,
    )

    active_mode = trial.get('interval_mode', 'cautious')
    primary_ci_name = 'HAC خام 95% (SE_HAC)' if active_mode == 'hac' else 'المجال الوقائي 95% (HAC / max SE)'
    primary_hover = 'Newey–West HAC خام' if active_mode == 'hac' else 'المجال الوقائي HAC'
    y_d_base = 1.75

    fig.add_trace(
        go.Scatter(
            x=[slope_d],
            y=[y_d_base + (0.09 if lens_mode == 'both' else 0.0)],
            mode='markers',
            name=primary_ci_name,
            opacity=1.0 if show_cautious else 0.25,
            marker=dict(symbol='star', size=13, color=verdict_color, line=dict(width=1.4, color='#ffffff')),
            error_x=dict(type='data', symmetric=False, array=[dr['ci95'][1] - slope_d], arrayminus=[slope_d - dr['ci95'][0]], color=verdict_color, thickness=4.6, width=8),
            hovertemplate=(
                f"<b>الفرق المقترن D = {loc_b_ar} − {loc_a_ar} ({primary_hover})</b><br>"
                f"فرق الميل: {format_bound(slope_d)} {rate_unit_ar}<br>"
                f"مجال الثقة 95%: {format_interval(dr['ci95'], '')}<br>"
                f"p = {dr['p_value']:.4g}<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[slope_d],
            y=[y_d_base - (0.11 if lens_mode == 'both' else 0.0)],
            mode='markers',
            name='OLS اعتيادي 95%',
            opacity=0.95 if show_iid else 0.22,
            marker=dict(symbol='circle-open', size=9, color='#455c61', line=dict(width=2, color='#455c61')),
            error_x=dict(type='data', symmetric=False, array=[dr['iid_ci95'][1] - slope_d], arrayminus=[slope_d - dr['iid_ci95'][0]], color='#52696e', thickness=2.2, width=5),
            hovertemplate=(
                f"<b>الفرق المقترن D = {loc_b_ar} − {loc_a_ar} (OLS الاعتيادي)</b><br>"
                f"فرق الميل: {format_bound(slope_d)} {rate_unit_ar}<br>"
                f"مجال الثقة 95%: {format_interval(dr['iid_ci95'], '')}<br>"
                f"p = {dr['iid_p']:.4g}<extra></extra>"
            ),
        )
    )

    active_ci = trial['active_ci']
    v_badge = 'يستبعد 0' if trial['active_excludes_zero'] else 'يعبر 0 · غير حاسم'
    ci_ltr = f"\u2066[{format_bound(active_ci[0])}, {format_bound(active_ci[1])}]\u2069"
    slope_ltr = f"\u2066{format_bound(slope_d)}\u2069"
    fig.add_annotation(
        x=0.5,
        y=2.14,
        xref='paper',
        yref='y',
        xanchor='center',
        text=f"<b>⚖ ب − أ: {slope_ltr}</b> {ci_ltr} · <b>{v_badge}</b>",
        showarrow=False,
        font=dict(size=10.6, color=verdict_color, family=ARABIC_PLOT_FONT),
        bgcolor='rgba(249,247,242,0.95)',
    )

    fig.add_hline(y=0.92, line_width=1.2, line_dash='dot', line_color='#cbc3b2')
    fig.add_annotation(
        x=0.5,
        y=0.98,
        xref='paper',
        yref='y',
        xanchor='center',
        text='المجالات المنفردة للسياق فقط (تداخلها لا يختبر فرق الميلين)',
        showarrow=False,
        font=dict(size=9.8, color='#55696e', family=ARABIC_PLOT_FONT),
        bgcolor=CHART_BG,
    )

    for c_ar, cres, y_pos, ccolor, csym, cglyph in [
        (loc_b_ar, rb, 0.45, SITE_B_COLOR, 'diamond', '◆'),
        (loc_a_ar, ra, 0.0, SITE_A_COLOR, 'circle', '●'),
    ]:
        if cres is None:
            continue
        cslope = cres['slope_decade']
        cci = cres['iid_ci95'] if lens_mode == 'conventional' else cres['ci95']
        cslope_ltr = f"\u2066{format_bound(cslope)}\u2069"
        cci_ltr = f"\u2066[{format_bound(cci[0])}, {format_bound(cci[1])}]\u2069"
        fig.add_trace(
            go.Scatter(
                x=[cslope],
                y=[y_pos],
                mode='markers',
                showlegend=False,
                opacity=0.68,
                marker=dict(symbol=csym, size=8.5, color=ccolor),
                error_x=dict(type='data', symmetric=False, array=[cci[1] - cslope], arrayminus=[cslope - cci[0]], color=ccolor, thickness=2.4, width=5),
                hovertemplate=(
                    f"<b>{c_ar} منفرداً (للسياق)</b><br>"
                    f"الميل: {format_bound(cslope)} {rate_unit_ar}<br>"
                    f"مجال الثقة 95%: {format_interval(cci, '')}<extra></extra>"
                ),
            )
        )
        fig.add_annotation(
            x=min(max(cslope, x_min + 0.16 * (x_max - x_min)), x_max - 0.24 * (x_max - x_min)),
            y=y_pos + 0.19,
            xref='x',
            yref='y',
            xanchor='center',
            text=f"{cglyph} {c_ar}: {cslope_ltr} {cci_ltr}",
            showarrow=False,
            font=dict(size=9.6, color=ccolor, family=ARABIC_PLOT_FONT),
            bgcolor='rgba(249,247,242,0.92)',
        )

    fig.update_layout(
        height=370,
        template='plotly_white',
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family=ARABIC_PLOT_FONT, color=INK_COLOR, size=12),
        margin=dict(l=98, r=24, t=58, b=74),
        legend=dict(orientation='h', yanchor='top', y=-0.27, xanchor='left', x=0.0, font=dict(size=10.6), bgcolor='rgba(249,247,242,0.0)'),
        xaxis=dict(title=f"المعدل العقدي ({rate_unit_ar})", range=[x_min, x_max], gridcolor='#e3ded2', zeroline=False),
        yaxis=dict(tickmode='array', tickvals=[0.0, 0.45, y_d_base], ticktext=[f"● {loc_a_ar}", f"◆ {loc_b_ar}", "<b>⚖ D = ب − أ</b>"], range=[-0.35, 2.38], gridcolor='#ece8de'),
    )
    return fig


def build_trial_provenance_payload(trial, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b):
    """Build machine-readable Evidence Passport JSON without legacy version labels."""
    dr = trial['diff_result']
    ra = trial['aligned_site_a_result']
    rb = trial['aligned_site_b_result']
    return {
        'platform': 'EarthPulse · The Climate Trial',
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
            'SE_HAC / SE_OLS measures relative change in estimated standard error only, never a Type-I error probability.',
            'Inconclusive result means interval crosses zero; it does NOT imply equal trends.',
        ],
    }


def build_evidence_passport_markdown(trial, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b):
    """Create a downloadable Arabic Markdown Evidence Summary for The Climate Trial."""
    loc_a_ar, loc_b_ar = ar_loc(loc_a), ar_loc(loc_b)
    var_ar, unit_ar, rate_unit_ar = ar_var(trial['parameter'])
    dr = trial['diff_result']
    ra = trial['aligned_site_a_result']
    rb = trial['aligned_site_b_result']
    lines = [
        "# نبض الأرض (EarthPulse) — جواز الأدلة المناخية",
        "",
        f"- **سؤال المحاكمة**: {format_trial_question_ar(loc_a, loc_b, trial['parameter'])}",
        f"- **الفرضية الإحصائية**: السلسلة المقترنة `D(سنة) = {loc_b_ar}(سنة) - {loc_a_ar}(سنة)`",
        f"- **المتغير المناخي**: {var_ar} (`{trial['parameter']}`، `{unit_ar}`)",
        f"- **الفترة الزمنية**: `{trial['start']}–{trial['end']}` (`{trial['n_paired']}` سنة مقترنة مكتملة)",
        f"- **افتراض عدم اليقين**: `{ar_mode_badge(trial['interval_mode'])}` (**تحليل استكشافي دون تصحيح لتعدد الاختبارات**)",
        f"- **الحُكم المشتق**: **{ar_trial_verdict_label(trial['verdict_code'])}**",
        "",
    ]
    if trial['eligible'] and dr is not None:
        corr_v = f"`{trial['residual_correlation']:+.3f}`" if trial['residual_correlation'] is not None else 'غير متاح'
        id_v = f"`{trial['slope_diff_identity_delta']:.2e}`" if trial['slope_diff_identity_delta'] is not None else 'غير متاح'
        lines.extend([
            "## استدلال الفرق المقترن (`D = B - A`)",
            "",
            "| المعيار | القيمة |",
            "| :--- | :--- |",
            f"| فرق الميل العقدي المقدّر | `{format_bound(dr['slope_decade'])} {rate_unit_ar}` (`{dr['slope_decade']:+.5f}`) |",
            f"| مجال 95% الوقائي (`max SE`، `{dr['hac_lags']}` فجوات) | `{format_interval(dr['ci95'], rate_unit_ar)}` (`p = {dr['p_value']:.4g}`) |",
            f"| مجال 95% الاعتيادي (`OLS`) | `{format_interval(dr['iid_ci95'], rate_unit_ar)}` (`p = {dr['iid_p']:.4g}`) |",
            f"| الارتباط الذاتي للبواقي المقترنة (`ρ₁`) | `{dr['residual_lag1']:+.3f}` |",
            f"| ارتباط البواقي عبر الموقعين (`r`) | {corr_v} |",
            f"| التحقق من المتطابقة الجبرية `OLS` | {id_v} |",
            "",
        ])
    if ra is not None and rb is not None:
        lines.extend([
            "## الاتجاهات الفردية المتطابقة زمنياً",
            "",
            f"- **{loc_a_ar}** (`{lat_a:.4f}°N, {lon_a:.4f}°E`): `{format_bound(ra['slope_decade'])} {rate_unit_ar}`، مجال 95% `{format_interval(ra['ci95'], rate_unit_ar)}` (`ρ₁ = {ra['residual_lag1']:+.3f}`)",
            f"- **{loc_b_ar}** (`{lat_b:.4f}°N, {lon_b:.4f}°E`): `{format_bound(rb['slope_decade'])} {rate_unit_ar}`، مجال 95% `{format_interval(rb['ci95'], rate_unit_ar)}` (`ρ₁ = {rb['residual_lag1']:+.3f}`)",
            "",
        ])
    lines.extend([
        "## موثوقية المصدر والبيانات الوصفية من NASA",
        "",
        f"- **الأصل المصدري**: `{data_a.get('_earthpulse', {}).get('data_origin', 'NASA POWER API')}`",
        f"- **ترويسة NASA**: `{data_a.get('header', {}).get('title', 'NASA/POWER MERRA-2')}` (`API {data_a.get('header', {}).get('api', {}).get('version', 'unknown')}`)",
        f"- **رابط طلب {loc_a_ar}**: {data_a.get('_earthpulse', {}).get('request_url', 'لقطة MERRA-2 الموثقة')}",
        f"- **رابط طلب {loc_b_ar}**: {data_b.get('_earthpulse', {}).get('request_url', 'لقطة MERRA-2 الموثقة')}",
    ])
    return "\n".join(lines)


# --- Sidebar Controls ---
with st.sidebar:
    st.header('عناصر تحكم نبض الأرض')
    data_mode_key = st.radio(
        'مصدر البيانات',
        ['bundled', 'live'],
        format_func=lambda k: 'لقطات NASA الموثقة (بدون إنترنت · 1991–2025)' if k == 'bundled' else 'واجهة NASA POWER الحية (Live API)',
        index=0,
    )
    st.caption(
        'تغطي اللقطات الموثقة الدار البيضاء والرباط ومراكش وورزازات للفترة 1991–2025. '
        'الإحداثيات المخصصة أو السنوات الأقدم (1981–1990) تستعلم مباشرةً من NASA POWER دون بيانات اصطناعية.'
    )
    st.divider()
    st.caption('تصميم وتطوير حفيظة بلعيد · مختبرات نبض الأرض، الدار البيضاء. نموذج بحثي مستقل لـ NASA Space Apps 2026 دون اعتماد رسمي من ناسا.')


# --- Session Defaults (Canonical English State Keys for Data Integrity) ---
st.session_state.setdefault('trial_tested', False)
st.session_state.setdefault('trial_loc_a', 'Casablanca')
st.session_state.setdefault('trial_loc_b', 'Marrakech')
st.session_state.setdefault('trial_param', 'T2M')
st.session_state.setdefault('trial_period', (1991, 2025))
st.session_state.setdefault('trial_lens', LENS_KEYS[0])
if st.session_state.get('trial_lens') not in LENS_CONFIG:
    st.session_state['trial_lens'] = LENS_KEYS[0]


def _on_trial_period_slider():
    st.session_state['trial_period'] = st.session_state['trial_period_slider']


def _apply_trial_preset(loc_a_v, loc_b_v, param_v, period_v=(1991, 2025)):
    st.session_state['trial_loc_a'] = loc_a_v
    st.session_state['trial_loc_b'] = loc_b_v
    st.session_state['trial_param'] = param_v
    st.session_state['trial_period'] = period_v
    st.session_state.pop('trial_period_slider', None)
    st.session_state['trial_tested'] = True


# --- Top Unified Header & Navigation ---
st.markdown(
    '<div class="eyebrow-row">'
    '<span class="eyebrow">نبض الأرض · محاكمة المناخ — ضع الادعاءات المناخية أمام الدليل الإحصائي</span>'
    '<span class="provenance-badge">تحليل استكشافي · NASA POWER / MERRA-2 · قاعدة 30 سنة · Newey–West HAC</span>'
    '</div>',
    unsafe_allow_html=True,
)

nav_key = st.radio(
    'وضع الاستقصاء',
    options=['trial', 'single'],
    format_func=lambda k: 'محاكمة المناخ (مقارنة موقعين بالسلاسل المقترنة)' if k == 'trial' else 'فحص موقع منفرد أو إحداثيات عالمية مخصصة',
    index=0,
    horizontal=True,
    label_visibility='collapsed',
)

render_step_ribbon()

if nav_key == 'trial':
    trial_loc_options = list(LOCATIONS.keys()) + ['Custom coordinates']

    tc1, tc2, tc3 = st.columns([1.05, 1.05, 1.3])
    with tc1:
        loc_a_choice = st.selectbox('الموقع أ (● خط الأساس)', trial_loc_options, format_func=ar_loc, key='trial_loc_a')
        if loc_a_choice == 'Custom coordinates':
            ca1, ca2 = st.columns(2)
            lat_a = ca1.number_input('خط العرض أ (°N)', -90.0, 90.0, 33.5731, step=0.01, format='%.4f', key='trial_lat_a')
            lon_a = ca2.number_input('خط الطول أ (°E)', -180.0, 180.0, -7.5898, step=0.01, format='%.4f', key='trial_lon_a')
            loc_a = f"Custom A ({lat_a:.2f}°, {lon_a:.2f}°)"
        else:
            loc_a = loc_a_choice
            lat_a, lon_a = LOCATIONS[loc_a]
    with tc2:
        loc_b_choice = st.selectbox('الموقع ب (◆ المنافس)', trial_loc_options, format_func=ar_loc, key='trial_loc_b')
        if loc_b_choice == 'Custom coordinates':
            cb1, cb2 = st.columns(2)
            lat_b = cb1.number_input('خط العرض ب (°N)', -90.0, 90.0, 31.6295, step=0.01, format='%.4f', key='trial_lat_b')
            lon_b = cb2.number_input('خط الطول ب (°E)', -180.0, 180.0, -7.9811, step=0.01, format='%.4f', key='trial_lon_b')
            loc_b = f"Custom B ({lat_b:.2f}°, {lon_b:.2f}°)"
        else:
            loc_b = loc_b_choice
            lat_b, lon_b = LOCATIONS[loc_b]
    with tc3:
        parameter = st.selectbox(
            'المتغير المناخي المشترك',
            list(VARIABLES.keys()),
            format_func=lambda k: f"{ar_var(k)[0]} ({ar_var(k)[1]})",
            key='trial_param',
        )

    start, end = st.session_state['trial_period']
    interval_mode, whisker_lens = resolve_lens(st.session_state['trial_lens'])

    try:
        with st.spinner('جارٍ استرجاع سجلات NASA POWER المقترنة…'):
            data_a, bundled_a = load_location_data(loc_a_choice, lat_a, lon_a, start, end, data_mode_key)
            data_b, bundled_b = load_location_data(loc_b_choice, lat_b, lon_b, start, end, data_mode_key)

        trial = climate_trial(loc_a, data_a, loc_b, data_b, parameter=parameter, start=start, end=end, interval_mode=interval_mode)
        comp = compare_locations(loc_a, data_a, loc_b, data_b, parameter=parameter, start=start, end=end, interval_mode=interval_mode)

        loc_a_ar, loc_b_ar = ar_loc(loc_a), ar_loc(loc_b)
        var_ar, unit_ar, rate_unit_ar = ar_var(parameter)

        # Opening Trial Question
        pair_eq_ar = f"D(سنة) = {loc_b_ar} − {loc_a_ar}"
        st.markdown(
            f'<p class="trial-tagline">محاكمة المناخ · «ضع الادعاءات المناخية أمام الدليل الإحصائي»</p>'
            f'<div class="editorial-headline">{format_trial_question_ar(loc_a, loc_b, parameter)}</div>'
            f'<p class="trial-subq"><b>هل يختلف الاتجاهان المناخيان عن بعضهما بدلالة إحصائية؟</b> '
            f'تُطرح السلاسل السنوية المتطابقة سنةً بسنة في سلسلة الفروق <b dir="rtl">{pair_eq_ar}</b> خلال {ltr(f"{start}–{end}")} '
            f'<span class="provenance-badge">استكشافي · {ltr(trial["n_paired"])} سنة مقترنة</span></p>',
            unsafe_allow_html=True,
        )

        # Two-City Face-Off Cards + Central TEST THE DIFFERENCE Action
        sa, sb = trial['site_a'], trial['site_b']

        def _site_card_html(site_info, coords, role_label, extra_cls, accent_color):
            lat_v, lon_v = coords
            c_ar = ar_loc(site_info['location'])
            if site_info['eligible']:
                sr = site_info['result']
                ex = site_info['active_excludes_zero']
                ci_active = site_info['active_ci']
                bcls = 'badge-clear' if ex else 'badge-cautious'
                btxt = 'يستبعد 0' if ex else 'يعبر 0'
                sr_mean_s = f"{sr['mean']:.2f}"
                sr_lag_s = f"ρ₁ = {sr['residual_lag1']:+.2f}"
                body = (
                    f'<div class="city-card-rate" style="color:{accent_color};">'
                    f'{ltr(format_bound(sr["slope_decade"]))} <span style="font-size:0.9rem;font-weight:600;">{rate_unit_ar}</span></div>'
                    f'<div class="city-card-meta">'
                    f'مجال 95%: <b>{ltr(format_interval(ci_active, ""))}</b> <span class="{bcls}">{btxt}</span><br>'
                    f'المتوسط: {ltr(sr_mean_s)} {unit_ar} · الارتباط الذاتي {ltr(sr_lag_s)}'
                    f'</div>'
                )
            else:
                body = (
                    f'<div class="city-card-rate" style="color:#6e4b0c;font-size:1.15rem;">الاستدلال معلّق</div>'
                    f'<div class="city-card-meta">توفر {ltr(site_info["n_complete"])} سنة مكتملة في {ltr(f"{start}–{end}")}. '
                    f'يشترط توفر 30 سنة متصلة مكتملة على الأقل.</div>'
                )
            return (
                f'<div class="city-card {extra_cls}">'
                f'<div class="city-card-kicker">{role_label} · {ltr(f"{lat_v:.2f}°N, {lon_v:.2f}°E")}</div>'
                f'<div class="city-card-name">{c_ar}</div>'
                f'{body}'
                f'</div>'
            )

        face_a, face_vs, face_b = st.columns([1.15, 0.95, 1.15], gap='medium')
        with face_a:
            st.markdown(_site_card_html(sa, (lat_a, lon_a), '● الموقع أ (الأساس)', 'city-card-a', SITE_A_COLOR), unsafe_allow_html=True)
        with face_vs:
            overlap_hint = (
                'تتداخل المجالات المنفردة 95%؛ لكن التداخل وحده لا يحسم أبداً هل يختلف الميلان.'
                if trial['separate_intervals_overlap']
                else 'لا تستنتج اختلاف الاتجاهين من المجالات المنفردة وحدها — اختبر سلسلة D(سنة) مباشرةً.'
            )
            vs_badge = 'المحاكمة مفعّلة · ب − أ' if st.session_state['trial_tested'] else 'المواجهة · H₀: ميل(ب) = ميل(أ)'
            st.markdown(
                f'<div class="vs-card">'
                f'<div class="vs-pill">{vs_badge}</div>'
                f'<div class="vs-prompt">{overlap_hint}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            btn_label = '⚖ اختبر الفارق الإحصائي' if not st.session_state['trial_tested'] else '↻ أعد إجراء المحاكمة'
            if st.button(btn_label, type='primary', use_container_width=True, key='trial_run_btn'):
                st.session_state['trial_tested'] = True
        with face_b:
            st.markdown(_site_card_html(sb, (lat_b, lon_b), '◆ الموقع ب (المنافس)', 'city-card-b', SITE_B_COLOR), unsafe_allow_html=True)

        if trial['years_a_only'] or trial['years_b_only']:
            st.warning(
                f"تم استبعاد السنوات غير المكتملة أو غير المتطابقة دون استكمال اصطناعي: "
                f"السنوات المستبعدة ({', '.join(map(str, trial['missing_paired']))})."
            )

        if st.session_state['trial_tested']:
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
                corr_txt = f"{trial['residual_correlation']:+.2f}" if trial['residual_correlation'] is not None else 'غير متاح'
                id_txt = f"{trial['slope_diff_identity_delta']:.1e}" if trial['slope_diff_identity_delta'] is not None else 'غير متاح'
                dr_exact_s = f"{dr['slope_decade']:+.5f}"
                p_active_s = f"p = {trial['active_p']:.4g}"
                dr_lag_s = f"ρ₁ = {dr['residual_lag1']:+.2f}"
                metrics_html = (
                    f'<div class="trial-metrics-grid">'
                    f'<div class="trial-metric-box"><div class="trial-metric-label">فرق الميل العقدي (ب − أ)</div>'
                    f'<div class="trial-metric-value">{ltr(format_bound(dr["slope_decade"]))} <span style="font-size:0.86rem;">{rate_unit_ar}</span></div>'
                    f'<div class="trial-metric-sub">الدقة الكاملة: {ltr(dr_exact_s)}</div></div>'
                    f'<div class="trial-metric-box"><div class="trial-metric-label">مجال 95% وقيمة p الاستكشافية</div>'
                    f'<div class="trial-metric-value">{ltr(format_interval(trial["active_ci"], ""))}</div>'
                    f'<div class="trial-metric-sub">{ltr(p_active_s)} · {ar_mode_badge(interval_mode)}</div></div>'
                    f'<div class="trial-metric-box"><div class="trial-metric-label">إزالة التشويش الإقليمي المشترك</div>'
                    f'<div class="trial-metric-value">{ltr(f"r = {corr_txt}")}</div>'
                    f'<div class="trial-metric-sub">ارتباط البواقي المقترنة {ltr(dr_lag_s)}</div></div>'
                    f'<div class="trial-metric-box"><div class="trial-metric-label">التحقق من متطابقة OLS</div>'
                    f'<div class="trial-metric-value">{ltr(f"Δ = {id_txt}")}</div>'
                    f'<div class="trial-metric-sub">{ltr("slope(B−A) == slope(B) − slope(A)")}</div></div>'
                    f'</div>'
                )
            else:
                metrics_html = ''

            st.markdown(
                f'<div class="trial-reveal-panel">'
                f'<div class="verdict-banner {v_banner_cls}">'
                f'<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:0.4rem;">'
                f'<span class="{v_pill_cls}">{ar_trial_verdict_label(vcode)}</span>'
                f'<span class="provenance-badge">استكشافي · {ltr(f"D(year) = {loc_b} − {loc_a} ({start}–{end})")}</span>'
                f'</div>'
                f'{metrics_html}'
                f'<p style="margin:0.5rem 0 0.28rem 0;font-size:0.96rem;color:#14282d;line-height:1.68;">{ar_trial_interpretation(trial, loc_a_ar, loc_b_ar)}</p>'
                f'<p style="margin:0.2rem 0 0 0;font-size:0.86rem;color:#3c5358;line-height:1.6;">{ar_overlap_insight(trial, loc_a_ar, loc_b_ar)}</p>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # --- STEP 1 ---
        render_grid_reality_section(
            loc_a, data_a, lat_a, lon_a, loc_b, data_b, lat_b, lon_b, parameter, start, end, interval_mode=interval_mode
        )

        # --- STEP 2 ---
        step2_active_desc = {
            'cautious': 'الوقائي max(SE_OLS, SE_HAC) مقابل OLS',
            'hac': 'Newey–West HAC الخام مقابل OLS',
            'conventional': 'الانحدار الاعتيادي OLS فقط',
        }.get(interval_mode, interval_mode)

        render_step_banner(
            2,
            'ما مدى قوة الدليل الإحصائي؟',
            'الاتجاهات المناخية، محاكمة الفرق المقترن، وعدسة عدم اليقين',
            'افحص السلاسل المتطابقة، واختبر حساسية الفترة الزمنية أو افتراضات الخطأ المعياري، وقارن SE_OLS وSE_HAC الخام والحد الوقائي.',
            badge=f'{ltr(trial["n_paired"])} سنة مقترنة · استكشافي',
        )

        if not st.session_state['trial_tested']:
            p_left, p_right = st.columns([1.12, 1.0])
            with p_left:
                st.markdown(
                    f'<div class="chart-header-box">'
                    f'<div class="chart-header-title">السلاسل السنوية المتطابقة والميول الخطية ({unit_ar})</div>'
                    f'<div class="chart-header-sub">اضغط «اختبر الفارق الإحصائي» أعلاه لتشغيل التحول المتحرك نحو سلسلة الفروق {ltr(f"D(year) = {loc_b} − {loc_a}")}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(build_comparison_series_figure(comp), use_container_width=True)
            with p_right:
                st.markdown(
                    f'<div class="chart-header-box">'
                    f'<div class="chart-header-title">مجالات الثقة الفردية حول خط الصفر ({rate_unit_ar})</div>'
                    f'<div class="chart-header-sub">يختبر كل مجال موقعاً واحداً مقابل 0.0 · ({step2_active_desc})</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(build_whisker_figure(comp, whisker_lens), use_container_width=True)

            render_uncertainty_lens_panel(
                [(loc_a_ar, sa['result']), (loc_b_ar, sb['result'])],
                interval_mode,
                unit_ar,
                rate_unit_ar,
                lens_state_key='trial_lens',
                show_control=True,
            )
            st.caption('انقر على زر **⚖ اختبر الفارق الإحصائي** أعلاه لحساب سطر المحاكمة المقترنة `D = ب − أ` وتشغيل التحول التفاعلي.')
        else:
            t_left, t_right = st.columns([1.15, 1.0])
            with t_left:
                st.markdown(
                    f'<div class="chart-header-box">'
                    f'<div class="chart-header-title">سلسلة الفروق السنوية المقترنة ({loc_b_ar} − {loc_a_ar}) ({unit_ar})</div>'
                    f'<div class="chart-header-sub">استخدم زر «▶ تحريك التحول» أعلى الرسم لمشاهدة تحوّل المسارين أ و ب إلى الفرق المقترن D(سنة)</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(build_trial_transition_figure(trial), use_container_width=True)
            with t_right:
                st.markdown(
                    f'<div class="chart-header-box">'
                    f'<div class="chart-header-title">حُكم الفارق حول خط الصفر المرجعي ({rate_unit_ar})</div>'
                    f'<div class="chart-header-sub">خط الصفر المرجعي (0.0 = انعدام الفارق) · {step2_active_desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(build_trial_verdict_figure(trial, whisker_lens), use_container_width=True)

            # --- Challenge the Verdict Investigation Panel ---
            with st.container(border=True):
                st.markdown(
                    '<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:0.4rem;">'
                    '<h3 style="margin:0;font-size:1.15rem;">اختبر صلابة الحُكم · لوحة الحساسية الاستكشافية</h3>'
                    '<span class="provenance-badge">استكشافي · دون تصحيح لتعدد الفترات والأزواج</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                ch1, ch2 = st.columns([1.05, 1.25])
                with ch1:
                    st.slider(
                        'نطاق التحليل الزمني (يتطلب 30 سنة متصلة مكتملة على الأقل)',
                        1981,
                        2025,
                        value=st.session_state['trial_period'],
                        key='trial_period_slider',
                        on_change=_on_trial_period_slider,
                    )
                with ch2:
                    st.radio(
                        'افتراض عدم اليقين (OLS مقابل HAC الخام مقابل الوقائي)',
                        LENS_KEYS,
                        format_func=lambda k: LENS_CONFIG[k][2],
                        horizontal=True,
                        key='trial_lens',
                    )

                st.caption('جرّب ادعاءً مناخياً آخر فوراً من سجلات NASA الموثقة:')
                q1, q2, q3, q4 = st.columns(4)
                q1.button('مراكش − البيضاء · حرارة', on_click=_apply_trial_preset, args=('Casablanca', 'Marrakech', 'T2M'), use_container_width=True, key='preset_pos')
                q2.button('البيضاء − مراكش · حرارة', on_click=_apply_trial_preset, args=('Marrakech', 'Casablanca', 'T2M'), use_container_width=True, key='preset_neg')
                q3.button('الرباط − البيضاء · حرارة', on_click=_apply_trial_preset, args=('Casablanca', 'Rabat', 'T2M'), use_container_width=True, key='preset_inc_t2m')
                q4.button('مراكش − البيضاء · أمطار', on_click=_apply_trial_preset, args=('Casablanca', 'Marrakech', 'PRECTOTCORR'), use_container_width=True, key='preset_inc_rain')

                ch_tab_sens, ch_tab_series = st.tabs([
                    'عدسة OLS وHAC والبرهان الجبري',
                    f'سلسلة الفروق سنةً بسنة D(سنة) ({trial["n_paired"]} سنة)',
                ])
                with ch_tab_sens:
                    if trial['eligible']:
                        dr = trial['diff_result']
                        ra = trial['aligned_site_a_result']
                        rb = trial['aligned_site_b_result']
                        render_uncertainty_lens_panel(
                            [
                                (f'الفرق المقترن D = {loc_b_ar} − {loc_a_ar}', dr),
                                (f'{loc_b_ar} (سنوات متطابقة)', rb),
                                (f'{loc_a_ar} (سنوات متطابقة)', ra),
                            ],
                            interval_mode,
                            unit_ar,
                            rate_unit_ar,
                            show_control=False,
                        )
                        st.caption(
                            f"**البرهان الجبري لميل OLS:** `slope(B − A) = {dr['slope_decade']:+.6f}` مقابل "
                            f"`({rb['slope_decade']:+.6f}) − ({ra['slope_decade']:+.6f}) = "
                            f"{rb['slope_decade'] - ra['slope_decade']:+.6f}` "
                            f"(`|Δ| = {trial['slope_diff_identity_delta']:.1e}`)."
                        )
                    else:
                        st.warning('الاستدلال معلّق: لا تتوافر 30 سنة متصلة مكتملة متطابقة.')

                with ch_tab_series:
                    mdf = trial['merged']
                    if not mdf.empty:
                        rows_html = []
                        for _, row in mdf.iterrows():
                            va_s = f"{row['value_a']:.2f}"
                            vb_s = f"{row['value_b']:.2f}"
                            df_s = f"{row['diff']:+.3f}"
                            fit_td = ltr(f"{row['fitted_diff']:+.3f}") if 'fitted_diff' in mdf.columns else '—'
                            res_td = ltr(f"{row['residual_diff']:+.3f}") if 'residual_diff' in mdf.columns else '—'
                            rows_html.append(
                                f"<tr><td>{ltr(int(row['year']))}</td>"
                                f"<td>{ltr(va_s)}</td>"
                                f"<td>{ltr(vb_s)}</td>"
                                f"<td><b>{ltr(df_s)}</b></td>"
                                f"<td>{fit_td}</td>"
                                f"<td>{res_td}</td></tr>"
                            )
                        st.markdown(
                            f'<div class="table-wrapper" tabindex="0" role="region" aria-label="سلسلة الفروق السنوية المقترنة">'
                            f'<table><thead><tr>'
                            f'<th>السنة</th>'
                            f'<th>{loc_a_ar} ({unit_ar})</th>'
                            f'<th>{loc_b_ar} ({unit_ar})</th>'
                            f'<th>{ltr("D(year) = B − A")}</th>'
                            f'<th>القيمة المقدّرة</th>'
                            f'<th>البواقي</th>'
                            f'</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.info('لا توجد أزواج سنوية مكتملة في هذه النافذة.')

        # Deep-dive Scientific Diagnostics Expander (preserves full 4-city matrix, persistence, window checks cleanly)
        with st.expander('تشخيصات علمية معمّقة · ثبات البواقي (ρ₁)، الخلايا المغربية الأربع، وحساسية النوافذ (+30 سنة)'):
            tab_resid, tab_matrix, tab_window = st.tabs([
                '1. ثبات البواقي المتسلسلة (ρ₁)',
                '2. مقارنة المواقع المرجعية الأربع',
                '3. استقرار النوافذ الزمنية (+30 سنة)',
            ])
            with tab_resid:
                if comp['both_eligible']:
                    r_col1, r_col2 = st.columns([1.15, 1.0])
                    with r_col1:
                        st.markdown(
                            '<div class="chart-header-box">'
                            '<div class="chart-header-title">الارتباط الذاتي للبواقي من الدرجة الأولى (eₜ₋₁ مقابل eₜ)</div>'
                            '<div class="chart-header-sub">يؤدي الارتباط الموجب بين السنوات المتعاقبة إلى تكتل الشذوذات واتساع مجال Newey–West HAC</div>'
                            '</div>',
                            unsafe_allow_html=True,
                        )
                        st.plotly_chart(build_residual_persistence_figure(comp), use_container_width=True)
                    with r_col2:
                        sa_lag_s = f"ρ₁ = {sa['result']['residual_lag1']:+.2f}"
                        sb_lag_s = f"ρ₁ = {sb['result']['residual_lag1']:+.2f}"
                        st.markdown('#### لماذا تغيّر ذاكرة البواقي حُكم الاتجاه؟')
                        st.write(
                            f"يعامل الانحدار الاعتيادي OLS كل سنة كأنها رمية نرد مستقلة تماماً عن سابقتها. "
                            f"عندما تُظهر البواقي ذاكرةً زمنية موجبة كما في **{loc_a_ar}** "
                            f"(حيث معامل الارتباط الذاتي **{ltr(sa_lag_s)}**)، "
                            "تميل السنوات الدافئة إلى التجمّع معاً، مما يقلص درجات الحرية الفعلية."
                        )
                        st.write(
                            f"تصحّح أخطاء Newey–West HAC المعيارية هذا الارتباط قصير المدى ({ltr(sa['result']['hac_lags'])} فجوات سنوية). "
                            f"في **{loc_b_ar}** ({ltr(sb_lag_s)}) تبقى الذاكرة الزمنية أضعف والميل أكثر حدة، "
                            f"فيظل مجاله **{'مستبعداً للصفر' if sb['cautious_excludes_zero'] else 'عابراً للصفر'}**."
                        )
                else:
                    st.info('اختر فترة متصلة لا تقل عن 30 سنة مكتملة لمعاينة مخطط ثبات البواقي.')

            with tab_matrix:
                st.markdown(f"#### خلايا الشبكة المرجعية الأربع في المغرب ({var_ar}، الأساس الموثق 1991–2025)")
                m_rows = []
                for city in LOCATIONS:
                    snap_path = Path(__file__).parent / 'data' / f'{city.lower()}.json'
                    if snap_path.exists():
                        cdata = json.loads(snap_path.read_text())
                        cev = evaluate_site(city, cdata, parameter, 1991, 2025)
                        if cev['eligible']:
                            cr = cev['result']
                            clat, clon = LOCATIONS[city]
                            m_rows.append({
                                'المدينة (شبكة MERRA-2)': f"{ar_loc(city)} ({clat:.2f}°N, {clon:.2f}°E)",
                                f'المتوسط ({unit_ar})': f"{cr['mean']:.2f}",
                                f'الميل / عقد ({rate_unit_ar})': f"{format_bound(cr['slope_decade'])} ({cr['slope_decade']:+.5f})",
                                'مجال OLS 95%': format_interval(cr['iid_ci95'], ''),
                                'المجال الوقائي 95% (HAC)': format_interval(cr['ci95'], ''),
                                'معامل ρ₁': f"{cr['residual_lag1']:+.2f}",
                                'الحالة الوقائية': ar_site_status(cev['cautious_excludes_zero'], cr['slope_decade']),
                            })
                if m_rows:
                    st.dataframe(pd.DataFrame(m_rows), use_container_width=True, hide_index=True)
                    st.caption('مسح استكشافي للمناطق المناخية الأربع (دون تصحيح لتعدد المقارنات). تداخل هذه المجالات المنفردة لا يختبر فروق الميول بينها.')

            with tab_window:
                if bundled_a and bundled_b:
                    w_col1, w_col2 = st.columns([1.2, 1.0])
                    with w_col1:
                        st.markdown(
                            '<div class="chart-header-box">'
                            '<div class="chart-header-title">حساسية النتائج عبر النوافذ الفرعية (+30 سنة متصلة)</div>'
                            f'<div class="chart-header-sub">مقارنة مجالات الثقة 95% الوقائية لـ {loc_a_ar} و{loc_b_ar} عبر فترات من 30 إلى 35 سنة</div>'
                            '</div>',
                            unsafe_allow_html=True,
                        )
                        st.plotly_chart(build_window_sensitivity_figure(loc_a, data_a, loc_b, data_b, parameter), use_container_width=True)
                    with w_col2:
                        st.markdown('#### الوقاية من انتقاء بداية ونهاية السلسلة')
                        st.write(
                            'قد يتغيّر الميل الخطي المقدّر إذا وافقت سنة البداية أو النهاية شذوذاً مناخياً عابراً '
                            '(مثل برودة 1991–1993 عقب ثوران بيناتوبو أو موجات الدفء في 2022–2025). '
                            'يكشف فحص كل النوافذ الممتدة من 30 إلى 35 سنة هل الاستنتاج مستقر أم حساس لاختيار الحدود الزمنية.'
                        )
                        st.caption('ملاحظة: فحص نوافذ متداخلة متعددة أداة تشخيصية استكشافية وليس اختبار فرضيات متعدد الأسرة.')
                else:
                    st.info('فعّل خيار «لقطات NASA الموثقة» من القائمة الجانبية لفحص حساسية النوافذ ضمن سجل 1991–2025.')

        # --- STEP 3: Evidence Passport ---
        passport_md = build_evidence_passport_markdown(trial, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b)
        provenance_obj = build_trial_provenance_payload(trial, loc_a, lat_a, lon_a, loc_b, lat_b, lon_b, data_a, data_b)
        export_trial_df = trial['merged'].copy()
        export_trial_df['location_a'] = loc_a
        export_trial_df['location_b'] = loc_b
        export_trial_df['parameter'] = parameter
        export_trial_df['units'] = trial['unit']
        export_trial_df['source'] = 'NASA POWER / MERRA-2'

        render_evidence_passport_section(
            question_ar=format_trial_question_ar(loc_a, loc_b, parameter),
            question_en=format_trial_question(loc_a, loc_b, parameter),
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
            interval_mode=interval_mode,
            key_prefix='trial_passport',
            secondary_md=passport_md,
            secondary_md_name=f'earthpulse_trial_passport_{loc_a}_{loc_b}_{parameter}_{start}_{end}.md',
            export_df=export_trial_df,
            export_csv_name=f'earthpulse_trial_series_{loc_a}_{loc_b}_{parameter}_{start}_{end}.csv',
        )

        with st.expander('البيانات الوصفية من NASA POWER وملف موثوقية المحاكمة (JSON) والروابط المباشرة'):
            st.download_button(
                'تحميل سجل الموثوقية الكامل · JSON',
                json.dumps(provenance_obj, indent=2),
                f'earthpulse_trial_provenance_{loc_a}_{loc_b}_{parameter}_{start}_{end}.json',
                'application/json',
                key='trial_prov_json_btn',
            )
            st.json(provenance_obj)
            l1, l2 = st.columns(2)
            if data_a.get('_earthpulse', {}).get('request_url'):
                l1.link_button(f'فتح طلب NASA المباشر · {loc_a_ar}', data_a['_earthpulse']['request_url'])
            if data_b.get('_earthpulse', {}).get('request_url'):
                l2.link_button(f'فتح طلب NASA المباشر · {loc_b_ar}', data_b['_earthpulse']['request_url'])

    except Exception as error:
        st.error(f'تعذّر إتمام المحاكمة المناخية: {error}')
        st.info('يُرجى اختيار لقطات NASA الموثقة (1991–2025) أو إعادة المحاولة لاحقاً؛ لا يُستعاض عن السجلات ببيانات اصطناعية.')

else:
    # Single-location & global custom coordinates mode
    st.markdown(
        '<div class="editorial-headline">استقصاء موقع منفرد أو إحداثيات عالمية مخصصة</div>'
        '<p class="verdict-lead">افحص خلية MERRA-2 لمدينة مغربية مرجعية أو أدخل أي خط عرض وطول عالميين '
        'لاسترجاع السجلات الشهرية الحية من NASA POWER وتطبيق معيار 30 سنة مع عدسة Newey–West HAC.</p>',
        unsafe_allow_html=True,
    )

    s_col1, s_col2, s_col3 = st.columns([1.2, 1.2, 1.3])
    with s_col1:
        location = st.selectbox('الموقع', list(LOCATIONS) + ['Custom coordinates'], format_func=ar_loc, key='single_loc')
    lat, lon = LOCATIONS.get(location, (33.5731, -7.5898))
    if location == 'Custom coordinates':
        coord1, coord2 = st.columns(2)
        with coord1:
            lat = st.number_input('خط العرض (°N)', -90.0, 90.0, lat, step=0.01, format='%.4f', key='single_lat')
        with coord2:
            lon = st.number_input('خط الطول (°E)', -180.0, 180.0, lon, step=0.01, format='%.4f', key='single_lon')
    with s_col2:
        parameter = st.selectbox('المتغير', list(VARIABLES), format_func=lambda k: f"{ar_var(k)[0]} ({ar_var(k)[1]})", key='single_param')
    with s_col3:
        period = st.slider('السنوات التقويمية المكتملة', 1981, 2025, (1991, 2025), key='single_period')

    st.session_state.setdefault('single_lens', LENS_KEYS[0])
    if st.session_state.get('single_lens') not in LENS_CONFIG:
        st.session_state['single_lens'] = LENS_KEYS[0]
    single_lens_key = st.radio(
        'افتراض عدم اليقين (OLS مقابل HAC الخام مقابل الوقائي)',
        LENS_KEYS,
        format_func=lambda k: LENS_CONFIG[k][2],
        horizontal=True,
        key='single_lens',
    )
    interval_mode, _ = resolve_lens(single_lens_key)

    start, end = period
    try:
        with st.spinner('جارٍ جلب تقديرات NASA POWER المناخية…'):
            data, bundled = load_location_data(location, lat, lon, start, end, data_mode_key)

        site_eval = evaluate_site(location, data, parameter, start, end, interval_mode=interval_mode)
        frame, omitted, result = site_eval['frame'], site_eval['omitted'], site_eval['result']
        loc_display = ar_loc(location) if location != 'Custom coordinates' else f"إحداثيات مخصصة ({lat:.2f}°, {lon:.2f}°)"
        canonical_loc = location if location != 'Custom coordinates' else f"Custom ({lat:.2f}, {lon:.2f})"
        var_ar, unit_ar, rate_unit_ar = ar_var(parameter)

        st.caption(
            f"{loc_display} ({lat:.4f}°, {lon:.4f}°)  /  {var_ar} ({unit_ar})  /  {start}–{end}  /  "
            f"{'لقطة NASA الموثقة محلياً' if bundled else 'استعلام مباشر من NASA API (مخزن مؤقتاً 24 ساعة)'}"
        )
        if omitted:
            st.warning('السنوات غير المكتملة المستبعدة دون تعويض اصطناعي: ' + ', '.join(map(str, omitted)))
        if not site_eval['eligible'] and site_eval['error']:
            st.warning('يتطلب الاستدلال توفر 30 سنة تقويمية متصلة ومكتملة على الأقل دون فجوات.')

        # STEP 1
        render_grid_reality_section(canonical_loc, data, lat, lon, None, None, None, None, parameter, start, end, interval_mode=interval_mode)

        # STEP 2
        active_ci_label = {
            'cautious': 'المجال الوقائي 95% (max SE)',
            'hac': 'مجال HAC الخام 95% (SE_HAC)',
            'conventional': 'مجال OLS الاعتيادي 95%',
        }.get(interval_mode, 'مجال 95%')
        render_step_banner(
            2,
            'ما مدى قوة الدليل الإحصائي؟',
            'مسار الاتجاه للموقع المنفرد وعدسة عدم اليقين',
            'عاين السلسلة السنوية، الميل الخطي، وقارن بين OLS وSE_HAC الخام والمعيار الوقائي.',
            badge=f'{ltr(f"{start}–{end}")} · {ar_mode_badge(interval_mode)}',
        )

        if result:
            active_ci = site_eval['active_ci']
            c1, c2, c3, c4 = st.columns([1, 1.35, 1.35, 0.8])
            c1.metric('الميل العقدي المقدّر', f"{format_bound(result['slope_decade'])} {rate_unit_ar}")
            c2.metric(active_ci_label, format_interval(active_ci, unit_ar))
            c3.metric('مجال OLS الاعتيادي 95%', format_interval(result['iid_ci95'], unit_ar))
            c4.metric('السنوات المكتملة', str(result['n']))

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=frame.year,
                y=frame.value,
                mode='lines+markers',
                name='التقدير السنوي',
                line=dict(color=SITE_A_COLOR, width=2.2),
                marker=dict(size=6, symbol='circle'),
                hovertemplate='%{x}: %{y:.2f} ' + unit_ar + '<extra></extra>',
            )
        )
        if result:
            fig.add_trace(go.Scatter(x=frame.year, y=result['fitted'], name='الميل الخطي', line=dict(color=SITE_B_COLOR, width=3.2, dash='dash')))
        fig.update_layout(
            height=380,
            template='plotly_white',
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=dict(family=ARABIC_PLOT_FONT, color=INK_COLOR, size=12.5),
            margin=dict(l=52, r=20, t=36, b=36),
            legend=dict(orientation='h', y=1.08, x=0.0),
            xaxis_title='السنة التقويمية',
            yaxis_title=f'{var_ar} ({unit_ar})',
            hovermode='x unified',
        )
        st.plotly_chart(fig, use_container_width=True)

        if result:
            sig = site_eval['active_excludes_zero']
            dir_ar = 'زيادة' if result['slope_decade'] > 0 else 'تراجع'
            exact_sl_s = f"{result['slope_decade']:+.5f}"
            span_res_s = f"{result['start']}–{result['end']}"
            ci_res_s = format_interval(active_ci, '')
            st.subheader('ماذا يقول الدليل الإحصائي؟')
            st.write(
                f"في تمثيل شبكة NASA MERRA-2 لهذا الموقع، يُظهر **{var_ar}** اتجاهاً مقدّراً بالـ{dir_ar} بنحو "
                f"**{abs(result['slope_decade']):.2f} {rate_unit_ar}** ({ltr(exact_sl_s)}) "
                f"خلال الفترة {ltr(span_res_s)} ({ltr(result['n'])} سنة مكتملة). "
                + (
                    f"وفق افتراض {ar_mode_badge(interval_mode)}، يستبعد مجال الثقة 95% ({ltr(ci_res_s)} {rate_unit_ar}) الصفر."
                    if sig
                    else f"وفق افتراض {ar_mode_badge(interval_mode)}، يعبر مجال الثقة 95% ({ltr(ci_res_s)} {rate_unit_ar}) الصفر؛ أي لا يثبت وجود اتجاه خطي حاسم عند هذا المستوى."
                )
            )
            render_uncertainty_lens_panel([(loc_display, result)], interval_mode, unit_ar, rate_unit_ar, show_control=False)

        left, right = st.columns([1.2, 1])
        with left:
            st.subheader('سلسلة الأدلة الشفافة')
            st.write(
                'توفّر NASA POWER تقديرات إعادة تحليل شبكية من MERRA-2. يُحسب المتوسط الحراري السنوي بوزن عدد أيام كل شهر (شاملاً السنوات الكبيسة)، '
                'بينما يُجمع الهطول بضرب المعدل اليومي الشهري في أيام الشهر، مع اشتراط اكتمال الأشهر الـ12 دون قيم مفقودة.'
            )
        with right:
            st.subheader('اقرأ الحدود المنهجية')
            st.write(
                'تلك تقديرات شبكية إقليمية وليست قياسات محطة رصد محلية. يختلف المناخ المحلي عند السواحل أو الجبال داخل الخلية الواحدة، '
                'وتبقى اختبارات الدلالة استكشافية غير مصححة لتعدد المواقع والفترات ولا تُثبت السببية الفيزيائية بمفردها.'
            )

        with st.expander('البيانات الوصفية من المصدر والإحصاءات الدقيقة وقابلية الاستنساخ'):
            st.json({
                'NASA_header': data['header'],
                'returned_point': data['geometry'],
                'retrieval': data.get('_earthpulse', {}),
                'analysis': {k: v for k, v in (result or {}).items() if k != 'fitted'},
            })
            if data.get('_earthpulse', {}).get('request_url'):
                st.link_button('فتح رابط طلب NASA المباشر', data['_earthpulse']['request_url'])

        export = frame.assign(parameter=parameter, units=VARIABLES[parameter][1], latitude=lat, longitude=lon, source='NASA POWER / MERRA-2')
        render_evidence_passport_section(
            question_ar=f"هل يتغيّر {var_ar} في {loc_display} ({start}–{end})؟",
            question_en=f"Is {VARIABLES[parameter][0].lower()} changing at {canonical_loc} ({start}–{end})?",
            parameter=parameter,
            start=start,
            end=end,
            loc_a=canonical_loc,
            lat_a=lat,
            lon_a=lon,
            data_a=data,
            single_site=site_eval,
            interval_mode=interval_mode,
            key_prefix='single_passport',
            export_df=export,
            export_csv_name=f'earthpulse_{canonical_loc}_{parameter}_{start}_{end}.csv',
        )
    except Exception as error:
        st.error(f'تعذّر إتمام هذا الاستقصاء: {error}')
        st.info('جرّب أحد الأمثلة الموثقة للفترة 1991–2025 أو أعد الاستعلام من API الحي لاحقاً.')
