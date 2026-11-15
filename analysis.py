"""EarthPulse analysis. AI-assisted implementation by OpenAI Codex; V2 comparison extensions assisted by Google Gemini (Argon). NASA data unaltered."""
import calendar
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import requests
from scipy import stats
import statsmodels.api as sm

LOCATIONS = {
    'Casablanca': (33.5731, -7.5898),
    'Rabat': (34.0209, -6.8416),
    'Marrakech': (31.6295, -7.9811),
    'Ouarzazate': (30.9335, -6.9370),
}
API = 'https://power.larc.nasa.gov/api/temporal/monthly/point'
VARIABLES = {
    'T2M': ('Temperature at 2 metres', '°C'),
    'PRECTOTCORR': ('Annual precipitation', 'mm/year'),
}


def fetch_power(lat, lon, start=1991, end=2025):
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('Coordinates are outside valid ranges.')
    if not (1981 <= start <= end < datetime.now(timezone.utc).year):
        raise ValueError('Choose completed calendar years from 1981 onward.')
    params = dict(
        parameters='T2M,PRECTOTCORR',
        community='AG',
        longitude=lon,
        latitude=lat,
        format='JSON',
        start=start,
        end=end,
    )
    response = requests.get(API, params=params, timeout=90)
    response.raise_for_status()
    data = response.json()
    if 'parameter' not in data.get('properties', {}):
        raise ValueError('NASA did not return the expected parameter data.')
    data['_earthpulse'] = {
        'request_url': response.url,
        'retrieved_utc': datetime.now(timezone.utc).isoformat(),
        'requested_latitude': lat,
        'requested_longitude': lon,
        'start': start,
        'end': end,
        'data_origin': 'NASA POWER API; no synthetic measurements',
    }
    return data


def annual_series(data, parameter, start, end):
    expected = {'T2M': 'C', 'PRECTOTCORR': 'mm/day'}
    if data['parameters'][parameter]['units'] != expected[parameter]:
        raise ValueError('Unexpected source units. Analysis stopped to prevent invalid conversion.')
    fill = data['header']['fill_value']
    raw = data['properties']['parameter'][parameter]
    rows, omitted = [], []
    for year in range(start, end + 1):
        vals = np.array([raw.get(f'{year}{month:02d}', np.nan) for month in range(1, 13)], dtype=float)
        if not np.all(np.isfinite(vals)) or np.any(vals == fill) or (parameter == 'PRECTOTCORR' and np.any(vals < 0)):
            omitted.append(year)
            continue
        days = np.array([calendar.monthrange(year, month)[1] for month in range(1, 13)])
        value = np.sum(vals * days)
        if parameter == 'T2M':
            value /= days.sum()
        rows.append({'year': year, 'value': float(value)})
    return pd.DataFrame(rows, columns=['year', 'value']), omitted


def trend(frame):
    x = frame['year'].to_numpy(dtype=float)
    y = frame['value'].to_numpy(dtype=float)
    if len(x) < 30:
        raise ValueError('At least 30 complete years are required for this exploratory trend analysis.')
    if not np.all(np.isfinite(y)) or not np.all(np.diff(x) == 1):
        raise ValueError('Trend inference requires consecutive, complete annual values. Select an uninterrupted period.')
    if np.ptp(y) == 0:
        raise ValueError('This series is constant; inferential trend statistics are undefined.')
    X = sm.add_constant(x - x.mean())
    ols = sm.OLS(y, X).fit()
    lag = max(1, int(np.floor(4 * (len(x) / 100) ** (2 / 9))))
    robust = ols.get_robustcov_results(cov_type='HAC', maxlags=lag, use_correction=True, use_t=True)
    # Report both intervals, and use the wider interval as a cautious screening rule.
    ci = robust.conf_int(alpha=0.05)[1] * 10
    iid_ci = ols.conf_int(alpha=0.05)[1] * 10
    se = max(float(robust.bse[1]), float(ols.bse[1]))
    crit = stats.t.ppf(0.975, len(x) - 2)
    slope = float(ols.params[1])
    wide_ci = [(slope - crit * se) * 10, (slope + crit * se) * 10]
    p = float(2 * stats.t.sf(abs(slope / se), len(x) - 2)) if se > 0 else 0.0
    residual = ols.resid
    rho = float(np.corrcoef(residual[:-1], residual[1:])[0, 1]) if np.std(residual) > 1e-12 else 0.0
    return dict(
        n=len(x),
        slope_decade=slope * 10,
        ci95=wide_ci,
        p_value=p,
        hac_ci95=ci.tolist(),
        hac_p=float(robust.pvalues[1]),
        iid_ci95=iid_ci.tolist(),
        iid_p=float(ols.pvalues[1]),
        hac_lags=lag,
        residual_lag1=rho,
        r_squared=float(ols.rsquared),
        fitted=ols.fittedvalues.tolist(),
        mean=float(y.mean()),
        start=int(x[0]),
        end=int(x[-1]),
    )


