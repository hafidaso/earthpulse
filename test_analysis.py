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


def test_grid_cell_metadata_and_approximate_footprint():
    from analysis import (
        MERRA2_LAT_RES_DEG,
        MERRA2_LON_RES_DEG,
        extract_grid_metadata,
        source_sha256,
    )

    casa = _load_snapshot('Casablanca')
    marr = _load_snapshot('Marrakech')
    results_index = json.loads((Path(__file__).parent / 'data' / 'results.json').read_text())
    expected_hashes = {row['location']: row['sha256'] for row in results_index}

    meta_c = extract_grid_metadata('Casablanca', casa, *LOCATIONS['Casablanca'])
    meta_m = extract_grid_metadata('Marrakech', marr, *LOCATIONS['Marrakech'])

    # NASA POWER point JSON does not publish exact MERRA-2 polygon vertices
    assert meta_c['geometry_type'] == 'Point'
    assert meta_c['exact_footprint_available'] is False
    assert 'approximate' in meta_c['footprint_label'].lower()
    assert meta_c['grid_elevation_m'] == pytest.approx(152.91, abs=1e-2)
    assert meta_m['grid_elevation_m'] == pytest.approx(836.94, abs=1e-2)
    assert 'no local weather-station' in meta_m['elevation_caveat'].lower()

    # Approximate resolution box matches documented 0.5° x 0.625° MERRA-2 spacing
    bounds_c = meta_c['footprint']['bounds']
    assert bounds_c['north'] - bounds_c['south'] == pytest.approx(MERRA2_LAT_RES_DEG)
    assert bounds_c['east'] - bounds_c['west'] == pytest.approx(MERRA2_LON_RES_DEG)
    assert meta_c['sources'] == ['MERRA2']

    # SHA-256 matches unaltered NASA snapshots recorded in data/results.json
    assert source_sha256('Casablanca', casa)['sha256'] == expected_hashes['Casablanca']
    assert source_sha256('Marrakech', marr)['sha256'] == expected_hashes['Marrakech']


def test_scientific_evidence_brief_one_page_pdf():
    import fitz
    from brief_pdf import build_scientific_evidence_brief_pdf

    casa = _load_snapshot('Casablanca')
    marr = _load_snapshot('Marrakech')
    rabat = _load_snapshot('Rabat')

    t_pos = climate_trial('Casablanca', casa, 'Marrakech', marr, parameter='T2M', start=1991, end=2025)
    pdf_t2m = build_scientific_evidence_brief_pdf(
        question='Is Marrakech warming faster than Casablanca?',
        parameter='T2M',
        start=1991,
        end=2025,
        loc_a='Casablanca',
        lat_a=LOCATIONS['Casablanca'][0],
        lon_a=LOCATIONS['Casablanca'][1],
        data_a=casa,
        loc_b='Marrakech',
        lat_b=LOCATIONS['Marrakech'][0],
        lon_b=LOCATIONS['Marrakech'][1],
        data_b=marr,
        trial=t_pos,
        interval_mode='cautious',
        generated_utc='2026-11-15T20:00:00Z',
    )
    doc = fitz.open(stream=pdf_t2m, filetype='pdf')
    assert len(doc) == 1
    txt = doc[0].get_text()
    assert 'Is Marrakech warming faster than Casablanca?' in txt
    assert '+0.26' in txt
    assert 'Evidence of a positive trend difference' in txt
    assert '6fa83df04114f52cdefc7abc239f89a941388204507a155e7733244ad24df6e0' in txt
    assert '6ee4ecd6f58d3be93f8694bd46113f3c9d8a1b45bb75cf61f5bee0d2439d6252' in txt
    assert 'Hafida Belayd' in txt
    assert '2026-11-15T20:00:00Z' in txt
    assert 'NOT a Type-I error' in txt

    # Dynamic change check: Rabat vs Casa inconclusive & PRECTOTCORR produce distinct verdicts & values
    t_inc = climate_trial('Casablanca', casa, 'Rabat', rabat, parameter='T2M', start=1991, end=2025)
    pdf_inc = build_scientific_evidence_brief_pdf(
        question='Is Rabat warming faster than Casablanca?',
        parameter='T2M',
        start=1991,
        end=2025,
        loc_a='Casablanca',
        lat_a=LOCATIONS['Casablanca'][0],
        lon_a=LOCATIONS['Casablanca'][1],
        data_a=casa,
        loc_b='Rabat',
        lat_b=LOCATIONS['Rabat'][0],
        lon_b=LOCATIONS['Rabat'][1],
        data_b=rabat,
        trial=t_inc,
    )
    doc_inc = fitz.open(stream=pdf_inc, filetype='pdf')
    assert len(doc_inc) == 1
    txt_inc = doc_inc[0].get_text()
    assert 'Inconclusive result' in txt_inc
    assert '9bb96b521ca695f8c6f0c26b24106299833bb4005352ac246b570e3ac4846d5f' in txt_inc


