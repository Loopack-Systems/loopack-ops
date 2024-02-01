from datetime import datetime
import streamlit as st
from queries import Queries

queries = Queries()

def vertical_space(num):
    for _ in range(num):
        st.text("")

st.set_page_config(
    page_title="Loopack", 
    initial_sidebar_state="collapsed"
)

st.title("Loopack Ops")

code_input = st.text_input("Code to enter", type="password")

if st.button("Enter") or 'login' in st.session_state:

    vertical_space(1)

    st.session_state['login'] = 'TRUE'

    if code_input == st.secrets["ENTER_CODE"]:
        
        st.markdown("### Register device event")

        st.selectbox("Event type", ["Empty collector", "Fill dispenser"], index=0)

        st.number_input("Number of cups", min_value=0, max_value=200, value="min", step=1, format="%d")

        st.write("Event time")
        col1, col2 = st.columns(2)
        col1.date_input("date", value="today", label_visibility="collapsed")
        col2.time_input("time", value="now", label_visibility="collapsed")

        vertical_space(2)

        if st.button("Register", type="primary"):
            pass

