import sqlite3

import streamlit as st

DB_PATH = "./data/inventario-1.db"


@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # conn.row_factory = sqlite3.Row
    return conn