def excludes_zero(ci):
    """Classify whether an interval strictly excludes zero using full numeric precision."""
    low, high = float(ci[0]), float(ci[1])
    return bool(low > 0.0 or high < 0.0)


def intervals_overlap(ci_a, ci_b):
    """Return True when two intervals share at least one point."""
    return bool(max(float(ci_a[0]), float(ci_b[0])) <= min(float(ci_a[1]), float(ci_b[1])))


def format_bound(value, decimals=2):
    """Format a signed estimate or bound, expanding precision near zero to avoid contradictory +0.00/-0.00 labels."""
    val = float(value)
    if val == 0.0:
        return f"0.{'0' * decimals}"
    threshold = 10 ** (-decimals)
    if abs(val) < threshold:
        extra_decimals = min(6, max(decimals + 2, int(np.ceil(-np.log10(abs(val)))) + 1))
        return f"{val:+.{extra_decimals}f}"
    return f"{val:+.{decimals}f}"


def format_interval(ci, unit='', decimals=2):
    """Format a two-sided interval [low, high] with near-zero precision protection."""
    low_str = format_bound(ci[0], decimals=decimals)
    high_str = format_bound(ci[1], decimals=decimals)
    suffix = f" {unit}" if unit else ""
    return f"{low_str} to {high_str}{suffix}"


def evaluate_site(location, data, parameter, start, end, interval_mode='cautious'):
    """Aggregate annual series and evaluate trend eligibility and interval classifications for one site."""
    frame, omitted = annual_series(data, parameter, start, end)
    site = {
        'location': location,
        'frame': frame,
        'omitted': omitted,
        'n_complete': int(len(frame)),
        'eligible': False,
        'error': None,
        'result': None,
        'cautious_excludes_zero': False,
        'iid_excludes_zero': False,
        'active_excludes_zero': False,
        'time_dependence_changes_verdict': False,
        'cautious_status': 'Ineligible for inference',
        'iid_status': 'Ineligible for inference',
        'active_status': 'Ineligible for inference',
    }
    try:
        res = trend(frame)
    except ValueError as exc:
        site['error'] = str(exc)
        return site

    cautious_ex = excludes_zero(res['ci95'])
    iid_ex = excludes_zero(res['iid_ci95'])
    use_iid = interval_mode == 'conventional'
    active_ci = res['iid_ci95'] if use_iid else res['ci95']
    active_p = res['iid_p'] if use_iid else res['p_value']
    active_ex = iid_ex if use_iid else cautious_ex

    direction = 'positive' if res['slope_decade'] > 0 else 'negative'
    cautious_status = f"Excludes zero ({direction} trend)" if cautious_ex else "Crosses zero (inconclusive)"
    iid_status = f"Excludes zero ({direction} trend)" if iid_ex else "Crosses zero (inconclusive)"

    site.update({
        'eligible': True,
        'result': res,
        'cautious_excludes_zero': cautious_ex,
        'iid_excludes_zero': iid_ex,
        'active_ci': active_ci,
        'active_p': active_p,
        'active_excludes_zero': active_ex,
        'time_dependence_changes_verdict': bool(cautious_ex != iid_ex),
        'cautious_status': cautious_status,
        'iid_status': iid_status,
        'active_status': iid_status if use_iid else cautious_status,
    })
    return site


