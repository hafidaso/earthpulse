import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from analysis import (
    LOCATIONS,
    annual_series,
    climate_trial,
    compare_locations,
    excludes_zero,
    fetch_power,
    format_bound,
    format_interval,
    intervals_overlap,
    paired_difference_series,
    trend,
)


def source(values, p='T2M', unit='C'):
    return {'header': {'fill_value': -999}, 'parameters': {p: {'units': unit}}, 'properties': {'parameter': {p: values}}}


def test_day_weighted_temperature_and_ignore_annual_field():
    values = {f'2000{m:02d}': float(m) for m in range(1, 13)}
    values['200013'] = 9999
    frame, omitted = annual_series(source(values), 'T2M', 2000, 2000)
    days = np.array([31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    assert frame.value.iloc[0] == pytest.approx(np.dot(np.arange(1, 13), days) / 366)
    assert omitted == []


def test_precipitation_leap_year_conversion():
    values = {f'{y}{m:02d}': 2.0 for y in [2000, 2001] for m in range(1, 13)}
    f, _ = annual_series(source(values, 'PRECTOTCORR', 'mm/day'), 'PRECTOTCORR', 2000, 2001)
    assert f.value.tolist() == [732.0, 730.0]


@pytest.mark.parametrize('bad', [-999, np.nan])
def test_missing_month_excludes_year(bad):
    values = {f'2000{m:02d}': 1.0 for m in range(1, 13)}
    values['200004'] = bad
    f, o = annual_series(source(values), 'T2M', 2000, 2000)
    assert f.empty and o == [2000]


def test_wrong_units_rejected():
    with pytest.raises(ValueError):
        annual_series(source({}, unit='K'), 'T2M', 2000, 2001)


def test_known_linear_trend():
    x = np.arange(1991, 2026)
    y = 12 + 0.04 * (x - 1991)
    r = trend(pd.DataFrame({'year': x, 'value': y}))
    assert r['slope_decade'] == pytest.approx(0.4)
    assert r['ci95'][0] <= 0.4000000001 and r['ci95'][1] >= 0.3999999999


def test_independent_reference_hac():
    import statsmodels.api as sm
    x = np.arange(1981, 2026)
    rng = np.random.default_rng(37)
    noise = np.zeros(len(x))
    for i in range(1, len(x)):
        noise[i] = 0.6 * noise[i - 1] + rng.normal()
    y = 0.025 * (x - x.mean()) + noise
    r = trend(pd.DataFrame({'year': x, 'value': y}))
    ref = sm.OLS(y, sm.add_constant(x - x.mean())).fit(
        cov_type='HAC', cov_kwds={'maxlags': r['hac_lags'], 'use_correction': True}, use_t=True
    )
    assert r['hac_ci95'] == pytest.approx(ref.conf_int()[1] * 10)
    assert r['ci95'][1] - r['ci95'][0] >= r['hac_ci95'][1] - r['hac_ci95'][0] - 1e-10


def test_short_and_gapped_periods_rejected():
    for x in [np.arange(2000, 2020), np.r_[np.arange(1981, 2000), np.arange(2001, 2026)]]:
        with pytest.raises(ValueError):
            trend(pd.DataFrame({'year': x, 'value': np.arange(len(x))}))


def test_invalid_coordinates():
    with pytest.raises(ValueError):
        fetch_power(91, 0)


def _load_snapshot(name):
    return json.loads((Path(__file__).parent / 'data' / f'{name.lower()}.json').read_text())


def test_comparison_interpretation_casablanca_vs_marrakech():
    casa = _load_snapshot('Casablanca')
    marr = _load_snapshot('Marrakech')
    comp = compare_locations('Casablanca', casa, 'Marrakech', marr, parameter='T2M', start=1991, end=2025)

    assert comp['both_eligible'] is True
    assert comp['headline'] == 'Two warming estimates. Different confidence in the trend.'

    ra = comp['site_a']['result']
    rb = comp['site_b']['result']
    assert ra['slope_decade'] == pytest.approx(0.21918, abs=1e-5)
    assert ra['ci95'] == pytest.approx([-0.02648, 0.46484], abs=1e-5)
    assert rb['slope_decade'] == pytest.approx(0.48224, abs=1e-5)
    assert rb['ci95'] == pytest.approx([0.23036, 0.73413], abs=1e-5)

    # Casablanca conventional interval excludes zero while cautious HAC interval crosses zero
    assert comp['site_a']['iid_excludes_zero'] is True
    assert comp['site_a']['cautious_excludes_zero'] is False
    assert comp['site_a']['time_dependence_changes_verdict'] is True

    # Marrakech excludes zero under both intervals
    assert comp['site_b']['iid_excludes_zero'] is True
    assert comp['site_b']['cautious_excludes_zero'] is True
    assert comp['site_b']['time_dependence_changes_verdict'] is False

    # Overlapping intervals do not imply a formal between-site slope test
    assert comp['intervals_overlap'] is True
    assert 'do not' in comp['overlap_note'].lower() or 'does not' in comp['overlap_note'].lower()
    assert 'out of scope' in comp['overlap_note'].lower()
    assert 'residual' in comp['time_dependence_note'].lower()


def test_comparison_precipitation_and_near_zero_precision():
    snapshots = {loc: _load_snapshot(loc) for loc in LOCATIONS}

    # All four bundled precipitation intervals include zero
    for loc, data in snapshots.items():
        frame, _ = annual_series(data, 'PRECTOTCORR', 1991, 2025)
        res = trend(frame)
        assert excludes_zero(res['ci95']) is False

    precip_comp = compare_locations(
        'Casablanca', snapshots['Casablanca'], 'Marrakech', snapshots['Marrakech'], parameter='PRECTOTCORR', start=1991, end=2025
    )
    assert precip_comp['headline'] == 'Two precipitation estimates. Neither establishes a linear trend.'
    assert precip_comp['site_a']['cautious_excludes_zero'] is False
    assert precip_comp['site_b']['cautious_excludes_zero'] is False

    # Rabat T2M has a positive lower bound very close to zero (+0.000191...); must classify with full precision and avoid +0.00 display
    rabat_comp = compare_locations(
        'Rabat', snapshots['Rabat'], 'Marrakech', snapshots['Marrakech'], parameter='T2M', start=1991, end=2025
    )
    rabat_ci = rabat_comp['site_a']['result']['ci95']
    assert rabat_comp['site_a']['cautious_excludes_zero'] is True
    formatted_low = format_bound(rabat_ci[0], decimals=2)
    assert formatted_low != '+0.00'
    assert '+0.00019' in format_interval(rabat_ci, '°C/decade')


def test_comparison_ineligible_short_period():
    casa = _load_snapshot('Casablanca')
    marr = _load_snapshot('Marrakech')
    comp = compare_locations('Casablanca', casa, 'Marrakech', marr, parameter='T2M', start=2000, end=2025)
    assert comp['both_eligible'] is False
    assert comp['site_a']['eligible'] is False
    assert comp['site_b']['eligible'] is False
    assert '30' in comp['second_line']


def test_paired_year_alignment_and_missing_year_handling():
    # A misses 2003 (-999 fill), B misses 2010 (NaN); paired frame must drop both years without interpolation
    vals_a = {f'{y}{m:02d}': 15.0 + 0.02 * (y - 1990) for y in range(1990, 2025) for m in range(1, 13)}
    vals_b = {f'{y}{m:02d}': 16.0 + 0.05 * (y - 1990) for y in range(1990, 2025) for m in range(1, 13)}
    vals_a['200305'] = -999
    vals_b['201007'] = np.nan

    data_a = source(vals_a)
    data_b = source(vals_b)

    fa, omitted_a = annual_series(data_a, 'T2M', 1990, 2024)
    fb, omitted_b = annual_series(data_b, 'T2M', 1990, 2024)
    assert omitted_a == [2003]
    assert omitted_b == [2010]

    paired = paired_difference_series(fa, fb, start=1990, end=2024)
    assert paired['years_a_only'] == [2010]
    assert paired['years_b_only'] == [2003]
    assert paired['missing_paired'] == [2003, 2010]
    assert len(paired['diff_frame']) == 33
    assert set(paired['diff_frame']['year']).isdisjoint({2003, 2010})
    assert np.allclose(paired['diff_frame']['value'], 1.0 + 0.03 * (paired['diff_frame']['year'] - 1990))

    # Gaps breaking continuity inside [1990, 2024] must withhold paired linear trend inference
    trial = climate_trial('SiteA', data_a, 'SiteB', data_b, parameter='T2M', start=1990, end=2024)
    assert trial['eligible'] is False
    assert trial['verdict_code'] == 'ineligible'
    assert trial['n_paired'] == 33
    assert trial['diff_result'] is None


def test_paired_difference_slope_identity_and_hac_estimation():
    import statsmodels.api as sm

    casa = _load_snapshot('Casablanca')
    marr = _load_snapshot('Marrakech')
    trial = climate_trial('Casablanca', casa, 'Marrakech', marr, parameter='T2M', start=1991, end=2025)

    assert trial['eligible'] is True
    assert trial['n_paired'] == 35
    ra, rb, rd = trial['aligned_site_a_result'], trial['aligned_site_b_result'], trial['diff_result']

    # OLS slope of paired difference D = B - A must agree numerically with slope(B) - slope(A) over identical years
    assert trial['slope_diff_identity_delta'] < 1e-12
    assert rd['slope_decade'] == pytest.approx(rb['slope_decade'] - ra['slope_decade'], abs=1e-12)
    assert rd['slope_decade'] == pytest.approx(0.2630647, abs=1e-5)

    # Independent statsmodels Newey-West HAC verification on paired series D(year)
    df = trial['diff_frame']
    x = df['year'].to_numpy(dtype=float)
    y = df['value'].to_numpy(dtype=float)
    ref = sm.OLS(y, sm.add_constant(x - x.mean())).fit(
        cov_type='HAC', cov_kwds={'maxlags': rd['hac_lags'], 'use_correction': True}, use_t=True
    )
    assert rd['hac_ci95'] == pytest.approx(ref.conf_int()[1] * 10)
    assert rd['ci95'][1] - rd['ci95'][0] >= rd['hac_ci95'][1] - rd['hac_ci95'][0] - 1e-10
    assert rd['ci95'][1] - rd['ci95'][0] >= rd['iid_ci95'][1] - rd['iid_ci95'][0] - 1e-10

    # Check positive-autocorrelation HAC widening on Rabat - Casablanca T2M (rho1 > 0)
    rabat = _load_snapshot('Rabat')
    rc_trial = climate_trial('Casablanca', casa, 'Rabat', rabat, parameter='T2M', start=1991, end=2025)
    assert rc_trial['diff_result']['residual_lag1'] > 0.3
    rc_cautious_w = rc_trial['diff_result']['ci95'][1] - rc_trial['diff_result']['ci95'][0]
    rc_iid_w = rc_trial['diff_result']['iid_ci95'][1] - rc_trial['diff_result']['iid_ci95'][0]
    assert rc_cautious_w > rc_iid_w


def test_trial_interval_classification_and_no_false_significance():
    casa = _load_snapshot('Casablanca')
    marr = _load_snapshot('Marrakech')
    rabat = _load_snapshot('Rabat')

    # 1. Positive trend difference (Marrakech - Casablanca T2M): even though solo intervals overlap, paired excludes zero
    pos = climate_trial('Casablanca', casa, 'Marrakech', marr, parameter='T2M', start=1991, end=2025)
    assert pos['separate_intervals_overlap'] is True
    assert pos['verdict_code'] == 'positive_difference'
    assert pos['verdict_label'] == 'Evidence of a positive trend difference'
    assert pos['cautious_excludes_zero'] is True

    # 2. Negative trend difference (Casablanca - Marrakech T2M)
    neg = climate_trial('Marrakech', marr, 'Casablanca', casa, parameter='T2M', start=1991, end=2025)
    assert neg['verdict_code'] == 'negative_difference'
    assert neg['verdict_label'] == 'Evidence of a negative trend difference'
    assert neg['diff_result']['slope_decade'] == pytest.approx(-pos['diff_result']['slope_decade'], abs=1e-12)
    assert neg['cautious_excludes_zero'] is True

    # 3. Inconclusive result (Rabat - Casablanca T2M & Marrakech - Casablanca PRECTOTCORR): MUST say inconclusive, NOT equal
    inc_t2m = climate_trial('Casablanca', casa, 'Rabat', rabat, parameter='T2M', start=1991, end=2025)
    assert inc_t2m['verdict_code'] == 'inconclusive'
    assert inc_t2m['verdict_label'] == 'Inconclusive result'
    assert 'not mean' in inc_t2m['interpretation'].lower()
    assert 'crosses zero' in inc_t2m['interpretation'].lower()

    inc_pr = climate_trial('Casablanca', casa, 'Marrakech', marr, parameter='PRECTOTCORR', start=1991, end=2025)
    assert inc_pr['verdict_code'] == 'inconclusive'
    assert inc_pr['verdict_label'] == 'Inconclusive result'
    assert 'not mean' in inc_pr['interpretation'].lower()

    # 4. Identical series must never claim significance
    same = climate_trial('Casablanca', casa, 'Casablanca', casa, parameter='T2M', start=1991, end=2025)
    assert same['eligible'] is False
    assert same['verdict_code'] == 'identical_series'
    assert same['active_excludes_zero'] is False

    # 5. Short window (<30 years) never fabricates significance
    short = climate_trial('Casablanca', casa, 'Marrakech', marr, parameter='T2M', start=2000, end=2025)
    assert short['eligible'] is False
    assert short['verdict_code'] == 'ineligible'
    assert short['active_excludes_zero'] is False

    # 6. Synthetic autocorrelated D(year) where conventional OLS falsely excludes zero while cautious HAC crosses zero
    years = np.arange(1991, 2026)
    rng = np.random.default_rng(6)
    ar_err = np.zeros(len(years))
    for i in range(1, len(years)):
        ar_err[i] = 0.72 * ar_err[i - 1] + 0.08 * rng.normal()
    x_c = years - years.mean()
    # Both A and B have non-constant linear baselines so individual site trends are defined too
    vals_a = {f'{y}{m:02d}': float(18.0 + 0.01 * (y - years.mean())) for y in years for m in range(1, 13)}
    diff_sig = 0.008 * x_c + ar_err
    vals_b = {
        f'{y}{m:02d}': float(18.0 + 0.01 * (y - years.mean()) + diff_sig[idx])
        for idx, y in enumerate(years)
        for m in range(1, 13)
    }
    t_cautious = climate_trial('SiteA', source(vals_a), 'SiteB', source(vals_b), 'T2M', 1991, 2025, 'cautious')
    t_ols = climate_trial('SiteA', source(vals_a), 'SiteB', source(vals_b), 'T2M', 1991, 2025, 'conventional')
    assert t_cautious['time_dependence_changes_verdict'] is True
    assert t_cautious['verdict_code'] == 'inconclusive'
    assert t_ols['verdict_code'] == 'positive_difference'
    assert '-0.0019' in format_interval(t_cautious['diff_result']['ci95'], '°C/decade')
    assert 'not mean' in t_cautious['interpretation'].lower()

