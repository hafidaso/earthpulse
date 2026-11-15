"""EarthPulse interface. AI-assisted code: OpenAI Codex. See AI_DISCLOSURE.md."""
import json
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
from analysis import LOCATIONS, VARIABLES, fetch_power, annual_series, trend

st.set_page_config(page_title='EarthPulse · Climate Trend Detective', page_icon='◉', layout='wide')
st.markdown('''<style>
.stApp {background:#f5f3ec;color:#142d33} h1,h2,h3 {font-family:Georgia,serif!important;letter-spacing:-.03em} h1 {font-size:3.7rem!important;line-height:1.08!important} .block-container {max-width:1350px;padding-top:2.5rem} [data-testid="stMetricValue"] {color:#176b68;font-family:Georgia,serif;font-size:2.7rem} [data-testid="stSidebar"] {background:#e8ebe4} .eyebrow {letter-spacing:.18em;font-size:.8rem;color:#36706f;font-weight:700} .deck {font-size:1.2rem;max-width:820px;color:#52656b} .stButton>button {background:#155e63;color:white;border:0} a {color:#176b68}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">EARTHPULSE LABS / NASA SPACE APPS 2026</div>', unsafe_allow_html=True)
st.title('The climate trend detective')
st.markdown('<p class="deck">What is changing, how quickly, and how certain are we? Investigate decades of NASA gridded climate estimates, one location at a time.</p>', unsafe_allow_html=True)
with st.sidebar:
    st.header('Your investigation')
    location = st.selectbox('Location', list(LOCATIONS)+['Custom coordinates'])
    lat, lon = LOCATIONS.get(location, (33.5731,-7.5898))
    if location == 'Custom coordinates':
        lat = st.number_input('Latitude', -90., 90., lat, step=.01, format='%.4f')
        lon = st.number_input('Longitude', -180., 180., lon, step=.01, format='%.4f')
    else: st.caption(f'{lat:.4f}° latitude, {lon:.4f}° longitude')
    parameter = st.selectbox('Variable', list(VARIABLES), format_func=lambda k: VARIABLES[k][0])
    period = st.slider('Completed calendar years', 1981, 2025, (1991,2025))
    mode = st.radio('Data access', ['Verified bundled NASA snapshot', 'Live NASA API'])
    st.caption('Snapshots cover the four example locations, 1991–2025. Custom coordinates and other periods use the live API.')
    st.divider()
    st.caption('Built by Hafida Belayd, EarthPulse Labs. Independent hackathon prototype. No NASA endorsement.')
    st.caption('AI-assisted implementation and documentation: OpenAI Codex. Measurements come from NASA POWER.')

@st.cache_data(ttl=86400, show_spinner=False)
def load_live(lat,lon,start,end): return fetch_power(lat,lon,start,end)

start,end=period
try:
    snapshot=Path(__file__).parent/'data'/f'{location.lower()}.json'
    bundled=mode.startswith('Verified') and location in LOCATIONS and start>=1991 and end<=2025 and snapshot.exists()
    with st.spinner('Retrieving NASA POWER climate estimates…'):
        data=json.loads(snapshot.read_text()) if bundled else load_live(lat,lon,start,end)
    frame,omitted=annual_series(data,parameter,start,end)
    name,unit=VARIABLES[parameter]
    st.caption(f'{location}  /  {name}  /  {start}–{end}  /  {"Bundled real NASA response" if bundled else "Live NASA API response (cached for up to 24 hours)"}')
    if omitted: st.warning('Incomplete years excluded: '+', '.join(map(str,omitted))+'. No values have been interpolated.')
    result=None
    try: result=trend(frame)
    except ValueError as error: st.warning(str(error))
    if result:
        c1,c2,c3=st.columns([1,1.4,1])
        c1.metric('Estimated change per decade',f'{result["slope_decade"]:+.2f} {unit}')
        c2.metric('95% interval · exploratory',f'{result["ci95"][0]:+.2f} to {result["ci95"][1]:+.2f}')
        c3.metric('Complete annual values',str(result['n']))
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=frame.year,y=frame.value,mode='lines+markers',name='Annual estimate',line=dict(color='#176b68',width=2),marker=dict(size=5),hovertemplate='%{x}: %{y:.2f} '+unit+'<extra></extra>'))
    if result: fig.add_trace(go.Scatter(x=frame.year,y=result['fitted'],name='Linear fit',line=dict(color='#bc643b',width=3)))
    fig.update_layout(height=430,template='plotly_white',paper_bgcolor='#f5f3ec',plot_bgcolor='#f5f3ec',font=dict(family='Arial',color='#142d33',size=14),margin=dict(l=10,r=20,t=20,b=10),legend=dict(orientation='h',y=1.12),xaxis_title='Calendar year',yaxis_title=f'{name} ({unit})',hovermode='x unified')
    st.plotly_chart(fig,use_container_width=True)
    if result:
        sig=result['p_value']<.05
        direction='increase' if result['slope_decade']>0 else 'decrease'
        st.subheader('What the evidence says')
        st.write(f'For the NASA grid representation of this location, the fitted {name.lower()} shows an estimated {direction} of {abs(result["slope_decade"]):.2f} {unit} per decade during {result["start"]}–{result["end"]}. '+('The exploratory 95% interval excludes zero.' if sig else 'The exploratory 95% interval includes zero: this analysis does not establish a consistent linear trend.'))
        st.caption(f'Exploratory two-sided p = {result["p_value"]:.4g}. We use the larger standard error from ordinary and Newey–West HAC regression ({result["hac_lags"]} annual lags). This cautious screen does not eliminate all time-series uncertainty.')
    left,right=st.columns([1.2,1])
    with left:
        st.subheader('A transparent chain of evidence')
        st.write('NASA POWER supplies MERRA-2 gridded reanalysis estimates. Temperature is the day-weighted annual mean at 2 metres. Annual precipitation sums each monthly mean daily rate multiplied by the number of calendar days. All 12 valid months are required.')
        st.write('Annual aggregation removes the regular within-year seasonal cycle. Linear regression describes the selected period. HAC uncertainty allows short-range residual autocorrelation and unequal variance. Neither the model nor statistical significance establishes causation.')
    with right:
        st.subheader('Read the limits')
        st.write('These are grid estimates, not direct city weather-station measurements. Coastal and mountainous terrain can differ within a grid cell. Trends depend on period, model quality and linearity. Long-memory dependence, changing observing systems and repeated exploratory tests may affect inference. No correction for searching many locations is applied.')
    with st.expander('Source metadata, statistics and reproducibility'):
        st.json({'NASA_header':data['header'],'NASA_parameters':data['parameters'],'returned_point':data['geometry'],'retrieval':data.get('_earthpulse',{}),'analysis':{k:v for k,v in (result or {}).items() if k!='fitted'}})
        st.markdown('[NASA POWER monthly API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) · [MERRA-2](https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/)')
        if data.get('_earthpulse',{}).get('request_url'): st.link_button('Open the exact NASA request',data['_earthpulse']['request_url'])
    a,b=st.columns(2)
    export=frame.assign(parameter=parameter,units=unit,latitude=lat,longitude=lon,source='NASA POWER / MERRA-2')
    a.download_button('Download annual data · CSV',export.to_csv(index=False),f'earthpulse_{location}_{parameter}_{start}_{end}.csv','text/csv')
    b.download_button('Download source response · JSON',json.dumps(data,indent=2),f'earthpulse_{location}_NASA.json','application/json')
except Exception as error:
    st.error(f'Unable to complete this investigation: {error}')
    st.info('Try a bundled example for 1991–2025, or retry the live API later. No synthetic data will be substituted.')
