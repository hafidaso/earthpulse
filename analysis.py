"""EarthPulse analysis. AI-assisted implementation by OpenAI Codex; NASA data unaltered."""
import calendar
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import requests
from scipy import stats
import statsmodels.api as sm

LOCATIONS = {'Casablanca': (33.5731, -7.5898), 'Rabat': (34.0209, -6.8416), 'Marrakech': (31.6295, -7.9811), 'Ouarzazate': (30.9335, -6.9370)}
API = 'https://power.larc.nasa.gov/api/temporal/monthly/point'
VARIABLES = {'T2M': ('Temperature at 2 metres', '°C'), 'PRECTOTCORR': ('Annual precipitation', 'mm/year')}

def fetch_power(lat, lon, start=1991, end=2025):
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('Coordinates are outside valid ranges.')
    if not (1981 <= start <= end < datetime.now(timezone.utc).year):
        raise ValueError('Choose completed calendar years from 1981 onward.')
    params = dict(parameters='T2M,PRECTOTCORR', community='AG', longitude=lon, latitude=lat, format='JSON', start=start, end=end)
    response = requests.get(API, params=params, timeout=90)
    response.raise_for_status()
    data = response.json()
    if 'parameter' not in data.get('properties', {}):
        raise ValueError('NASA did not return the expected parameter data.')
    data['_earthpulse'] = {'request_url': response.url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(), 'requested_latitude': lat, 'requested_longitude': lon, 'start': start, 'end': end, 'data_origin': 'NASA POWER API; no synthetic measurements'}
    return data

def annual_series(data, parameter, start, end):
    expected = {'T2M': 'C', 'PRECTOTCORR': 'mm/day'}
    if data['parameters'][parameter]['units'] != expected[parameter]:
        raise ValueError('Unexpected source units. Analysis stopped to prevent invalid conversion.')
    fill = data['header']['fill_value']
    raw = data['properties']['parameter'][parameter]
    rows, omitted = [], []
    for year in range(start, end+1):
        vals = np.array([raw.get(f'{year}{month:02d}', np.nan) for month in range(1,13)], dtype=float)
        if not np.all(np.isfinite(vals)) or np.any(vals == fill) or (parameter == 'PRECTOTCORR' and np.any(vals < 0)):
            omitted.append(year)
            continue
        days = np.array([calendar.monthrange(year, month)[1] for month in range(1,13)])
        value = np.sum(vals * days)
        if parameter == 'T2M': value /= days.sum()
        rows.append({'year': year, 'value': float(value)})
    return pd.DataFrame(rows, columns=['year', 'value']), omitted

def trend(frame):
    x = frame['year'].to_numpy(dtype=float)
    y = frame['value'].to_numpy(dtype=float)
    if len(x) < 30: raise ValueError('At least 30 complete years are required for this exploratory trend analysis.')
    if not np.all(np.isfinite(y)) or not np.all(np.diff(x) == 1):
        raise ValueError('Trend inference requires consecutive, complete annual values. Select an uninterrupted period.')
    if np.ptp(y) == 0: raise ValueError('This series is constant; inferential trend statistics are undefined.')
    X = sm.add_constant(x-x.mean())
    ols = sm.OLS(y, X).fit()
    lag = max(1, int(np.floor(4*(len(x)/100)**(2/9))))
    robust = ols.get_robustcov_results(cov_type='HAC', maxlags=lag, use_correction=True, use_t=True)
    # Report both intervals, and use the wider interval as a cautious screening rule.
    ci = robust.conf_int(alpha=.05)[1] * 10
    iid_ci = ols.conf_int(alpha=.05)[1] * 10
    se = max(float(robust.bse[1]), float(ols.bse[1]))
    crit = stats.t.ppf(.975, len(x)-2)
    slope = float(ols.params[1])
    wide_ci = [(slope-crit*se)*10, (slope+crit*se)*10]
    p = float(2*stats.t.sf(abs(slope/se), len(x)-2)) if se > 0 else 0.0
    residual = ols.resid
    rho = float(np.corrcoef(residual[:-1], residual[1:])[0,1]) if np.std(residual) > 1e-12 else 0.0
    return dict(n=len(x), slope_decade=slope*10, ci95=wide_ci, p_value=p,
                hac_ci95=ci.tolist(), hac_p=float(robust.pvalues[1]), iid_ci95=iid_ci.tolist(), iid_p=float(ols.pvalues[1]),
                hac_lags=lag, residual_lag1=rho, r_squared=float(ols.rsquared),
                fitted=ols.fittedvalues.tolist(), mean=float(y.mean()), start=int(x[0]), end=int(x[-1]))
