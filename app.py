from datetime import datetime
import streamlit as st
from queries import Queries
import pandas as pd

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

    if code_input == "123":
        #st.secrets["ENTER_CODE"]
        st.markdown("### Register device event")

        action = st.selectbox("Event type", ["Fill dispenser", "Empty bins"], index=0)

        if action == 'Empty bins':

            n_cups = st.number_input("Total Cups", min_value=0, max_value=200, value="min", step=1, format="%d", key=0)
            
            dirty_cups = st.text_input("Dirty Cups IDs", placeholder="1,2,3,4",  key=1)
            clean_cups = st.text_input("Clean Cups IDs", placeholder="1,2,3,4", key=2)


        elif action == 'Fill dispenser':
            n_cups_inserted = st.number_input("Cups inserted", min_value=0, max_value=200, value="min", step=1, format="%d")
            reset_stock = st.checkbox('Reset Stock')

        st.write("Event time")
        col1, col2 = st.columns(2)
        date = col1.date_input("date", value="today", label_visibility="collapsed")
        time = col2.time_input("time", value="now", label_visibility="collapsed")
        event_time = datetime.combine(date, time)

        vertical_space(2)

        if st.button("Register", type="primary"):

            if action == 'Empty bins':
                dirty =[]
                clean = []
                if len(dirty_cups) != 0:
                    dirty = list(map(int, dirty_cups.split(",")))
                if len(clean_cups) != 0:
                    clean = list(map(int, clean_cups.split(",")))
                
                ds = pd.Series(dirty + clean)
                if n_cups != len(ds):
                    st.error(f"Nr of cups doesn't match nr of IDs. Cups: {n_cups}, IDs: {len(ds)} (Dirty: {len(set(dirty))}, Clean: {len(set(clean))}). Repeated: {ds[ds.duplicated()].to_list()}")
                else:
                    try:
                        res = queries.register_cups(dirty, clean, event_time)
                        st.success('Cups Collected', icon="✅")
                    except Exception as e:
                        st.error(f"Something went wrong. Try again. Exception:{e}")

            elif action == 'Fill dispenser':
                    try:
                        res = queries.add_dispenser_cups(n_cups_inserted, event_time, reset_stock)
                        st.success('Dispenser Updated', icon="✅")
                    except Exception as e:
                        st.error(f"Something went wrong. Try again. Exception:{e}")

