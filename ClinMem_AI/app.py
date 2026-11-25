import streamlit as st
from frontend.dashboard import main
st.set_page_config(page_title='ClinMem AI',page_icon='🧠',layout='wide')
main()