def test_uncertainty_lens_standard_errors_and_raw_hac_ratio():
    from analysis import evaluate_site, uncertainty_lens_summary

    casa = _load_snapshot('Casablanca')
    marr = _load_snapshot('Marrakech')

    # Casablanca T2M: SE_HAC > SE_OLS -> ratio > 1 and cautious matches HAC
    ev_c_conv = evaluate_site('Casablanca', casa, 'T2M', 1991, 2025, interval_mode='conventional')
    ev_c_hac = evaluate_site('Casablanca', casa, 'T2M', 1991, 2025, interval_mode='hac')
    ev_c_caut = evaluate_site('Casablanca', casa, 'T2M', 1991, 2025, interval_mode='cautious')

    ul_c = uncertainty_lens_summary(ev_c_caut['result'])
    assert ul_c['se_hac_decade'] > ul_c['se_ols_decade']
    assert ul_c['hac_to_ols_se_ratio'] == pytest.approx(ul_c['se_hac_decade'] / ul_c['se_ols_decade'], rel=1e-9)
    assert ul_c['hac_to_ols_se_ratio'] == pytest.approx(1.5160, abs=1e-3)
    assert ul_c['se_cautious_decade'] == pytest.approx(ul_c['se_hac_decade'])
    assert ul_c['cautious_floored_by_ols'] is False
    assert ev_c_conv['active_excludes_zero'] is True
    assert ev_c_hac['active_excludes_zero'] is False
    assert ev_c_caut['active_excludes_zero'] is False
    assert 'not a type-i error' in ul_c['ratio_note'].lower()

    # Marrakech PRECTOTCORR: SE_HAC < SE_OLS -> ratio < 1, while cautious max() preserves SE_OLS
    ev_m_rain = evaluate_site('Marrakech', marr, 'PRECTOTCORR', 1991, 2025, interval_mode='cautious')
    ev_m_rain_hac = evaluate_site('Marrakech', marr, 'PRECTOTCORR', 1991, 2025, interval_mode='hac')
    ul_m = uncertainty_lens_summary(ev_m_rain['result'])
    assert ul_m['se_hac_decade'] < ul_m['se_ols_decade']
    assert ul_m['hac_to_ols_se_ratio'] < 1.0
    assert ul_m['cautious_floored_by_ols'] is True
    assert ul_m['se_cautious_decade'] == pytest.approx(ul_m['se_ols_decade'])
    assert ev_m_rain['active_ci'] == pytest.approx(ev_m_rain['result']['ci95'])
    assert ev_m_rain_hac['active_ci'] == pytest.approx(ev_m_rain['result']['hac_ci95'])
    assert ev_m_rain_hac['active_ci'][1] - ev_m_rain_hac['active_ci'][0] < ev_m_rain['active_ci'][1] - ev_m_rain['active_ci'][0]






def test_compare_and_single_brief_modes_and_raw_hac_lens():
    """Verify raw HAC mode vs cautious safeguard and Compare/Single 1-page PDF briefs."""
    import json
    from pathlib import Path
    import fitz
    from analysis import (
        compare_locations,
        evaluate_site,
        source_sha256,
        uncertainty_lens_summary,
    )
    from brief_pdf import build_scientific_evidence_brief_pdf

    data_dir = Path(__file__).parent / 'data'
    casa = json.loads((data_dir / 'casablanca.json').read_text())
    mar = json.loads((data_dir / 'marrakech.json').read_text())

    # On Marrakech PRECTOTCORR (1991-2025), raw SE_HAC < SE_OLS so cautious floors at SE_OLS while 'hac' uses raw SE_HAC.
    ev_cau = evaluate_site('Marrakech', mar, 'PRECTOTCORR', 1991, 2025, interval_mode='cautious')
    ev_hac = evaluate_site('Marrakech', mar, 'PRECTOTCORR', 1991, 2025, interval_mode='hac')
    lens = uncertainty_lens_summary(ev_cau['result'])
    assert lens is not None
    assert lens['cautious_floored_by_ols'] is True
    assert lens['hac_to_ols_se_ratio'] < 1.0
    assert ev_hac['active_ci'] == lens['hac_ci95']
    assert ev_cau['active_ci'] == lens['cautious_ci95']
    assert ev_hac['active_ci'] != ev_cau['active_ci']

    comp = compare_locations('Casablanca', casa, 'Marrakech', mar, 'T2M', 1991, 2025, interval_mode='hac')
    assert comp['interval_mode'] == 'hac'

    pdf_comp = build_scientific_evidence_brief_pdf(
        question='How do temperature trends compare between Casablanca and Marrakech (1991-2025)?',
        parameter='T2M',
        start=1991,
        end=2025,
        loc_a='Casablanca',
        lat_a=33.5731,
        lon_a=-7.5898,
        data_a=casa,
        loc_b='Marrakech',
        lat_b=31.6295,
        lon_b=-7.9811,
        data_b=mar,
        comp=comp,
        interval_mode='hac',
    )
    doc_comp = fitz.open(stream=pdf_comp, filetype='pdf')
    assert doc_comp.page_count == 1
    txt_comp = doc_comp[0].get_text()
    assert source_sha256('Casablanca', casa)['sha256'] in txt_comp
    assert source_sha256('Marrakech', mar)['sha256'] in txt_comp
    assert 'SE_HAC' in txt_comp

    pdf_single = build_scientific_evidence_brief_pdf(
        question='Is annual precipitation changing at Marrakech (1991-2025)?',
        parameter='PRECTOTCORR',
        start=1991,
        end=2025,
        loc_a='Marrakech',
        lat_a=31.6295,
        lon_a=-7.9811,
        data_a=mar,
        single_site=ev_hac,
        interval_mode='hac',
    )
    doc_single = fitz.open(stream=pdf_single, filetype='pdf')
    assert doc_single.page_count == 1
    txt_single = doc_single[0].get_text()
    assert 'Marrakech' in txt_single
    assert source_sha256('Marrakech', mar)['sha256'] in txt_single

    # Modified / live payload for a reference city name must hash the live payload, NOT the bundled file.
    live_copy = json.loads(json.dumps(casa))
    live_copy['_earthpulse'] = {'request_url': 'https://power.larc.nasa.gov/api/mock?start=1981&end=2025'}
    live_sha = source_sha256('Casablanca', live_copy)
    bundled_sha = source_sha256('Casablanca', casa)
    assert 'Unaltered bundled' in bundled_sha['scope']
    assert 'Live NASA API' in live_sha['scope']
    assert live_sha['sha256'] != bundled_sha['sha256']
