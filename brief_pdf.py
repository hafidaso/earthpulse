"""One-page Scientific Evidence Brief PDF generator for EarthPulse (ReportLab)."""
from datetime import datetime, timezone
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from analysis import (
    VARIABLES,
    extract_grid_metadata,
    format_bound,
    format_interval,
    source_sha256,
)

W, H = A4  # 595.27 x 841.89 pt — guaranteed crisp single-page brief
MARGIN = 32.0
CONTENT_W = W - 2 * MARGIN

PAPER = colors.HexColor('#f9f7f2')
CARD = colors.HexColor('#ece8de')
BORDER = colors.HexColor('#cfc8b6')
INK = colors.HexColor('#14282d')
MUTED = colors.HexColor('#3a5055')
TEAL = colors.HexColor('#15616d')
OCHRE = colors.HexColor('#b55327')


def _wrap_px(text, max_width_pt, font='Helvetica', size=7.5):
    """Wrap text accurately to fit max_width_pt using ReportLab font metrics."""
    if not text:
        return ['—']
    words = ' '.join(str(text).split()).split(' ')
    lines = []
    curr = ''
    for word in words:
        cand = f'{curr} {word}'.strip()
        if pdfmetrics.stringWidth(cand, font, size) <= max_width_pt:
            curr = cand
        else:
            if curr:
                lines.append(curr)
            # Break long tokens (like URLs) character-by-character if wider than max_width_pt
            if pdfmetrics.stringWidth(word, font, size) <= max_width_pt:
                curr = word
            else:
                chunk = ''
                for ch in word:
                    if pdfmetrics.stringWidth(chunk + ch, font, size) <= max_width_pt:
                        chunk += ch
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = ch
                curr = chunk
    if curr:
        lines.append(curr)
    return lines or ['—']


def _draw_wrapped_px(c, text, x, y_top, max_width_pt, leading=9.6, font='Helvetica', size=7.4, color=INK, max_lines=8):
    """Draw pixel-wrapped text downward from y_top and return next baseline y."""
    c.setFont(font, size)
    c.setFillColor(color)
    lines = _wrap_px(text, max_width_pt, font=font, size=size)[:max_lines]
    y = y_top
    for ln in lines:
        c.drawString(x, y, ln)
        y -= leading
    return y


def _se_summary_fields(res, unit, rate_unit):
    """Extract SE_OLS, SE_HAC, cautious max SE, ratio, and CI strings safely from a trend() dict."""
    if res is None:
        return None
    se_ols = res.get('se_ols_decade')
    se_hac = res.get('se_hac_decade')
    se_caut = res.get('se_cautious_decade')
    ratio = res.get('hac_to_ols_se_ratio')
    if se_ols is None or se_hac is None:
        from scipy import stats
        crit = float(stats.t.ppf(0.975, max(1, res['n'] - 2)))
        se_ols = float((res['iid_ci95'][1] - res['iid_ci95'][0]) / (2.0 * crit))
        se_hac = float((res['hac_ci95'][1] - res['hac_ci95'][0]) / (2.0 * crit))
        se_caut = max(se_ols, se_hac)
        ratio = float(se_hac / se_ols) if se_ols > 0 else 1.0
    return {
        'slope': f"{format_bound(res['slope_decade'])}",
        'slope_exact': f"{res['slope_decade']:+.5f}",
        'se_ols': f"{se_ols:.4f}",
        'se_hac': f"{se_hac:.4f}",
        'se_caut': f"{se_caut:.4f}",
        'ratio': f"{ratio:.3f}x",
        'ols_ci': format_interval(res['iid_ci95'], ''),
        'hac_ci': format_interval(res['hac_ci95'], ''),
        'caut_ci': format_interval(res['ci95'], ''),
        'p_caut': f"{res['p_value']:.3g}",
        'p_ols': f"{res['iid_p']:.3g}",
        'p_hac': f"{res.get('hac_p', res['p_value']):.3g}",
        'rho1': f"{res['residual_lag1']:+.2f}",
        'lags': str(res['hac_lags']),
    }


def _box(c, x, y, w, h, fill=PAPER, stroke=BORDER, accent=None):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 4, fill=1, stroke=1)
    if accent is not None:
        c.setFillColor(accent)
        c.rect(x, y, 4, h, fill=1, stroke=0)


