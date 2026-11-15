import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from analysis import (
    LOCATIONS,
    annual_series,
    compare_locations,
    excludes_zero,
    fetch_power,
    format_bound,
    format_interval,
    intervals_overlap,
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
