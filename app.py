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

        action = st.selectbox("Event type", ["Empty bins", "Fill dispenser"], index=0)

        if action == 'Empty bins':

            n_cups = st.number_input("Total Cups", min_value=0, max_value=200, value="min", step=1, format="%d", key=0)
            
            dirty_cups = st.text_input("Dirty Cups IDs", placeholder="1,2,3,4",  key=1)
            clean_cups = st.text_input("Clean Cups IDs", placeholder="1,2,3,4", key=2)


        elif action == 'Fill dispenser':
            cups_in_stock = st.number_input("Cups in stock", min_value=0, max_value=200, value="min", step=1, format="%d")
            n_cups_inserted = st.number_input("Cups inserted", min_value=0, max_value=200, value="min", step=1, format="%d")

        st.write("Event time")
        col1, col2 = st.columns(2)
        col1.date_input("date", value="today", label_visibility="collapsed")
        col2.time_input("time", value="now", label_visibility="collapsed")

        vertical_space(2)

        if st.button("Register", type="primary"):

            if action == 'Empty bins':
                dirty =[]
                clean = []
                if len(dirty_cups) != 0:
                    dirty = dirty_cups.split(",")
                if len(clean_cups) != 0:
                    clean = clean_cups.split(",")
                
                if n_cups != len(list(set(dirty + clean))):
                    st.error("Nr of cups doesn't match nr of IDs")
                else:
                    try:
                        res = queries.register_dirty_cups(dirty)
                        res = queries.register_clean_cups(clean)
                        st.success('Cups Collected', icon="✅")
                    except:
                        st.error(f"Something went wrong, with res = {res}")

            elif action == 'Fill dispenser':
                    try:
                        res = queries.update_dispenser_stock(cups_in_stock)
                        res = queries.add_dispenser_cups(n_cups_inserted)
                        st.success('Dispenser Updated', icon="✅")
                    except:
                        st.error(f"Something went wrong, with res = {res}")