def build_scientific_evidence_brief_pdf(
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
    generated_utc=None,
):
    """Generate a single-page A4 Scientific Evidence Brief PDF cleanly populated from computed EarthPulse data."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle('EarthPulse Scientific Evidence Brief')
    c.setAuthor('Hafida Belayd · EarthPulse Labs, Casablanca')

    ts_utc = generated_utc or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    var_name, unit = VARIABLES[parameter]
    rate_unit = f"{unit}/dec"
    mode_labels = {
        'cautious': 'Cautious max(SE_OLS, SE_HAC)',
        'hac': 'Raw Newey–West HAC (SE_HAC)',
        'conventional': 'Conventional OLS (SE_OLS)',
    }
    mode_desc = mode_labels.get(interval_mode, interval_mode)

    # Background page
    c.setFillColor(colors.HexColor('#ffffff'))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Top editorial masthead bar
    c.setFillColor(INK)
    c.rect(0, H - 56, W, 56, fill=1, stroke=0)
    c.setFillColor(OCHRE)
    c.rect(0, H - 59, W, 3, fill=1, stroke=0)

    c.setFillColor(colors.HexColor('#d9d3c3'))
    c.setFont('Helvetica-Bold', 7.6)
    c.drawString(MARGIN, H - 19, 'EARTHPULSE · SCIENTIFIC EVIDENCE BRIEF (ONE-PAGE VERIFIABLE PASSPORT)')
    c.drawRightString(W - MARGIN, H - 19, f'GENERATED UTC: {ts_utc}')

    q_lines = _wrap_px(question, CONTENT_W, font='Times-Bold', size=14.0)[:2]
    c.setFillColor(colors.HexColor('#ffffff'))
    c.setFont('Times-Bold', 14.0 if len(q_lines) == 1 else 12.2)
    c.drawString(MARGIN, H - 38, q_lines[0])
    if len(q_lines) > 1:
        c.drawString(MARGIN, H - 51, q_lines[1])

    # Scope strip
    y = H - 76
    _box(c, MARGIN, y - 16, CONTENT_W, 25, fill=CARD, stroke=BORDER)
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 7.8)
    c.drawString(MARGIN + 8, y - 2, f'Variable: {var_name} ({parameter}, {unit})  |  Period: {start}–{end}')
    c.setFont('Helvetica', 7.5)
    c.setFillColor(MUTED)
    c.drawRightString(W - MARGIN - 8, y - 2, f'Uncertainty Assumption: {mode_desc}')
    c.drawString(MARGIN + 8, y - 12, 'Author & Project: Hafida Belayd · EarthPulse Labs, Casablanca (NASA Space Apps 2026 — Exploratory · No NASA Endorsement)')

    # Section 1: Selected Locations, Coordinates & Grid-Cell Context
    y -= 31
    c.setFillColor(TEAL)
    c.setFont('Helvetica-Bold', 8.2)
    c.drawString(MARGIN, y, '1. LOCATIONS, COORDINATES & MERRA-2 SPATIAL SCALE')
    y -= 7

    meta_a = extract_grid_metadata(loc_a, data_a, lat_a, lon_a)
    sha_a = source_sha256(loc_a, data_a)
    sites_meta = [('Location A', meta_a, sha_a, TEAL)]
    if loc_b and data_b is not None:
        meta_b = extract_grid_metadata(loc_b, data_b, lat_b, lon_b)
        sha_b = source_sha256(loc_b, data_b)
        sites_meta.append(('Location B', meta_b, sha_b, OCHRE))

    card_w = (CONTENT_W - 10) / 2 if len(sites_meta) == 2 else CONTENT_W
    box_h = 68
    for idx, (role, m, _, accent) in enumerate(sites_meta):
        bx = MARGIN + idx * (card_w + 10)
        _box(c, bx, y - box_h, card_w, box_h, fill=PAPER, stroke=BORDER, accent=accent)
        inner_w = card_w - 18
        loc_title = f"{role}: {m['location']} ({m['region_name']})"
        y_cur = _draw_wrapped_px(c, loc_title, bx + 10, y - 10, inner_w, leading=8.4, font='Helvetica-Bold', size=7.2, color=accent, max_lines=2)
        y_cur = _draw_wrapped_px(
            c,
            f"Query: {m['requested_lat']:.4f}°N, {m['requested_lon']:.4f}°E  |  NASA Point: {m['returned_lat']:.3f}°N, {m['returned_lon']:.3f}°E",
            bx + 10, y_cur - 1, inner_w, leading=8.6, font='Helvetica', size=6.9, color=INK, max_lines=1,
        )
        elev_s = f"{m['grid_elevation_m']:.1f} m" if m['grid_elevation_m'] is not None else 'N/A'
        y_cur = _draw_wrapped_px(
            c,
            f"Grid Elev: {elev_s}  |  Scale: {m['resolution_deg']} ({m['approx_km']})",
            bx + 10, y_cur - 1, inner_w, leading=8.6, font='Helvetica', size=6.9, color=INK, max_lines=1,
        )
        _draw_wrapped_px(
            c,
            'Approx. 0.5°x0.625° scale box shown on map; exact cell bounds not in POWER point JSON.',
            bx + 10, y_cur - 1, inner_w, leading=8.2, font='Helvetica-Oblique', size=6.5, color=MUTED, max_lines=2,
        )

    y -= (box_h + 12)

    # Section 2: Measured Slopes, Standard Errors & Confidence Intervals Table
    c.setFillColor(TEAL)
    c.setFont('Helvetica-Bold', 8.2)
    c.drawString(MARGIN, y, f'2. MEASURED SLOPES, OLS VS. NEWEY–WEST HAC STANDARD ERRORS & 95% INTERVALS ({rate_unit})')
    y -= 6

    table_rows = []
    if trial is not None:
        sa_r = trial.get('aligned_site_a_result') or trial['site_a'].get('result')
        sb_r = trial.get('aligned_site_b_result') or trial['site_b'].get('result')
        dr = trial.get('diff_result')
        table_rows.append((f"A: {loc_a}", trial['site_a']['n_complete'], _se_summary_fields(sa_r, unit, rate_unit), trial['site_a'].get('active_status', 'Ineligible')))
        if loc_b:
            table_rows.append((f"B: {loc_b}", trial['site_b']['n_complete'], _se_summary_fields(sb_r, unit, rate_unit), trial['site_b'].get('active_status', 'Ineligible')))
        table_rows.append(('D = B - A', trial['n_paired'], _se_summary_fields(dr, unit, rate_unit), trial.get('verdict_label', 'Ineligible')))
    elif comp is not None:
        sa, sb = comp['site_a'], comp['site_b']
        table_rows.append((f"A: {loc_a}", sa['n_complete'], _se_summary_fields(sa.get('result'), unit, rate_unit), sa.get('active_status', 'Ineligible')))
        if loc_b:
            table_rows.append((f"B: {loc_b}", sb['n_complete'], _se_summary_fields(sb.get('result'), unit, rate_unit), sb.get('active_status', 'Ineligible')))
    elif single_site is not None:
        table_rows.append((f"{loc_a}", single_site['n_complete'], _se_summary_fields(single_site.get('result'), unit, rate_unit), single_site.get('active_status', 'Ineligible')))

    hdr_h = 18
    row_h = 31
    tbl_h = hdr_h + len(table_rows) * row_h
    _box(c, MARGIN, y - tbl_h, CONTENT_W, tbl_h, fill=PAPER, stroke=BORDER)
    c.setFillColor(CARD)
    c.rect(MARGIN, y - hdr_h, CONTENT_W, hdr_h, fill=1, stroke=1)

    # Spacious, non-overlapping offsets across CONTENT_W = 531.27 pt
    cols = [MARGIN + 5, MARGIN + 82, MARGIN + 102, MARGIN + 150, MARGIN + 194, MARGIN + 248, MARGIN + 292, MARGIN + 432]
    headers = ['Series', 'n', 'Slope', 'SE_OLS', 'SE_HAC (raw)', 'HAC/OLS', 'Cautious / OLS / HAC 95% CI', 'Zero-Slope Verdict']
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 6.8)
    for cx, htxt in zip(cols, headers):
        c.drawString(cx, y - 12, htxt)

    ry = y - hdr_h
    for ridx, (label, n_yr, sef, status) in enumerate(table_rows):
        ry_bot = ry - row_h
        if ridx % 2 == 1:
            c.setFillColor(colors.HexColor('#f3f0e7'))
            c.rect(MARGIN + 1, ry_bot, CONTENT_W - 2, row_h, fill=1, stroke=0)
        c.setStrokeColor(BORDER)
        c.line(MARGIN, ry_bot, W - MARGIN, ry_bot)
        _draw_wrapped_px(c, label, cols[0], ry - 10.5, 74, leading=8.5, font='Helvetica-Bold', size=6.9, color=INK, max_lines=2)
        c.setFillColor(INK)
        c.setFont('Helvetica', 6.9)
        c.drawString(cols[1], ry - 10.5, str(n_yr))
        if sef is None:
            c.setFillColor(MUTED)
            c.drawString(cols[2], ry - 10.5, 'Inference withheld (<30 consecutive complete years or constant D)')
            _draw_wrapped_px(c, status, cols[7], ry - 10, (W - MARGIN) - cols[7] - 4, leading=8.2, font='Helvetica-Bold', size=6.5, color=INK, max_lines=2)
        else:
            c.setFont('Helvetica-Bold', 6.9)
            c.drawString(cols[2], ry - 10.5, sef['slope'])
            c.setFont('Helvetica', 6.8)
            c.drawString(cols[3], ry - 10.5, sef['se_ols'])
            c.drawString(cols[4], ry - 10.5, f"{sef['se_hac']} ({sef['lags']}L)")
            c.drawString(cols[5], ry - 10.5, sef['ratio'])
            c.setFont('Helvetica-Bold', 6.4)
            c.drawString(cols[6], ry - 9.5, f"Caut: {sef['caut_ci']} (p={sef['p_caut']})")
            c.setFont('Helvetica', 6.1)
            c.setFillColor(MUTED)
            c.drawString(cols[6], ry - 18.0, f"OLS:  {sef['ols_ci']} (p={sef['p_ols']})")
            c.drawString(cols[6], ry - 26.5, f"HAC:  {sef['hac_ci']} (p={sef['p_hac']})")
            vcol = OCHRE if 'Excludes' in status or 'positive' in status.lower() else (TEAL if 'negative' in status.lower() else INK)
            _draw_wrapped_px(c, f"{status} (r1={sef['rho1']})", cols[7], ry - 9.5, (W - MARGIN) - cols[7] - 4, leading=8.0, font='Helvetica-Bold', size=6.3, color=vcol, max_lines=3)
        ry = ry_bot

    c.setFillColor(MUTED)
    c.setFont('Helvetica-Oblique', 6.9)
    c.drawString(MARGIN, ry - 10, 'Note: SE_HAC / SE_OLS measures relative change in estimated standard error only; it is NOT a Type-I error probability or false-positive rate.')

    y = ry - 22

    # Section 3: Derived Verdict & Statistical Comparison Findings
    c.setFillColor(TEAL)
    c.setFont('Helvetica-Bold', 8.2)
    c.drawString(MARGIN, y, '3. DERIVED STATISTICAL VERDICT & INTERPRETATION (COMPUTED FROM SELECTED SERIES)')
    y -= 6

    if trial is not None:
        v_head = trial['verdict_label']
        v_body = f"{trial['interpretation']} {trial['overlap_insight']}"
        if trial.get('eligible') and trial.get('slope_diff_identity_delta') is not None:
            v_body += (
                f" OLS identity |slope(B-A) - (slope(B)-slope(A))| = {trial['slope_diff_identity_delta']:.2e}; "
                f"cross-site residual r = {trial.get('residual_correlation', 0.0):+.2f}."
            )
        v_accent = OCHRE if trial['verdict_code'] == 'positive_difference' else (TEAL if trial['verdict_code'] == 'negative_difference' else MUTED)
    elif comp is not None:
        v_head = comp['headline']
        v_body = f"{comp['second_line']} {comp['overlap_note']}"
        v_accent = TEAL
    elif single_site is not None:
        v_head = single_site['active_status']
        if single_site['eligible']:
            r = single_site['result']
            v_body = (
                f"Fitted decadal slope for {loc_a} ({r['start']}–{r['end']}, n={r['n']}): {format_bound(r['slope_decade'])} {rate_unit}; "
                f"cautious 95% CI {format_interval(r['ci95'], rate_unit)} (p = {r['p_value']:.4g})."
            )
        else:
            v_body = single_site.get('error') or 'Fewer than 30 consecutive complete years.'
        v_accent = OCHRE if single_site.get('active_excludes_zero') else TEAL
    else:
        v_head = 'Summary unavailable'
        v_body = 'No computed analysis object provided.'
        v_accent = MUTED

    vbox_h = 80
    _box(c, MARGIN, y - vbox_h, CONTENT_W, vbox_h, fill=CARD, stroke=BORDER, accent=v_accent)
    c.setFillColor(INK)
    c.setFont('Times-Bold', 10.2)
    c.drawString(MARGIN + 10, y - 14, _wrap_px(v_head, CONTENT_W - 20, 'Times-Bold', 10.2)[0])
    _draw_wrapped_px(c, v_body, MARGIN + 10, y - 27, CONTENT_W - 20, leading=9.3, font='Helvetica', size=7.2, color=INK, max_lines=5)
    y -= (vbox_h + 12)

    # Section 4: Methodology & Limitations (2 Columns)
    c.setFillColor(TEAL)
    c.setFont('Helvetica-Bold', 8.2)
    c.drawString(MARGIN, y, '4. METHODOLOGY & SCIENTIFIC LIMITATIONS')
    y -= 6

    col_w = (CONTENT_W - 10) / 2
    ml_h = 122
    _box(c, MARGIN, y - ml_h, col_w, ml_h, fill=PAPER, stroke=BORDER)
    _box(c, MARGIN + col_w + 10, y - ml_h, col_w, ml_h, fill=PAPER, stroke=BORDER)

    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 7.8)
    c.drawString(MARGIN + 8, y - 13, 'Data Processing & Uncertainty Methodology')
    meth_text = (
        '1) Require all 12 valid calendar months/year from NASA POWER; ignore month 13 and reject fill -999. '
        '2) Weight T2M by days/month (leap years included); sum PRECTOTCORR totals (mm/yr). '
        '3) Enforce >=30 consecutive complete years without interpolation; pair D(year) = B - A strictly on shared complete years. '
        '4) Fit OLS on centered year; compute Newey–West HAC (Bartlett kernel, finite-sample t, L = floor(4*(n/100)^(2/9)) lags); apply cautious max(SE_OLS, SE_HAC) safeguard alongside raw HAC and OLS.'
    )
    _draw_wrapped_px(c, meth_text, MARGIN + 8, y - 24, col_w - 16, leading=9.1, font='Helvetica', size=6.9, color=MUTED, max_lines=10)

    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 7.8)
    c.drawString(MARGIN + col_w + 18, y - 13, 'Key Scientific Limitations & Guardrails')
    lim_text = (
        '• Spatial Resolution: MERRA-2 0.5° × 0.625° regional averages smooth coastal breezes & terrain gradients; no local station downscaling or elevation correction is applied. Exact grid vertices are absent in point JSON. '
        '• Small-Sample Inference: With n = 30–35 years, HAC variance estimates carry sampling noise; overlapping intervals never test B - A differences; inconclusive intervals mean zero is not excluded, NOT equal trends. '
        '• Multiplicity & Causation: Exploratory comparisons are unadjusted; linear slopes do not prove physical causation.'
    )
    _draw_wrapped_px(c, lim_text, MARGIN + col_w + 18, y - 24, col_w - 16, leading=9.1, font='Helvetica', size=6.9, color=MUTED, max_lines=10)

    y -= (ml_h + 12)

    # Section 5: Data Source Provenance & Exact SHA-256 Checksums
    c.setFillColor(TEAL)
    c.setFont('Helvetica-Bold', 8.2)
    c.drawString(MARGIN, y, '5. NASA DATA SOURCE PROVENANCE & SHA-256 INTEGRITY HASHES')
    y -= 6

    prov_h = max(108.0, y - 30.0)
    _box(c, MARGIN, 30, CONTENT_W, prov_h, fill=CARD, stroke=BORDER)
    py = y - 11
    hdr = data_a.get('header', {})
    src_line = f"Source: {hdr.get('title', 'NASA/POWER MERRA-2')} (API {hdr.get('api', {}).get('version', 'v2.10.0')}, {', '.join(hdr.get('sources', ['MERRA2']))}) · https://power.larc.nasa.gov/docs/services/api/temporal/monthly/"
    py = _draw_wrapped_px(c, src_line, MARGIN + 8, py, CONTENT_W - 16, leading=8.4, font='Helvetica-Bold', size=6.8, color=INK, max_lines=2)
    py -= 2
    for role, m, sha_info, _ in sites_meta:
        url = m.get('request_url') or 'Bundled NASA snapshot'
        ret_t = m.get('retrieved_utc') or 'N/A'
        py = _draw_wrapped_px(
            c,
            f"{role} ({m['location']}) · Retrieved UTC: {ret_t} · {sha_info['scope']}",
            MARGIN + 8, py, CONTENT_W - 16, leading=8.4, font='Helvetica-Bold', size=6.7, color=INK, max_lines=1,
        )
        py = _draw_wrapped_px(
            c,
            f"SHA-256: {sha_info['sha256']}",
            MARGIN + 8, py, CONTENT_W - 16, leading=8.4, font='Courier-Bold', size=6.7, color=TEAL, max_lines=1,
        )
        py = _draw_wrapped_px(
            c,
            f"API URL: {url}",
            MARGIN + 8, py, CONTENT_W - 16, leading=7.8, font='Courier', size=6.2, color=MUTED, max_lines=3,
        )
        py -= 3

    # Clean non-overlapping Page Footer
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 6.9)
    c.drawString(MARGIN, 17, 'EarthPulse Scientific Evidence Brief · Hafida Belayd, EarthPulse Labs, Casablanca (No NASA Endorsement)')
    c.drawRightString(W - MARGIN, 17, f'Page 1 of 1 · UTC {ts_utc}')

    c.showPage()
    c.save()
    return buf.getvalue()
