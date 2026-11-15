"""EarthPulse entrypoint: Earth Investigation Studio (English default), Discovery & Seasons, Expert Analysis, optional Arabic."""
import streamlit as st

st.set_page_config(
    page_title='EarthPulse — Earth Investigation Studio',
    page_icon='◉',
    layout='wide',
    initial_sidebar_state='collapsed',
)

pages = [
    st.Page('lab.py', title='Investigation Studio', icon='🧭', default=True),
    st.Page('discover.py', title='Discovery & Seasons', icon='🛰️'),
    st.Page('expert_en.py', title='Expert Analysis', icon='🔬'),
    st.Page('expert_ar.py', title='العربية', icon='🌐', url_path='arabic'),
]
st.navigation(pages, position='top').run()
