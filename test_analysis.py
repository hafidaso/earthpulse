import numpy as np
import pandas as pd
import pytest
from analysis import annual_series, trend, fetch_power

def source(values, p='T2M',unit='C'):
 return {'header':{'fill_value':-999},'parameters':{p:{'units':unit}},'properties':{'parameter':{p:values}}}

def test_day_weighted_temperature_and_ignore_annual_field():
 values={f'2000{m:02d}':float(m) for m in range(1,13)}; values['200013']=9999
 frame,omitted=annual_series(source(values),'T2M',2000,2000)
 days=np.array([31,29,31,30,31,30,31,31,30,31,30,31])
 assert frame.value.iloc[0]==pytest.approx(np.dot(np.arange(1,13),days)/366)
 assert omitted==[]

def test_precipitation_leap_year_conversion():
 values={f'{y}{m:02d}':2. for y in [2000,2001] for m in range(1,13)}
 f,_=annual_series(source(values,'PRECTOTCORR','mm/day'),'PRECTOTCORR',2000,2001)
 assert f.value.tolist()==[732.,730.]

@pytest.mark.parametrize('bad',[-999,np.nan])
def test_missing_month_excludes_year(bad):
 values={f'2000{m:02d}':1. for m in range(1,13)}; values['200004']=bad
 f,o=annual_series(source(values),'T2M',2000,2000)
 assert f.empty and o==[2000]

def test_wrong_units_rejected():
 with pytest.raises(ValueError): annual_series(source({},unit='K'),'T2M',2000,2001)

def test_known_linear_trend():
 x=np.arange(1991,2026); y=12+.04*(x-1991)
 r=trend(pd.DataFrame({'year':x,'value':y}))
 assert r['slope_decade']==pytest.approx(.4)
 assert r['ci95'][0]<=.4000000001 and r['ci95'][1]>=.3999999999

def test_independent_reference_hac():
 import statsmodels.api as sm
 x=np.arange(1981,2026); rng=np.random.default_rng(37); noise=np.zeros(len(x))
 for i in range(1,len(x)): noise[i]=.6*noise[i-1]+rng.normal()
 y=.025*(x-x.mean())+noise
 r=trend(pd.DataFrame({'year':x,'value':y}))
 ref=sm.OLS(y,sm.add_constant(x-x.mean())).fit(cov_type='HAC',cov_kwds={'maxlags':r['hac_lags'],'use_correction':True},use_t=True)
 assert r['hac_ci95']==pytest.approx(ref.conf_int()[1]*10)
 assert r['ci95'][1]-r['ci95'][0]>=r['hac_ci95'][1]-r['hac_ci95'][0]-1e-10

def test_short_and_gapped_periods_rejected():
 for x in [np.arange(2000,2020),np.r_[np.arange(1981,2000),np.arange(2001,2026)]]:
  with pytest.raises(ValueError): trend(pd.DataFrame({'year':x,'value':np.arange(len(x))}))

def test_invalid_coordinates():
 with pytest.raises(ValueError): fetch_power(91,0)