def compare_locations(loc_a, data_a, loc_b, data_b, parameter='T2M', start=1991, end=2025, interval_mode='cautious'):
    """Compare two locations and derive the headline, plain-English verdict, and methodological notes from the data."""
    var_name, unit = VARIABLES[parameter]
    rate_unit = f"{unit}/decade"
    site_a = evaluate_site(loc_a, data_a, parameter, start, end, interval_mode=interval_mode)
    site_b = evaluate_site(loc_b, data_b, parameter, start, end, interval_mode=interval_mode)
    both_eligible = bool(site_a['eligible'] and site_b['eligible'])
    same_location = bool(loc_a == loc_b)

    overlap_note = (
        "Each 95% interval tests that location’s own slope against zero. "
        "Do not use interval overlap between two locations to infer whether their slopes differ from each other; "
        "a formal between-site hypothesis test is out of scope."
    )

    if not both_eligible:
        reasons = []
        for s in (site_a, site_b):
            if not s['eligible']:
                omitted_info = f" (omitted years: {', '.join(map(str, s['omitted']))})" if s['omitted'] else ""
                reasons.append(f"{s['location']} has {s['n_complete']} complete annual values in {start}–{end}{omitted_info}: {s['error']}")
        headline = "Trend inference unavailable for the selected period."
        second_line = " ".join(reasons) + " Observed annual estimates are shown below without fitted trend lines."
        time_dep_note = (
            "Trend intervals (both conventional OLS and Newey–West HAC screening) require at least 30 consecutive, "
            "complete annual values without gaps."
        )
        return {
            'parameter': parameter,
            'variable_name': var_name,
            'unit': unit,
            'rate_unit': rate_unit,
            'start': start,
            'end': end,
            'interval_mode': interval_mode,
            'site_a': site_a,
            'site_b': site_b,
            'both_eligible': False,
            'same_location': same_location,
            'intervals_overlap': None,
            'headline': headline,
            'second_line': second_line,
            'time_dependence_note': time_dep_note,
            'overlap_note': overlap_note,
        }

    ra, rb = site_a['result'], site_b['result']
    overlap = intervals_overlap(site_a['active_ci'], site_b['active_ci'])

    if overlap:
        overlap_note = (
            f"The exploratory 95% intervals for {loc_a} and {loc_b} overlap. "
            "Each interval tests only that site’s own slope against zero; interval overlap does not test whether "
            "the two slopes differ from each other (a between-site hypothesis test is out of scope)."
        )

    # Derive headline and plain-English second line from full-precision results
    cautious_diff = site_a['cautious_excludes_zero'] != site_b['cautious_excludes_zero']
    active_diff = site_a['active_excludes_zero'] != site_b['active_excludes_zero']
    both_warming = (parameter == 'T2M') and (ra['slope_decade'] > 0) and (rb['slope_decade'] > 0)

    if same_location:
        headline = f"Same grid cell selected twice ({loc_a})."
        second_line = (
            f"Choose two different Moroccan locations to compare their {var_name.lower()} trajectories and uncertainty intervals across {start}–{end}."
        )
    elif both_warming and (cautious_diff or active_diff):
        headline = "Two warming estimates. Different confidence in the trend."
        clear_site = site_b if site_b['cautious_excludes_zero'] else site_a
        uncertain_site = site_a if clear_site is site_b else site_b
        rc, ru = clear_site['result'], uncertain_site['result']
        if interval_mode == 'conventional' and uncertain_site['iid_excludes_zero']:
            second_line = (
                f"Across {start}–{end} ({rc['n']} complete years), {clear_site['location']} warms by an estimated "
                f"{format_bound(rc['slope_decade'])} {rate_unit} (conventional 95% interval {format_interval(rc['iid_ci95'], rate_unit)}) "
                f"and {uncertain_site['location']} by {format_bound(ru['slope_decade'])} {rate_unit} "
                f"(conventional {format_interval(ru['iid_ci95'], rate_unit)}), but accounting for year-to-year residual dependence "
                f"widens {uncertain_site['location']}’s cautious 95% interval ({format_interval(ru['ci95'], rate_unit)}) across zero."
            )
        else:
            second_line = (
                f"Across {start}–{end} ({rc['n']} complete years), {clear_site['location']} warms by an estimated "
                f"{format_bound(rc['slope_decade'])} {rate_unit} (cautious 95% interval {format_interval(rc['ci95'], rate_unit)}, "
                f"excluding zero), whereas {uncertain_site['location']}’s {format_bound(ru['slope_decade'])} {rate_unit} estimate "
                f"({format_interval(ru['ci95'], rate_unit)}) crosses zero once residual time dependence is accounted for."
            )
    elif parameter == 'T2M' and site_a['active_excludes_zero'] and site_b['active_excludes_zero']:
        headline = "Two warming estimates. Both exploratory intervals exclude zero."
        second_line = (
            f"Across {start}–{end} ({ra['n']} complete years), {loc_a} changes by an estimated "
            f"{format_bound(ra['slope_decade'])} {rate_unit} (95% interval {format_interval(site_a['active_ci'], rate_unit)}) "
            f"and {loc_b} by {format_bound(rb['slope_decade'])} {rate_unit} ({format_interval(site_b['active_ci'], rate_unit)}); "
            f"both intervals lie entirely above zero."
        )
    elif parameter == 'T2M' and not site_a['active_excludes_zero'] and not site_b['active_excludes_zero']:
        headline = "Two temperature estimates. Neither interval excludes zero."
        second_line = (
            f"Across {start}–{end} ({ra['n']} complete years), {loc_a} estimates {format_bound(ra['slope_decade'])} {rate_unit} "
            f"(95% interval {format_interval(site_a['active_ci'], rate_unit)}) and {loc_b} estimates "
            f"{format_bound(rb['slope_decade'])} {rate_unit} ({format_interval(site_b['active_ci'], rate_unit)}); "
            f"both exploratory 95% intervals cross zero."
        )
    elif parameter == 'PRECTOTCORR' and not site_a['active_excludes_zero'] and not site_b['active_excludes_zero']:
        headline = "Two precipitation estimates. Neither establishes a linear trend."
        second_line = (
            f"Across {start}–{end} ({ra['n']} complete years), {loc_a} estimates {format_bound(ra['slope_decade'])} {rate_unit} "
            f"(95% interval {format_interval(site_a['active_ci'], rate_unit)}) and {loc_b} estimates "
            f"{format_bound(rb['slope_decade'])} {rate_unit} ({format_interval(site_b['active_ci'], rate_unit)}); "
            f"both exploratory 95% intervals span zero amid strong interannual rainfall variability."
        )
    elif active_diff or cautious_diff:
        var_word = "temperature" if parameter == 'T2M' else "precipitation"
        headline = f"Two {var_word} estimates. Different confidence in the trend."
        second_line = (
            f"Across {start}–{end} ({ra['n']} complete years), {loc_a} estimates {format_bound(ra['slope_decade'])} {rate_unit} "
            f"(95% interval {format_interval(site_a['active_ci'], rate_unit)}) while {loc_b} estimates "
            f"{format_bound(rb['slope_decade'])} {rate_unit} ({format_interval(site_b['active_ci'], rate_unit)})."
        )
    else:
        headline = "Two precipitation estimates. Both exploratory intervals exclude zero."
        second_line = (
            f"Across {start}–{end} ({ra['n']} complete years), {loc_a} changes by {format_bound(ra['slope_decade'])} {rate_unit} "
            f"({format_interval(site_a['active_ci'], rate_unit)}) and {loc_b} by {format_bound(rb['slope_decade'])} {rate_unit} "
            f"({format_interval(site_b['active_ci'], rate_unit)})."
        )

    # Build time-dependence explanation
    flips = [s for s in (site_a, site_b) if s['time_dependence_changes_verdict']]
    if flips:
        s_flip = flips[0]
        r_flip = s_flip['result']
        other = site_b if s_flip is site_a else site_a
        r_other = other['result']
        time_dep_note = (
            f"Accounting for residual time dependence changes the strength of the evidence for {s_flip['location']}. "
            f"Ordinary OLS assumes independent annual residuals and yields a narrower 95% interval of "
            f"{format_interval(r_flip['iid_ci95'], rate_unit)} (p = {r_flip['iid_p']:.4g}, excluding zero). "
            f"Because {s_flip['location']}’s residuals exhibit positive lag-1 autocorrelation (ρ₁ = {r_flip['residual_lag1']:+.2f}), "
            f"Newey–West HAC standard errors ({r_flip['hac_lags']} annual lags) widen the cautious screening interval to "
            f"{format_interval(r_flip['ci95'], rate_unit)} (p = {r_flip['p_value']:.4g}), which crosses zero. "
            f"For {other['location']} (ρ₁ = {r_other['residual_lag1']:+.2f}), both the conventional interval "
            f"({format_interval(r_other['iid_ci95'], rate_unit)}) and cautious interval ({format_interval(r_other['ci95'], rate_unit)}) "
            f"{'exclude' if other['cautious_excludes_zero'] else 'include'} zero."
        )
    else:
        time_dep_note = (
            f"We report both conventional OLS intervals and cautious screening intervals using the larger of OLS and "
            f"Newey–West HAC standard errors ({ra['hac_lags']} annual lags). "
            f"For {loc_a} (residual lag-1 ρ₁ = {ra['residual_lag1']:+.2f}), the conventional 95% interval is "
            f"{format_interval(ra['iid_ci95'], rate_unit)} vs. cautious {format_interval(ra['ci95'], rate_unit)}. "
            f"For {loc_b} (ρ₁ = {rb['residual_lag1']:+.2f}), the conventional 95% interval is "
            f"{format_interval(rb['iid_ci95'], rate_unit)} vs. cautious {format_interval(rb['ci95'], rate_unit)}. "
            f"Accounting for short-range residual dependence adjusts interval width without flipping the zero-crossing classification for this pair."
        )

    return {
        'parameter': parameter,
        'variable_name': var_name,
        'unit': unit,
        'rate_unit': rate_unit,
        'start': start,
        'end': end,
        'interval_mode': interval_mode,
        'site_a': site_a,
        'site_b': site_b,
        'both_eligible': True,
        'same_location': same_location,
        'intervals_overlap': overlap,
        'headline': headline,
        'second_line': second_line,
        'time_dependence_note': time_dep_note,
        'overlap_note': overlap_note,
    }
