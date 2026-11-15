"""EarthPulse entrypoint: English Climate Evidence Lab by default, English Expert Analysis, optional Arabic."""
import streamlit as st

st.set_page_config(
    page_title='EarthPulse — The Climate Evidence Lab',
    page_icon='◉',
    layout='wide',
    initial_sidebar_state='collapsed',
)

pages = [
    st.Page('lab.py', title='Climate Evidence Lab', icon='🧭', default=True),
    st.Page('expert_en.py', title='Expert Analysis', icon='🔬'),
    st.Page('expert_ar.py', title='العربية', icon='🌐', url_path='arabic'),
]
st.navigation(pages, position='top').run()
