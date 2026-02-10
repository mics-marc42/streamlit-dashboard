import streamlit as st
import pandas as pd
from bigquery_utils import query_bigquery

st.set_page_config(page_title="Query Viewer", layout="wide")

st.title("BigQuery Query Viewer")

query = "Select * from table"

try:
    with st.spinner("Executing query..."):
        df = query_bigquery(query)
        st.success(f"Query executed successfully! Found {len(df)} rows.")
        st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"Error executing query: {str(e)}")
