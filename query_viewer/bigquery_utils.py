from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st

_client = None

def get_bigquery_client():
    global _client
    if _client is None:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        _client = bigquery.Client(
            credentials=credentials,
            project=credentials.project_id,
        )
    return _client

def query_bigquery(query):
    client = get_bigquery_client()
    df = client.query(query).to_dataframe()
    return df
